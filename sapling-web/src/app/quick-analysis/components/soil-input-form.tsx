"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SOIL_PARAMS, PARAM_LABELS } from "../types";

interface SoilInputFormProps {
  soilValues: Record<string, string>;
  onChange: (values: Record<string, string>) => void;
  labName: string;
  onLabNameChange: (v: string) => void;
  analysisDate: string;
  onAnalysisDateChange: (v: string) => void;
}

export function SoilInputForm({
  soilValues,
  onChange,
  labName,
  onLabNameChange,
  analysisDate,
  onAnalysisDateChange,
}: SoilInputFormProps) {
  return (
    <>
      {/* Lab info */}
      <Card>
        <CardHeader>
          <CardTitle>Lab Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="labName">Lab Name</Label>
              <Input
                id="labName"
                value={labName}
                onChange={(e) => onLabNameChange(e.target.value)}
                placeholder="e.g. NviroTek"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="analysisDate">Analysis Date</Label>
              <Input
                id="analysisDate"
                type="date"
                value={analysisDate}
                onChange={(e) => onAnalysisDateChange(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Soil values by group */}
      {Object.entries(SOIL_PARAMS).map(([group, params]) => (
        <Card key={group}>
          <CardHeader>
            <CardTitle>{group}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {params.map((param) => (
                <div key={param} className="space-y-1.5">
                  <Label htmlFor={param}>{PARAM_LABELS[param] || param}</Label>
                  <Input
                    id={param}
                    type="number"
                    step="any"
                    value={soilValues[param] || ""}
                    onChange={(e) => {
                      const updated = { ...soilValues, [param]: e.target.value };
                      // pH correlation: always update the other from the last edited
                      const val = parseFloat(e.target.value);
                      if (param === "pH (H2O)" && val > 0) {
                        updated["pH (KCl)"] = (val - 1).toFixed(2);
                      } else if (param === "pH (KCl)" && val > 0) {
                        updated["pH (H2O)"] = (val + 1).toFixed(2);
                      }
                      onChange(updated);
                    }}
                    placeholder="0"
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </>
  );
}
