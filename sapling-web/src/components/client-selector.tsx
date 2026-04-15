"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, ChevronDown } from "lucide-react";

interface Client {
  id: string;
  name: string;
  contact_person?: string;
}
interface Farm {
  id: string;
  name: string;
  client_id: string;
  region?: string;
}
interface Field {
  id: string;
  name: string;
  farm_id: string;
  size_ha?: number;
  soil_type?: string;
}

interface ClientSelectorProps {
  onSelect: (selection: {
    client_id?: string;
    client_name: string;
    farm_id?: string;
    farm_name: string;
    field_id?: string;
    field_name: string;
  }) => void;
  initialClient?: string;
  initialFarm?: string;
  initialField?: string;
  showField?: boolean;
}

/** Combobox-style dropdown: click to open full list, type to filter, create new inline. */
export function ComboBox({
  label,
  placeholder,
  disabled,
  items,
  value,
  onChange,
  onSelect,
  onCreate,
  creating,
  displayKey = "name",
  secondaryKey,
  secondaryFormat,
}: {
  label: string;
  placeholder: string;
  disabled?: boolean;
  items: Record<string, unknown>[];
  value: string;
  onChange: (val: string) => void;
  onSelect: (item: Record<string, unknown>) => void;
  onCreate?: () => void;
  creating?: boolean;
  displayKey?: string;
  secondaryKey?: string;
  secondaryFormat?: (item: Record<string, unknown>) => string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const [showAll, setShowAll] = useState(false);
  const filtered = showAll ? items : items.filter((item) =>
    String(item[displayKey] || "")
      .toLowerCase()
      .includes(value.toLowerCase())
  );

  const exactMatch = items.some(
    (item) =>
      String(item[displayKey] || "").toLowerCase() === value.trim().toLowerCase()
  );

  return (
    <div className="relative overflow-visible" ref={ref}>
      <Label>{label}</Label>
      <div className="relative">
        <Input
          placeholder={placeholder}
          disabled={disabled}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setShowAll(false);
            setOpen(true);
          }}
          onFocus={() => { setShowAll(true); setOpen(true); }}
        />
        {!disabled && (
          <button
            type="button"
            tabIndex={-1}
            onClick={() => { setShowAll(true); setOpen(!open); }}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:text-foreground"
          >
            <ChevronDown className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
        )}
      </div>
      {open && !disabled && (
        <div className="absolute z-[100] mt-1 w-full rounded-md border bg-white shadow-lg max-h-64 overflow-y-auto">
          {filtered.length === 0 && !value.trim() && (
            <div className="px-3 py-2 text-sm text-muted-foreground">
              No items yet
            </div>
          )}
          {filtered.map((item) => (
            <button
              key={String(item.id)}
              type="button"
              className="w-full text-left px-3 py-2 hover:bg-gray-100 text-sm flex items-center justify-between"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onSelect(item);
                setOpen(false);
                setShowAll(false);
              }}
            >
              <span className="font-medium">{String(item[displayKey])}</span>
              {secondaryFormat && (
                <span className="text-xs text-muted-foreground">
                  {secondaryFormat(item)}
                </span>
              )}
              {!secondaryFormat && secondaryKey && item[secondaryKey] ? (
                <span className="text-xs text-muted-foreground">
                  {String(item[secondaryKey])}
                </span>
              ) : null}
            </button>
          ))}
          {value.trim() && !exactMatch && onCreate && (
            <button
              type="button"
              className="w-full text-left px-3 py-2 hover:bg-orange-50 text-sm flex items-center gap-2 text-[var(--sapling-orange)] border-t"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onCreate();
                setOpen(false);
              }}
              disabled={creating}
            >
              <Plus className="size-4" />
              {creating ? "Creating..." : `Create "${value.trim()}"`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export function ClientSelector({
  onSelect,
  initialClient = "",
  initialFarm = "",
  initialField = "",
  showField = true,
}: ClientSelectorProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [fields, setFields] = useState<Field[]>([]);

  const [clientSearch, setClientSearch] = useState(initialClient);
  const [farmSearch, setFarmSearch] = useState(initialFarm);
  const [fieldSearch, setFieldSearch] = useState(initialField);

  const [selectedClientId, setSelectedClientId] = useState<string>();
  const [selectedFarmId, setSelectedFarmId] = useState<string>();
  const [selectedFieldId, setSelectedFieldId] = useState<string>();

  const [creatingClient, setCreatingClient] = useState(false);
  const [creatingFarm, setCreatingFarm] = useState(false);
  const [creatingField, setCreatingField] = useState(false);
  const restoringRef = useRef(!!initialClient);

  // Sync from props when they change (e.g. URL param pre-fill after mount)
  const prevInitialRef = useRef({ client: initialClient, farm: initialFarm, field: initialField });
  useEffect(() => {
    const prev = prevInitialRef.current;
    const clientChanged = initialClient && initialClient !== prev.client;
    if (clientChanged) {
      setClientSearch(initialClient);
      // Resolve client ID and cascade to farm/field
      restoringRef.current = true;
      const match = clients.find((c) => c.name.toLowerCase() === initialClient.toLowerCase());
      if (match) {
        setSelectedClientId(match.id);
        api.get<Farm[]>(`/api/clients/${match.id}/farms`).then(async (farmsData) => {
          setFarms(farmsData);
          if (initialFarm) {
            setFarmSearch(initialFarm);
            const farmMatch = farmsData.find((f) => f.name.toLowerCase() === initialFarm.toLowerCase());
            if (farmMatch) {
              setSelectedFarmId(farmMatch.id);
              if (initialField) {
                setFieldSearch(initialField);
                try {
                  const fieldsData = await api.get<Field[]>(`/api/clients/farms/${farmMatch.id}/fields`);
                  setFields(fieldsData);
                  const fieldMatch = fieldsData.find((f) => f.name.toLowerCase() === initialField.toLowerCase());
                  if (fieldMatch) setSelectedFieldId(fieldMatch.id);
                } catch {}
              }
            }
          }
          restoringRef.current = false;
        }).catch(() => { restoringRef.current = false; });
      } else {
        restoringRef.current = false;
      }
    } else {
      if (initialFarm && initialFarm !== prev.farm) setFarmSearch(initialFarm);
      if (initialField && initialField !== prev.field) setFieldSearch(initialField);
    }
    prevInitialRef.current = { client: initialClient, farm: initialFarm, field: initialField };
  }, [initialClient, initialFarm, initialField, clients]);

  // Load clients on mount, and resolve IDs if initial names are provided
  useEffect(() => {
    api.getAll<Client>("/api/clients").then(async (data) => {
      setClients(data);
      if (initialClient) {
        const match = data.find(
          (c) => c.name.toLowerCase() === initialClient.toLowerCase()
        );
        if (match) {
          setSelectedClientId(match.id);
          // Eagerly load farms and resolve farm ID
          try {
            const farmsData = await api.get<Farm[]>(`/api/clients/${match.id}/farms`);
            setFarms(farmsData);
            if (initialFarm) {
              const farmMatch = farmsData.find(
                (f) => f.name.toLowerCase() === initialFarm.toLowerCase()
              );
              if (farmMatch) {
                setSelectedFarmId(farmMatch.id);
                // Eagerly load fields and resolve field ID
                if (initialField) {
                  try {
                    const fieldsData = await api.get<Field[]>(`/api/clients/farms/${farmMatch.id}/fields`);
                    setFields(fieldsData);
                    const fieldMatch = fieldsData.find(
                      (f) => f.name.toLowerCase() === initialField.toLowerCase()
                    );
                    if (fieldMatch) setSelectedFieldId(fieldMatch.id);
                  } catch {}
                }
              }
            }
          } catch {}
        }
      }
      restoringRef.current = false;
    }).catch(() => { restoringRef.current = false; });
  }, []);

  // Load farms when client selected (skip during restore)
  useEffect(() => {
    if (restoringRef.current) return;
    if (selectedClientId) {
      api
        .get<Farm[]>(`/api/clients/${selectedClientId}/farms`)
        .then(setFarms)
        .catch(() => setFarms([]));
    } else {
      setFarms([]);
    }
    setSelectedFarmId(undefined);
    setSelectedFieldId(undefined);
    setFarmSearch("");
    setFieldSearch("");
    setFields([]);
  }, [selectedClientId]);

  // Load fields when farm selected (skip during restore)
  useEffect(() => {
    if (restoringRef.current) return;
    if (selectedFarmId) {
      api
        .get<Field[]>(`/api/clients/farms/${selectedFarmId}/fields`)
        .then(setFields)
        .catch(() => setFields([]));
    } else {
      setFields([]);
    }
    setSelectedFieldId(undefined);
    setFieldSearch("");
  }, [selectedFarmId]);

  // Emit selection changes
  useEffect(() => {
    if (restoringRef.current) return;
    onSelect({
      client_id: selectedClientId,
      client_name: clientSearch,
      farm_id: selectedFarmId,
      farm_name: farmSearch,
      field_id: selectedFieldId,
      field_name: fieldSearch,
    });
  }, [selectedClientId, clientSearch, selectedFarmId, farmSearch, selectedFieldId, fieldSearch]);

  async function createQuickClient() {
    if (!clientSearch.trim()) return;
    setCreatingClient(true);
    try {
      const newClient = await api.post<Client>("/api/clients", {
        name: clientSearch.trim(),
      });
      setClients((prev) => [...prev, newClient]);
      setSelectedClientId(newClient.id);
    } catch {}
    setCreatingClient(false);
  }

  async function createQuickFarm() {
    if (!farmSearch.trim() || !selectedClientId) return;
    setCreatingFarm(true);
    try {
      const newFarm = await api.post<Farm>(
        `/api/clients/${selectedClientId}/farms`,
        { name: farmSearch.trim() }
      );
      setFarms((prev) => [...prev, newFarm]);
      setSelectedFarmId(newFarm.id);
    } catch {}
    setCreatingFarm(false);
  }

  async function createQuickField() {
    if (!fieldSearch.trim() || !selectedFarmId) return;
    setCreatingField(true);
    try {
      const newField = await api.post<Field>(
        `/api/clients/farms/${selectedFarmId}/fields`,
        { name: fieldSearch.trim() }
      );
      setFields((prev) => [...prev, newField]);
      setSelectedFieldId(newField.id);
    } catch {}
    setCreatingField(false);
  }

  return (
    <div className="space-y-3">
      <ComboBox
        label="Client"
        placeholder="Select or type client name..."
        items={clients as unknown as Record<string, unknown>[]}
        value={clientSearch}
        onChange={(val) => {
          setClientSearch(val);
          setSelectedClientId(undefined);
        }}
        onSelect={(item) => {
          setClientSearch(String(item.name));
          setSelectedClientId(String(item.id));
        }}
        onCreate={createQuickClient}
        creating={creatingClient}
        secondaryKey="contact_person"
      />

      <ComboBox
        label="Farm"
        placeholder={selectedClientId ? "Select or type farm name..." : "Select a client first"}
        disabled={!selectedClientId}
        items={farms as unknown as Record<string, unknown>[]}
        value={farmSearch}
        onChange={(val) => {
          setFarmSearch(val);
          setSelectedFarmId(undefined);
        }}
        onSelect={(item) => {
          setFarmSearch(String(item.name));
          setSelectedFarmId(String(item.id));
        }}
        onCreate={selectedClientId ? createQuickFarm : undefined}
        creating={creatingFarm}
        secondaryKey="region"
      />

      {showField && (
        <ComboBox
          label="Field"
          placeholder={selectedFarmId ? "Select or type field name..." : "Select a farm first"}
          disabled={!selectedFarmId}
          items={fields as unknown as Record<string, unknown>[]}
          value={fieldSearch}
          onChange={(val) => {
            setFieldSearch(val);
            setSelectedFieldId(undefined);
          }}
          onSelect={(item) => {
            setFieldSearch(String(item.name));
            setSelectedFieldId(String(item.id));
          }}
          onCreate={selectedFarmId ? createQuickField : undefined}
          creating={creatingField}
          secondaryFormat={(item) => {
            const parts: string[] = [];
            if (item.size_ha) parts.push(`${item.size_ha} ha`);
            if (item.soil_type) parts.push(String(item.soil_type));
            return parts.join(" · ");
          }}
        />
      )}
    </div>
  );
}
