"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { BlendDetailView } from "@/components/blend-detail-view";
import { SoilDetailView } from "@/components/soil-detail-view";
import { Loader2 } from "lucide-react";

interface PreviewState {
  type: "blend" | "soil";
  id: string;
}

export function useRecordPreview() {
  const [record, setRecord] = useState<PreviewState | null>(null);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function openPreview(type: "blend" | "soil", id: string) {
    setRecord({ type, id });
    setData(null);
    setLoading(true);
    try {
      const endpoint =
        type === "blend" ? `/api/blends/${id}` : `/api/soil/${id}`;
      const result = await api.get(endpoint);
      setData(result);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  function closePreview() {
    setRecord(null);
    setData(null);
  }

  return { record, data, loading, openPreview, closePreview };
}

export function RecordPreviewSheet({
  record,
  data,
  loading,
  onClose,
}: {
  record: { type: "blend" | "soil"; id: string } | null;
  data: any;
  loading: boolean;
  onClose: () => void;
}) {
  const { isAdmin } = useAuth();

  return (
    <Sheet
      open={!!record}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent side="right" className="sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {record?.type === "blend"
              ? "Blend Details"
              : "Soil Analysis Details"}
          </SheetTitle>
        </SheetHeader>
        <div className="px-4 pb-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
            </div>
          ) : data ? (
            record?.type === "blend" ? (
              <BlendDetailView blend={data} isAdmin={isAdmin} />
            ) : (
              <SoilDetailView soil={data} />
            )
          ) : (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Failed to load details
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
