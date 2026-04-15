"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

export default function FarmDetailRedirect() {
  const params = useParams<{ id: string; farmId: string }>();
  const router = useRouter();

  useEffect(() => {
    // Redirect to client hub — farm detail is now handled there
    router.replace(`/clients/${params.id}`);
  }, [params.id, router]);

  return null;
}
