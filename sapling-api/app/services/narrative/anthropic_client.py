"""Thin Anthropic SDK wrapper used by the narrative pipeline.

Single concern: take a system prompt + a user message, return the model
text + usage telemetry. Defaults are tuned for Sapling's narrative
workload:

  - model:    claude-opus-4-7
  - thinking: OFF — adaptive thinking busts the prompt cache. Each call
              with adaptive thinking writes a fresh cache (cache_read=0
              on calls 2-4 of a render). Without thinking, the system-
              prompt cache hits on every subsequent call, cutting input
              cost by ~80 % across a 4-section render. Empirically
              verified 2026-04-29 against Opus 4.7. Prose generation
              doesn't benefit from thinking the way multi-step reasoning
              tasks do — voice + tone + adherence to fact lists are all
              base-model strengths.
  - effort:   high (intelligence-sensitive prose)
  - caching:  ephemeral on the system prompt (reused across N section
              calls in one render — verified via cache_read tokens)
  - retry:    SDK default (max_retries=2, exp backoff on 429/5xx)

If the API is unreachable, the call raises — the caller is responsible
for falling back to deterministic prose. We do NOT silently swallow
errors here; the policeman / renderer decides what FAIL means.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import anthropic

from app.config import get_settings

log = logging.getLogger(__name__)


# Model + defaults locked in one place. Change here, not at call sites.
_MODEL = "claude-opus-4-7"
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_EFFORT = "high"


@dataclass(frozen=True)
class CompletionResult:
    """Plain result envelope. The narrative layer doesn't need raw
    SDK objects — just the text, the section it's for, and enough
    usage data to log cost telemetry."""
    text: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    stop_reason: Optional[str]


class NarrativeClient:
    """Encapsulates one Anthropic client + the Sapling defaults.

    Constructed once per render — the system-prompt cache breakpoint
    means subsequent section calls inside the same render reuse the
    cached prefix (verifiable via `cache_read_tokens`).
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: str = _MODEL,
        effort: str = _DEFAULT_EFFORT,
    ):
        # Resolve key from (in priority order): explicit arg → app
        # Settings (pydantic-settings, reads .env file) → process env.
        # Settings is the same source the lab extractor uses, so
        # production deploys that put the key in `.env` but don't
        # export it to the process environment work consistently
        # across both code paths.
        key = (
            api_key
            or get_settings().anthropic_api_key
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY missing — cannot run Opus narrative "
                "pipeline. Either set the env var, add it to .env, or "
                "pass narrative_mode='deterministic'."
            )
        self._client = anthropic.Anthropic(api_key=key)
        self._model = model
        self._effort = effort

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        cache_system: bool = True,
    ) -> CompletionResult:
        """Single-shot non-streaming completion.

        `cache_system=True` puts an ephemeral cache breakpoint on the
        system block so it's reused across N section calls in the same
        render. The system prompt is large (voice + disclosure rules ≈
        2-3k tokens) — caching pays off after the second call.
        """
        system_blocks = [
            {
                "type": "text",
                "text": system_prompt,
                **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
            }
        ]

        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": [{"role": "user", "content": user_message}],
            "output_config": {"effort": self._effort},
            # `thinking` deliberately omitted — see module docstring.
            # Adaptive thinking would bust the prompt cache on every
            # call, which would erase the cost benefit of caching a
            # large system prompt across N sequential section calls.
        }

        try:
            resp = self._client.messages.create(**kwargs)
        except anthropic.APIStatusError as exc:
            log.warning(
                "Opus narrative call failed: status=%s body=%s",
                getattr(exc, "status_code", "?"),
                str(exc)[:300],
            )
            raise

        text = _extract_text(resp.content)
        usage = resp.usage
        return CompletionResult(
            text=text,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            stop_reason=getattr(resp, "stop_reason", None),
        )


def _extract_text(content_blocks) -> str:
    """Pull the text out of a Messages response. Adaptive thinking on
    Opus 4.7 omits thinking content by default ("display": "omitted")
    so the only non-empty blocks are normal text — but we filter on
    block type to be safe."""
    out: list[str] = []
    for block in content_blocks or []:
        btype = getattr(block, "type", None)
        if btype == "text":
            text = getattr(block, "text", "") or ""
            if text:
                out.append(text)
    return "".join(out).strip()
