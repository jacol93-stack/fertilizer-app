"use client";

import { useEffect, useState } from "react";
import { setImpersonateUser } from "@/lib/api";
import { Eye, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ImpersonatedUser {
  id: string;
  name: string;
  email: string;
  role: string;
}

const STORAGE_KEY = "sapling_impersonate";

function loadFromStorage(): ImpersonatedUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const user = JSON.parse(raw);
      setImpersonateUser(user.id); // sync with api.ts
      return user;
    }
  } catch {}
  return null;
}

function saveToStorage(user: ImpersonatedUser | null) {
  if (typeof window === "undefined") return;
  if (user) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    setImpersonateUser(user.id);
  } else {
    sessionStorage.removeItem(STORAGE_KEY);
    setImpersonateUser(null);
  }
}

// Global state
let _listeners: Array<() => void> = [];
let _impersonatedUser: ImpersonatedUser | null = null;

// Initialize from storage on module load
if (typeof window !== "undefined") {
  _impersonatedUser = loadFromStorage();
}

export function startImpersonation(user: ImpersonatedUser) {
  _impersonatedUser = user;
  saveToStorage(user);
  _listeners.forEach((fn) => fn());
}

export function stopImpersonation() {
  _impersonatedUser = null;
  saveToStorage(null);
  _listeners.forEach((fn) => fn());
}

export function getImpersonatedUser(): ImpersonatedUser | null {
  return _impersonatedUser;
}

export function useImpersonation() {
  const [, setTick] = useState(0);

  useEffect(() => {
    // Re-sync from storage on mount (handles page reloads)
    const stored = loadFromStorage();
    if (stored) {
      _impersonatedUser = stored;
      setTick((t) => t + 1);
    }

    const listener = () => setTick((t) => t + 1);
    _listeners.push(listener);
    return () => {
      _listeners = _listeners.filter((fn) => fn !== listener);
    };
  }, []);

  return {
    impersonatedUser: _impersonatedUser,
    isImpersonating: !!_impersonatedUser,
    startImpersonation,
    stopImpersonation,
  };
}

export function ImpersonationBanner() {
  const { impersonatedUser, isImpersonating } = useImpersonation();

  if (!isImpersonating || !impersonatedUser) return null;

  return (
    <div className="sticky top-0 z-[100] flex items-center justify-between bg-red-600 px-4 py-2.5 text-white shadow-md">
      <div className="flex items-center gap-3">
        <Eye className="size-4 shrink-0" />
        <span className="text-sm">
          Viewing as <strong>{impersonatedUser.name}</strong> ({impersonatedUser.email}) - {impersonatedUser.role}
        </span>
      </div>
      <Button
        size="sm"
        variant="ghost"
        className="text-white hover:bg-red-700 hover:text-white"
        onClick={() => {
          stopImpersonation();
          window.location.href = "/admin/users";
        }}
      >
        <ArrowLeft className="size-3.5" />
        Back to Admin
      </Button>
    </div>
  );
}
