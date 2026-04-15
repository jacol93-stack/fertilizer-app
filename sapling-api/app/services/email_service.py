"""Email service using Resend API for quote notifications."""

import os
import httpx
from datetime import datetime

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "jaco@saplingfertilizer.co.za")
FROM_EMAIL = "Sapling Fertilizer <noreply@saplingfertilizer.co.za>"
APP_URL = os.environ.get("APP_URL", "https://app.saplingfertilizer.co.za")


def _send_email(to: str, subject: str, html: str) -> bool:
    """Send an email via Resend API. Returns True on success."""
    if not RESEND_API_KEY:
        print("WARNING: RESEND_API_KEY not set, skipping email")
        return False
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=10,
        )
        success = response.status_code in (200, 201, 202)
        if not success:
            print(f"Email send failed: {response.status_code} {response.text}")
        return success
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def _brand_wrapper(content: str) -> str:
    """Wrap content in branded HTML email template."""
    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;">
        <div style="background: #191919; padding: 20px 30px; text-align: center;">
            <h1 style="color: #ff4f00; margin: 0; font-size: 24px;">Sapling</h1>
            <p style="color: #999; margin: 4px 0 0; font-size: 12px;">Fertilise Smarter, Grow Stronger</p>
        </div>
        <div style="border-top: 3px solid #ff4f00;"></div>
        <div style="padding: 30px;">
            {content}
        </div>
        <div style="background: #f5f5f5; padding: 15px 30px; text-align: center; font-size: 11px; color: #999;">
            Sapling Fertilizer | app.saplingfertilizer.co.za<br>
            This is an automated notification. Please do not reply to this email.
        </div>
    </div>
    """


def _button(text: str, url: str) -> str:
    """Generate a CTA button for emails."""
    return f"""
    <div style="text-align: center; margin: 25px 0;">
        <a href="{url}" style="display: inline-block; background: #ff4f00; color: #ffffff; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">{text}</a>
    </div>
    """


def _detail_row(label: str, value: str) -> str:
    return f"""
    <tr>
        <td style="padding: 6px 12px; font-weight: 600; color: #191919; width: 140px; vertical-align: top;">{label}</td>
        <td style="padding: 6px 12px; color: #4d4d4d;">{value}</td>
    </tr>
    """


def _detail_table(rows: list[tuple[str, str]]) -> str:
    inner = "".join(_detail_row(label, value) for label, value in rows)
    return f"""
    <table style="width: 100%; border-collapse: collapse; background: #f9f9f9; border-radius: 8px; margin: 15px 0;">
        {inner}
    </table>
    """


def _tracking_pixel(message_id: str) -> str:
    """1x1 tracking pixel for email read receipts."""
    return f'<img src="{APP_URL}/api/quotes/email/track/{message_id}.png" width="1" height="1" style="display:none" />'


# ── Public email functions ─────────────────────────────────────────────────


def send_quote_request_email(
    quote: dict,
    agent_name: str,
    agent_email: str,
    message_id: str,
) -> bool:
    """Notify admin of a new quote request."""
    quote_type_label = {
        "blend": "Blend Quote",
        "feeding_program": "Fertilizer Program Quote",
        "nutrient_request": "Nutrient Request",
        "blend_assist": "Blend Assistance Request",
    }.get(quote.get("quote_type", ""), "Quote")

    details = [
        ("Quote Number", quote.get("quote_number", "")),
        ("Type", quote_type_label),
        ("Agent", f"{agent_name} ({agent_email})"),
        ("Client", quote.get("client_name", "")),
    ]
    if quote.get("farm_name"):
        details.append(("Farm", quote["farm_name"]))
    if quote.get("field_name"):
        details.append(("Field", quote["field_name"]))
    if quote.get("agent_notes"):
        details.append(("Agent Notes", quote["agent_notes"]))

    # Add request data summary
    rd = quote.get("request_data", {})
    if rd.get("sa_notation"):
        details.append(("SA Notation", rd["sa_notation"]))
    if rd.get("international_notation"):
        details.append(("International", rd["international_notation"]))
    if rd.get("batch_size"):
        details.append(("Batch Size", f"{rd['batch_size']} kg"))

    html = _brand_wrapper(f"""
        <h2 style="color: #191919; margin: 0 0 10px;">New Quote Request</h2>
        <p style="color: #4d4d4d; margin: 0 0 20px;">
            {agent_name} has submitted a quote request.
        </p>
        {_detail_table(details)}
        {_button("Review Quote", f"{APP_URL}/admin/quotes?id={quote.get('id', '')}")}
        {_tracking_pixel(message_id)}
    """)

    return _send_email(ADMIN_EMAIL, f"New Quote Request - {quote.get('quote_number', '')}", html)


def send_quote_response_email(
    quote: dict,
    agent_email: str,
    agent_name: str,
    price: float,
    price_unit: str,
    admin_notes: str,
    valid_until: str,
    message_id: str,
) -> bool:
    """Notify agent that their quote has been priced."""
    details = [
        ("Quote Number", quote.get("quote_number", "")),
        ("Client", quote.get("client_name", "")),
        ("Quoted Price", f"R{price:,.2f} {price_unit}"),
    ]
    if valid_until:
        details.append(("Valid Until", valid_until))
    if admin_notes:
        details.append(("Notes", admin_notes))

    html = _brand_wrapper(f"""
        <h2 style="color: #191919; margin: 0 0 10px;">Your Quote is Ready</h2>
        <p style="color: #4d4d4d; margin: 0 0 20px;">
            Hi {agent_name}, your quote request has been priced.
        </p>
        {_detail_table(details)}
        <p style="color: #4d4d4d; text-align: center;">
            Please review and accept or decline this quote in the app.
        </p>
        {_button("View Quote", f"{APP_URL}/quotes?id={quote.get('id', '')}")}
        {_tracking_pixel(message_id)}
    """)

    return _send_email(agent_email, f"Quote Ready - {quote.get('quote_number', '')}", html)


def send_quote_accepted_email(
    quote: dict,
    agent_name: str,
    message_id: str,
) -> bool:
    """Notify admin that agent accepted the quote."""
    html = _brand_wrapper(f"""
        <h2 style="color: #43a047; margin: 0 0 10px;">Quote Accepted</h2>
        <p style="color: #4d4d4d; margin: 0 0 20px;">
            {agent_name} has accepted quote <strong>{quote.get('quote_number', '')}</strong>
            for client <strong>{quote.get('client_name', '')}</strong>.
        </p>
        {_detail_table([
            ("Quote Number", quote.get("quote_number", "")),
            ("Price", f"R{quote.get('quoted_price', 0):,.2f} {quote.get('price_unit', '')}"),
            ("Client", quote.get("client_name", "")),
        ])}
        {_button("View Quote", f"{APP_URL}/admin/quotes?id={quote.get('id', '')}")}
        {_tracking_pixel(message_id)}
    """)

    return _send_email(ADMIN_EMAIL, f"Quote Accepted - {quote.get('quote_number', '')}", html)


def send_quote_declined_email(
    quote: dict,
    agent_name: str,
    reason: str,
    message_id: str,
) -> bool:
    """Notify admin that agent declined the quote."""
    html = _brand_wrapper(f"""
        <h2 style="color: #e53935; margin: 0 0 10px;">Quote Declined</h2>
        <p style="color: #4d4d4d; margin: 0 0 20px;">
            {agent_name} has declined quote <strong>{quote.get('quote_number', '')}</strong>.
        </p>
        {_detail_table([
            ("Quote Number", quote.get("quote_number", "")),
            ("Client", quote.get("client_name", "")),
            ("Reason", reason or "No reason provided"),
        ])}
        {_button("View Quote", f"{APP_URL}/admin/quotes?id={quote.get('id', '')}")}
        {_tracking_pixel(message_id)}
    """)

    return _send_email(ADMIN_EMAIL, f"Quote Declined - {quote.get('quote_number', '')}", html)


def send_quote_revision_email(
    quote: dict,
    agent_name: str,
    notes: str,
    message_id: str,
) -> bool:
    """Notify admin that agent requested revision."""
    html = _brand_wrapper(f"""
        <h2 style="color: #ff9800; margin: 0 0 10px;">Revision Requested</h2>
        <p style="color: #4d4d4d; margin: 0 0 20px;">
            {agent_name} has requested changes to quote <strong>{quote.get('quote_number', '')}</strong>.
        </p>
        {_detail_table([
            ("Quote Number", quote.get("quote_number", "")),
            ("Client", quote.get("client_name", "")),
            ("Revision Notes", notes),
        ])}
        {_button("Review Quote", f"{APP_URL}/admin/quotes?id={quote.get('id', '')}")}
        {_tracking_pixel(message_id)}
    """)

    return _send_email(ADMIN_EMAIL, f"Revision Requested - {quote.get('quote_number', '')}", html)


def _format_thread_history(messages: list[dict]) -> str:
    """Format message history for email thread display."""
    if not messages:
        return ""
    history = ""
    for msg in messages:
        sender = msg.get("sender_name", msg.get("sender_role", "Unknown"))
        time = msg.get("created_at", "")[:16].replace("T", " ")
        content = msg.get("content", "")
        msg_type = msg.get("message_type", "note")

        if msg_type in ("accepted", "declined", "status_change"):
            history += f'<div style="text-align:center;padding:4px 0;color:#999;font-size:11px;">--- {content} ({time}) ---</div>'
        elif msg_type == "quote_sent":
            price = msg.get("metadata", {}).get("quoted_price", "")
            history += f'<div style="background:#f3e8ff;padding:8px 12px;margin:4px 0;border-radius:4px;font-size:12px;"><strong>{sender}</strong> ({time})<br>Quote sent: R{price}<br>{content or ""}</div>'
        else:
            history += f'<div style="background:#f5f5f5;padding:8px 12px;margin:4px 0;border-radius:4px;font-size:12px;"><strong>{sender}</strong> ({time})<br>{content}</div>'
    return history


def send_new_message_email(
    quote: dict,
    recipient_email: str,
    sender_name: str,
    message_preview: str,
    is_admin_recipient: bool,
    message_id: str,
    thread_messages: list[dict] | None = None,
) -> bool:
    """Notify recipient of a new message on a quote thread."""
    view_url = f"{APP_URL}/admin/quotes?id={quote.get('id', '')}" if is_admin_recipient else f"{APP_URL}/quotes?id={quote.get('id', '')}"

    thread_html = ""
    if thread_messages:
        thread_html = f"""
        <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px;">
            <p style="color: #999; font-size: 11px; font-weight: 600; margin: 0 0 8px;">CONVERSATION HISTORY</p>
            {_format_thread_history(thread_messages)}
        </div>
        """

    html = _brand_wrapper(f"""
        <h2 style="color: #191919; margin: 0 0 10px;">New Message</h2>
        <p style="color: #4d4d4d; margin: 0 0 10px;">
            {sender_name} sent a message on quote <strong>{quote.get('quote_number', '')}</strong>:
        </p>
        <div style="background: #f5f5f5; border-left: 3px solid #ff4f00; padding: 12px 15px; margin: 15px 0; border-radius: 0 6px 6px 0;">
            <p style="color: #4d4d4d; margin: 0; font-style: italic;">"{message_preview}"</p>
        </div>
        {_button("View Thread", view_url)}
        {thread_html}
        {_tracking_pixel(message_id)}
    """)

    return _send_email(recipient_email, f"New Message - {quote.get('quote_number', '')}", html)
