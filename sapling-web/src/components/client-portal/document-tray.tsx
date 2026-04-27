"use client";

import { useState } from "react";
import { Calendar, FileText, GripVertical, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";

export interface TrayDoc {
  id: string;
  type: "soil" | "leaf";
  lab_name: string | null;
  date: string | null;
  crop: string | null;
  source_document_url: string | null;
  field_id: string | null;
}

export interface TrayBlock {
  id: string;
  name: string;
  farm_name: string;
  crop: string | null;
}

/** Side-by-side tray: list of unlinked docs on the left, blocks grouped
 * by farm on the right. Drag a doc card onto a block to link.
 *
 * Auto-match still runs at extract time; this view catches the misses
 * and lets the agronomist sort them visually instead of via dropdown. */
export function DocumentTray({
  unlinkedDocs,
  blocks,
  onLinked,
}: {
  unlinkedDocs: TrayDoc[];
  blocks: TrayBlock[];
  onLinked: () => void | Promise<void>;
}) {
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [hoverBlock, setHoverBlock] = useState<string | null>(null);
  const [linkingId, setLinkingId] = useState<string | null>(null);

  const blocksByFarm = new Map<string, TrayBlock[]>();
  for (const b of blocks) {
    if (!blocksByFarm.has(b.farm_name)) blocksByFarm.set(b.farm_name, []);
    blocksByFarm.get(b.farm_name)!.push(b);
  }

  async function handleDrop(blockId: string, docId: string) {
    const doc = unlinkedDocs.find((d) => d.id === docId);
    if (!doc) return;
    const block = blocks.find((b) => b.id === blockId);
    setLinkingId(docId);
    try {
      await api.post(`/api/${doc.type}/${docId}/link-field`, { field_id: blockId });
      toast.success(`Linked to ${block?.name ?? "field"}`);
      await onLinked();
    } catch {
      toast.error("Failed to link");
    } finally {
      setLinkingId(null);
      setDraggingId(null);
      setHoverBlock(null);
    }
  }

  if (unlinkedDocs.length === 0) {
    return (
      <div className="rounded-lg border border-dashed bg-white py-12 text-center">
        <FileText className="mx-auto size-8 text-muted-foreground/40" />
        <p className="mt-3 text-sm text-muted-foreground">
          No unlinked documents. Every analysis is matched to a block.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-700">
          Unlinked · {unlinkedDocs.length}
        </h3>
        <p className="mb-3 text-[11px] text-muted-foreground">
          Drag a card onto a block on the right to link it.
        </p>
        <ul className="space-y-2">
          {unlinkedDocs.map((doc) => (
            <li
              key={doc.id}
              draggable
              onDragStart={(e) => {
                setDraggingId(doc.id);
                e.dataTransfer.setData("text/plain", doc.id);
                e.dataTransfer.effectAllowed = "link";
              }}
              onDragEnd={() => setDraggingId(null)}
              className={`flex cursor-grab items-center gap-3 rounded-lg border bg-amber-50/50 p-3 text-sm transition-shadow hover:shadow-sm active:cursor-grabbing ${
                draggingId === doc.id ? "opacity-50" : ""
              }`}
            >
              <GripVertical className="size-3.5 shrink-0 text-muted-foreground" />
              <FileText
                className={`size-4 shrink-0 ${
                  doc.type === "soil" ? "text-amber-600" : "text-emerald-600"
                }`}
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-2">
                  <span className="truncate font-medium text-[var(--sapling-dark)]">
                    {doc.lab_name ?? "Lab report"}
                  </span>
                  <span className="rounded bg-white px-1 py-0.5 text-[10px] uppercase text-muted-foreground">
                    {doc.type}
                  </span>
                </div>
                <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                  {doc.crop && <span>{doc.crop}</span>}
                  {doc.date && (
                    <span className="inline-flex items-center gap-0.5">
                      <Calendar className="size-2.5" />
                      {new Date(doc.date).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
              {linkingId === doc.id && (
                <Loader2 className="size-4 shrink-0 animate-spin text-[var(--sapling-orange)]" />
              )}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Blocks
        </h3>
        <p className="mb-3 text-[11px] text-muted-foreground">Drop here to link.</p>
        <div className="space-y-3">
          {Array.from(blocksByFarm.entries()).map(([farm, fs]) => (
            <div key={farm}>
              <p className="mb-1.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                {farm}
              </p>
              <ul className="space-y-1.5">
                {fs.map((b) => {
                  const hovering = hoverBlock === b.id;
                  return (
                    <li
                      key={b.id}
                      onDragOver={(e) => {
                        e.preventDefault();
                        e.dataTransfer.dropEffect = "link";
                        if (hoverBlock !== b.id) setHoverBlock(b.id);
                      }}
                      onDragLeave={(e) => {
                        if (e.relatedTarget && (e.currentTarget as Node).contains(e.relatedTarget as Node)) return;
                        setHoverBlock((prev) => (prev === b.id ? null : prev));
                      }}
                      onDrop={(e) => {
                        e.preventDefault();
                        const docId = e.dataTransfer.getData("text/plain");
                        if (docId) handleDrop(b.id, docId);
                      }}
                      className={`flex items-center justify-between gap-2 rounded-md border bg-white px-3 py-2 text-sm transition-colors ${
                        hovering
                          ? "border-[var(--sapling-orange)] bg-orange-50"
                          : "border-gray-200"
                      }`}
                    >
                      <span className="min-w-0 flex-1 truncate font-medium text-[var(--sapling-dark)]">
                        {b.name}
                      </span>
                      {b.crop && (
                        <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600">
                          {b.crop}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
