"use client";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LEAF_ELEMENTS } from "../types";

interface LeafInputFormProps {
  leafValues: Record<string, string>;
  onChange: (values: Record<string, string>) => void;
}

export function LeafInputForm({ leafValues, onChange }: LeafInputFormProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Leaf Element Concentrations</CardTitle>
        <CardDescription>
          Enter values from lab report (% for macros, mg/kg for micros)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3">
          {LEAF_ELEMENTS.map((elem) => (
            <div key={elem} className="space-y-1.5">
              <Label htmlFor={`leaf-${elem}`}>
                {elem} {["N", "P", "K", "Ca", "Mg", "S"].includes(elem) ? "(%)" : "(mg/kg)"}
              </Label>
              <Input
                id={`leaf-${elem}`}
                type="number"
                step="0.01"
                placeholder="0"
                value={leafValues[elem] || ""}
                onChange={(e) =>
                  onChange({ ...leafValues, [elem]: e.target.value })
                }
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
