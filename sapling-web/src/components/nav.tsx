"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Menu,
  ChevronDown,
  Shield,
  User,
  LogOut,
  FlaskConical,
  Leaf,
  Calendar,
  FileText,
  Users,
  Archive,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { api } from "@/lib/api";

const mainLinks = [
  { href: "/quick-blend", label: "Quick Blend", icon: FlaskConical },
  // /quick-analysis was removed — replaced by per-client Soil Reports
  // (sidebar action on the client detail page). Soil interpretation
  // now lives at /clients/[id]/soil-reports rather than as a global
  // entry point because it's always client-scoped.
  { href: "/season-manager", label: "Season Manager", icon: Calendar },
  { href: "/quotes", label: "Quotes", icon: FileText },
  { href: "/clients", label: "Clients", icon: Users },
  { href: "/records", label: "Records", icon: Archive },
];

// Desktop nav shows text only (no icons) — icons are for mobile sidebar only

const adminLinks = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/admin/materials", label: "Materials" },
  { href: "/admin/markups", label: "Markups" },
  { href: "/admin/norms", label: "Norms" },
  { href: "/admin/quotes", label: "Quotes" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/audit", label: "Audit" },
  { href: "/admin/ai-usage", label: "AI Usage" },
];

function NavLink({
  href,
  label,
  icon: Icon,
  active,
  badge,
}: {
  href: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  active: boolean;
  badge?: number;
}) {
  return (
    <Link
      href={href}
      className={`relative inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "text-[var(--sapling-orange)]"
          : "text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
      }`}
    >
      {Icon && <Icon className="size-4" />}
      {label}
      {badge != null && badge > 0 && (
        <span className="absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
          {badge > 9 ? "9+" : badge}
        </span>
      )}
      {active && (
        <span className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-[var(--sapling-orange)]" />
      )}
    </Link>
  );
}

function getInitials(name: string | undefined): string {
  if (!name) return "?";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function Nav() {
  const { profile, isAdmin, signOut } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const showAdmin = useEffectiveAdmin();
  const [quoteUnread, setQuoteUnread] = useState(0);

  // Poll for unread quote messages every 30 seconds
  useEffect(() => {
    if (!profile) return;
    function fetchUnread() {
      api.get<{ count: number }>("/api/quotes/unread-count")
        .then((r) => setQuoteUnread(r.count))
        .catch(() => {});
    }
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, [profile]);

  return (
    <header className="sticky top-0 z-50 h-[120px] border-b border-gray-200 bg-white">
      <div className="mx-auto flex h-full max-w-7xl items-center justify-between px-4">
        {/* Left: Logo */}
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/logo_no_slogan.png"
            alt="Sapling"
            width={360}
            height={96}
            className="h-24 w-auto"
            priority
          />
        </Link>

        {/* Center: Nav links (desktop) */}
        <nav className="hidden items-center gap-1 md:flex">
          {mainLinks.map((link) => (
            <NavLink
              key={link.href}
              href={link.href}
              label={link.label}
              active={pathname.startsWith(link.href)}
              badge={link.href === "/quotes" ? quoteUnread : undefined}
            />
          ))}

          {/* Admin dropdown */}
          {showAdmin && (
            <DropdownMenu>
              <DropdownMenuTrigger
                className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-sm font-medium transition-colors hover:bg-gray-100 ${
                  pathname.startsWith("/admin")
                    ? "text-[var(--sapling-orange)]"
                    : "text-[var(--sapling-medium-grey)]"
                }`}
              >
                <Shield className="size-4" />
                Admin
                <ChevronDown className="size-3" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="center">
                {adminLinks.map((link) => (
                  <DropdownMenuItem
                    key={link.href}
                    onClick={() => router.push(link.href)}
                  >
                    {link.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </nav>

        {/* Right: User menu (desktop) + Mobile hamburger */}
        <div className="flex items-center gap-2">
          {/* User dropdown (desktop) */}
          <DropdownMenu>
            <DropdownMenuTrigger className="hidden items-center gap-2 rounded-lg px-2.5 py-1.5 transition-colors hover:bg-gray-100 md:inline-flex">
              <Avatar className="size-7">
                <AvatarFallback className="bg-[var(--sapling-orange)] text-xs text-white">
                  {getInitials(profile?.name)}
                </AvatarFallback>
              </Avatar>
              <span className="text-sm font-medium text-[var(--sapling-dark)]">
                {profile?.name ?? "User"}
              </span>
              <ChevronDown className="size-3 text-[var(--sapling-medium-grey)]" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem
                onClick={() => router.push("/profile")}
                className="gap-2"
              >
                <User className="size-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => signOut()}
                className="gap-2 text-red-600"
              >
                <LogOut className="size-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Mobile hamburger */}
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger className="inline-flex size-8 items-center justify-center rounded-lg transition-colors hover:bg-gray-100 md:hidden">
              <Menu className="size-5" />
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <SheetHeader>
                <SheetTitle className="text-left">Menu</SheetTitle>
              </SheetHeader>
              <nav className="mt-6 flex flex-col gap-1">
                {mainLinks.map((link) => {
                  const Icon = link.icon;
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setMobileOpen(false)}
                      className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        pathname.startsWith(link.href)
                          ? "bg-orange-50 text-[var(--sapling-orange)]"
                          : "text-[var(--sapling-medium-grey)] hover:bg-gray-50"
                      }`}
                    >
                      {Icon && <Icon className="size-4" />}
                      {link.label}
                    </Link>
                  );
                })}

                {showAdmin && (
                  <>
                    <div className="my-2 border-t border-gray-200" />
                    <p className="px-3 py-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                      Admin
                    </p>
                    {adminLinks.map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={() => setMobileOpen(false)}
                        className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                          pathname.startsWith(link.href)
                            ? "bg-orange-50 text-[var(--sapling-orange)]"
                            : "text-[var(--sapling-medium-grey)] hover:bg-gray-50"
                        }`}
                      >
                        {link.label}
                      </Link>
                    ))}
                  </>
                )}

                <div className="my-2 border-t border-gray-200" />
                <Link
                  href="/profile"
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-[var(--sapling-medium-grey)] hover:bg-gray-50"
                >
                  <User className="size-4" />
                  Profile
                </Link>
                <button
                  onClick={() => {
                    setMobileOpen(false);
                    signOut();
                  }}
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium text-red-600 hover:bg-red-50"
                >
                  <LogOut className="size-4" />
                  Sign out
                </button>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
