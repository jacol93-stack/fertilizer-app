import { Suspense } from "react";
import { ClientPortalShell } from "@/components/client-portal/portal-shell";

export default async function ClientLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <Suspense>
      <ClientPortalShell clientId={id}>{children}</ClientPortalShell>
    </Suspense>
  );
}
