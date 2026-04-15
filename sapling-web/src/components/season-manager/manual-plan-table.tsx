"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2 } from "lucide-react";
import { PRODUCT_TYPES, APPLICATION_METHODS, MONTH_NAMES } from "@/lib/season-constants";
import type { Block } from "@/lib/season-constants";

export interface ManualPlanRow {
  id: string;
  block_name: string;
  month: number;
  product_type: string;
  product_name: string;
  rate_kg_ha: number | null;
  method: string;
}

interface ManualPlanTableProps {
  rows: ManualPlanRow[];
  setRows: React.Dispatch<React.SetStateAction<ManualPlanRow[]>>;
  blocks: Omit<Block, "id">[];
}

let nextId = 1;
function makeId() {
  return `row-${nextId++}`;
}

export function ManualPlanTable({ rows, setRows, blocks }: ManualPlanTableProps) {
  const addRow = () => {
    setRows((prev) => [
      ...prev,
      {
        id: makeId(),
        block_name: blocks[0]?.name || "",
        month: 1,
        product_type: "pelletised",
        product_name: "",
        rate_kg_ha: null,
        method: "broadcast",
      },
    ]);
  };

  const updateRow = (id: string, updates: Partial<ManualPlanRow>) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...updates } : r)));
  };

  const removeRow = (id: string) => {
    setRows((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="px-3 py-2 text-left font-medium text-muted-foreground">Block</th>
              <th className="px-3 py-2 text-left font-medium text-muted-foreground">Month</th>
              <th className="px-3 py-2 text-left font-medium text-muted-foreground">Type</th>
              <th className="px-3 py-2 text-left font-medium text-muted-foreground">Product Name</th>
              <th className="px-3 py-2 text-left font-medium text-muted-foreground">Rate kg/ha</th>
              <th className="px-3 py-2 text-left font-medium text-muted-foreground">Method</th>
              <th className="px-3 py-2 w-10" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b last:border-b-0">
                <td className="px-2 py-1.5">
                  <select
                    value={row.block_name}
                    onChange={(e) => updateRow(row.id, { block_name: e.target.value })}
                    className="w-full rounded border bg-white px-2 py-1 text-sm"
                  >
                    {blocks.map((b, i) => (
                      <option key={i} value={b.name}>
                        {b.name || `Block ${i + 1}`}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1.5">
                  <select
                    value={row.month}
                    onChange={(e) => updateRow(row.id, { month: parseInt(e.target.value) })}
                    className="w-full rounded border bg-white px-2 py-1 text-sm"
                  >
                    {MONTH_NAMES.slice(1).map((name, i) => (
                      <option key={i + 1} value={i + 1}>
                        {name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1.5">
                  <select
                    value={row.product_type}
                    onChange={(e) => updateRow(row.id, { product_type: e.target.value })}
                    className="w-full rounded border bg-white px-2 py-1 text-sm"
                  >
                    {PRODUCT_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1.5">
                  <Input
                    value={row.product_name}
                    onChange={(e) => updateRow(row.id, { product_name: e.target.value })}
                    placeholder="e.g. Sapling 3:2:1"
                    className="h-8"
                  />
                </td>
                <td className="px-2 py-1.5">
                  <Input
                    type="number"
                    value={row.rate_kg_ha ?? ""}
                    onChange={(e) =>
                      updateRow(row.id, {
                        rate_kg_ha: e.target.value ? parseFloat(e.target.value) : null,
                      })
                    }
                    placeholder="0"
                    className="h-8 w-24"
                  />
                </td>
                <td className="px-2 py-1.5">
                  <select
                    value={row.method}
                    onChange={(e) => updateRow(row.id, { method: e.target.value })}
                    className="w-full rounded border bg-white px-2 py-1 text-sm"
                  >
                    {APPLICATION_METHODS.map((m) => (
                      <option key={m} value={m}>
                        {m.charAt(0).toUpperCase() + m.slice(1)}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-2 py-1.5">
                  <Button variant="ghost" size="sm" onClick={() => removeRow(row.id)}>
                    <Trash2 className="size-3.5 text-red-500" />
                  </Button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-sm text-muted-foreground">
                  No applications added yet. Click "Add Application" to start.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <Button variant="outline" onClick={addRow} className="w-full">
        <Plus className="size-4" />
        Add Application
      </Button>
    </div>
  );
}
