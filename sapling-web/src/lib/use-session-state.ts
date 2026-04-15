"use client";

import { useState, useEffect, useCallback } from "react";

/**
 * Like useState, but persists to sessionStorage so values survive navigation.
 * Call clearSessionGroup(groupKey) to reset all fields in a group.
 */
export function useSessionState<T>(
  groupKey: string,
  fieldKey: string,
  initialValue: T
): [T, (val: T | ((prev: T) => T)) => void] {
  const storageKey = `${groupKey}:${fieldKey}`;

  const [value, setValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;
    try {
      const stored = sessionStorage.getItem(storageKey);
      if (stored !== null) return JSON.parse(stored);
    } catch {}
    return initialValue;
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify(value));
    } catch {}
  }, [storageKey, value]);

  return [value, setValue];
}

/**
 * Clear all sessionStorage keys for a given group prefix.
 */
export function clearSessionGroup(groupKey: string) {
  if (typeof window === "undefined") return;
  const toRemove: string[] = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key?.startsWith(`${groupKey}:`)) toRemove.push(key);
  }
  toRemove.forEach((k) => sessionStorage.removeItem(k));
}
