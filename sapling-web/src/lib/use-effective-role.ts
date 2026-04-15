"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

/**
 * Returns the effective admin status, accounting for impersonation.
 * When an admin is impersonating a non-admin agent, this returns false.
 */
export function useEffectiveAdmin(): boolean {
  const { isAdmin } = useAuth();
  const [effective, setEffective] = useState(isAdmin);

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem("sapling_impersonate");
      if (stored) {
        const imp = JSON.parse(stored);
        setEffective(imp.role === "admin");
      } else {
        setEffective(isAdmin);
      }
    } catch {
      setEffective(isAdmin);
    }
  }, [isAdmin]);

  return effective;
}
