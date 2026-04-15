"use client";

import { useState } from "react";
import { API_URL } from "@/lib/api";
import { Loader2, FileText, Upload, X, Check } from "lucide-react";
import type { ExtractedSample } from "../types";

interface UploadedFile {
  file: File;
  status: "extracting" | "done" | "error";
  department?: string;
  samples: ExtractedSample[];
  labName?: string;
  analysisDate?: string;
  error?: string;
}

interface DocumentUploadProps {
  labNameHint?: string;
  clientId?: string;
  onExtracted: (result: {
    department: string | null;
    samples: ExtractedSample[];
    labName: string | null;
    analysisDate: string | null;
    sourceDocumentUrl: string | null;
  }) => void;
  onError: (msg: string) => void;
}

export function DocumentUpload({ labNameHint, clientId, onExtracted, onError }: DocumentUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [dragging, setDragging] = useState(false);

  const extractFile = async (file: File) => {
    const entry: UploadedFile = { file, status: "extracting", samples: [] };
    setFiles((prev) => [...prev, entry]);

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (labNameHint) formData.append("lab_name_hint", labNameHint);
      if (clientId) formData.append("client_id", clientId);

      const token = (
        await (await import("@/lib/supabase")).createClient().auth.getSession()
      ).data.session?.access_token;
      const res = await fetch(`${API_URL}/api/soil/extract`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
        throw new Error(err.detail || `Extraction failed (${res.status})`);
      }
      const data = await res.json();
      const samples: ExtractedSample[] = (data.samples || []).filter(
        (s: ExtractedSample) => !s.block_name?.startsWith("Norm")
      );

      setFiles((prev) =>
        prev.map((f) =>
          f.file === file
            ? { ...f, status: "done", department: data.department, samples, labName: data.lab_name, analysisDate: data.analysis_date }
            : f
        )
      );

      onExtracted({
        department: data.department || null,
        samples,
        labName: data.lab_name || null,
        analysisDate: data.analysis_date || null,
        sourceDocumentUrl: data.source_document_url || null,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Extraction failed";
      setFiles((prev) =>
        prev.map((f) => (f.file === file ? { ...f, status: "error", error: msg } : f))
      );
      onError(msg);
    }
  };

  const handleFiles = (fileList: FileList | File[]) => {
    const arr = Array.from(fileList);
    for (const f of arr) {
      extractFile(f);
    }
  };

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
        }}
        className={`flex flex-col items-center gap-4 rounded-lg border-2 border-dashed p-8 transition-colors ${
          dragging ? "border-[var(--sapling-orange)] bg-orange-50" : "border-gray-300"
        }`}
      >
        <FileText className="size-10 text-muted-foreground/30" />
        <div className="text-center">
          <p className="text-sm font-medium text-[var(--sapling-dark)]">
            Drop soil and/or leaf reports here
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            PDF, JPEG, PNG — multiple files supported
          </p>
        </div>
        <label className="cursor-pointer">
          <input
            type="file"
            accept=".pdf,image/jpeg,image/png,image/webp"
            multiple
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) handleFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <span className="inline-flex items-center gap-2 rounded-md bg-[var(--sapling-orange)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--sapling-orange)]/90">
            <Upload className="size-4" />
            Choose Files
          </span>
        </label>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-1.5">
          {files.map((f, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
            >
              <div className="flex items-center gap-2">
                {f.status === "extracting" && <Loader2 className="size-4 animate-spin text-[var(--sapling-orange)]" />}
                {f.status === "done" && <Check className="size-4 text-green-600" />}
                {f.status === "error" && <X className="size-4 text-red-500" />}
                <span className="font-medium">{f.file.name}</span>
                {f.department && (
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                    {f.department}
                  </span>
                )}
                {f.status === "done" && (
                  <span className="text-xs text-muted-foreground">
                    {f.samples.length} sample{f.samples.length !== 1 ? "s" : ""}
                  </span>
                )}
              </div>
              <button onClick={() => removeFile(f.file)} className="text-muted-foreground hover:text-foreground">
                <X className="size-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
