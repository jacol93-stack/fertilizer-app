"use client";

interface LeafData {
  id: string;
  crop: string | null;
  cultivar?: string | null;
  sample_part?: string | null;
  sample_date?: string | null;
  lab_name?: string | null;
  farm_id?: string | null;
  field_id?: string | null;
  values: Record<string, number | string | null> | null;
  classifications: Record<string, string> | null;
  recommendations?: Record<string, unknown> | null;
  foliar_recommendations?: Record<string, unknown>[] | null;
  notes?: string | null;
  created_at?: string | null;
  // Resolved names (set by parent)
  farm_name?: string;
  field_name?: string;
}

function leafClassColor(c: string): string {
  const lower = (c || "").toLowerCase();
  if (lower === "sufficient" || lower === "adequate") return "bg-green-100 text-green-700";
  if (lower === "deficient") return "bg-red-100 text-red-700";
  if (lower === "low") return "bg-orange-100 text-orange-700";
  if (lower === "high") return "bg-blue-100 text-blue-700";
  if (lower === "excess" || lower === "toxic") return "bg-purple-100 text-purple-700";
  return "bg-gray-100 text-gray-700";
}

export function LeafDetailView({ leaf }: { leaf: LeafData }) {
  const valueEntries = leaf.values
    ? Object.entries(leaf.values).filter(([, v]) => v !== null && v !== "")
    : [];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">
          {leaf.crop || "Unknown Crop"}
          {leaf.cultivar ? ` — ${leaf.cultivar}` : ""}
        </h3>
        <div className="mt-1 flex flex-wrap gap-3 text-sm text-muted-foreground">
          {leaf.sample_part && <span>Part: {leaf.sample_part}</span>}
          {leaf.lab_name && <span>Lab: {leaf.lab_name}</span>}
          {leaf.sample_date && <span>Date: {leaf.sample_date}</span>}
          {leaf.farm_name && <span>Farm: {leaf.farm_name}</span>}
          {leaf.field_name && <span>Field: {leaf.field_name}</span>}
        </div>
      </div>

      {/* Leaf Values + Classifications */}
      {valueEntries.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Element Concentrations
          </h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2">Element</th>
                  <th className="px-3 py-2 text-right">Value</th>
                  {leaf.classifications && (
                    <th className="px-3 py-2 text-center">Classification</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {valueEntries.map(([elem, val]) => (
                  <tr key={elem} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{elem}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{val}</td>
                    {leaf.classifications && (
                      <td className="px-3 py-2 text-center">
                        {leaf.classifications[elem] && (
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${leafClassColor(
                              leaf.classifications[elem]
                            )}`}
                          >
                            {leaf.classifications[elem]}
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Foliar Recommendations */}
      {leaf.foliar_recommendations && leaf.foliar_recommendations.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Foliar Recommendations
          </h4>
          <div className="space-y-2">
            {leaf.foliar_recommendations.map((rec, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
              >
                <p className="font-medium text-[var(--sapling-dark)]">
                  {String(rec.product || rec.name || `Recommendation ${i + 1}`)}
                </p>
                {rec.rate ? (
                  <p className="text-muted-foreground">
                    Rate: {String(rec.rate)}{rec.unit ? ` ${String(rec.unit)}` : ""}
                  </p>
                ) : null}
                {rec.notes ? (
                  <p className="text-xs text-muted-foreground">{String(rec.notes)}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {leaf.notes && (
        <div>
          <h4 className="mb-1 text-sm font-semibold text-[var(--sapling-dark)]">Notes</h4>
          <p className="text-sm text-muted-foreground">{leaf.notes}</p>
        </div>
      )}
    </div>
  );
}
