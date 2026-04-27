import { Suspense } from "react";
import { AdminPortalShell } from "@/components/admin-portal/portal-shell";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense>
      <AdminPortalShell>{children}</AdminPortalShell>
    </Suspense>
  );
}
