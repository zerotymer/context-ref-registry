"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTransition } from "react";
import { cn } from "@/lib/utils";
import { logoutAction } from "@/lib/actions/auth";
import type { UserRead } from "@/lib/actions/auth";

interface NavItem {
  href: string;
  label: string;
  badge?: number;
  icon: React.ReactNode;
}

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md text-sm",
        active
          ? "bg-indigo-50 text-indigo-700 font-medium"
          : "text-gray-600 hover:bg-gray-50",
      )}
    >
      {item.icon}
      {item.label}
      {item.badge !== undefined && item.badge > 0 && (
        <span className="ml-auto bg-amber-100 text-amber-700 text-xs font-semibold px-1.5 py-0.5 rounded-full">
          {item.badge}
        </span>
      )}
    </Link>
  );
}

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    admin: "bg-red-50 text-red-600 border-red-200",
    project_admin: "bg-indigo-50 text-indigo-600 border-indigo-200",
    user: "bg-gray-50 text-gray-600 border-gray-200",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center border px-1.5 py-0.5 rounded-full text-xs font-medium",
        colors[role] ?? colors.user,
      )}
    >
      {role}
    </span>
  );
}

interface SidebarProps {
  candidateCount?: number;
  user: UserRead;
}

export function Sidebar({ candidateCount = 0, user }: SidebarProps) {
  const [pending, startTransition] = useTransition();

  const baseItems: NavItem[] = [
    {
      href: "/",
      label: "Dashboard",
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0h6" />
        </svg>
      ),
    },
    {
      href: "/entities",
      label: "Entity 목록",
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
      ),
    },
    {
      href: "/review",
      label: "승인 대기",
      badge: candidateCount,
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      href: "/bundle",
      label: "Bundle 탐색기",
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
  ];

  const adminItems: NavItem[] = [
    {
      href: "/admin/users",
      label: "사용자 관리",
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ),
    },
    {
      href: "/admin/projects",
      label: "프로젝트 관리",
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
      ),
    },
  ];

  const projectAdminItems: NavItem[] = [
    {
      href: "/admin/projects",
      label: "내 프로젝트 관리",
      icon: (
        <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
  ];

  const initials = user.email[0]?.toUpperCase() ?? "U";

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="px-4 py-4 border-b border-gray-100">
        <div className="font-semibold text-gray-900 text-base leading-tight">
          LLM Reference
          <br />
          Registry
        </div>
        <div className="text-xs text-gray-400 mt-0.5">v0.1.0</div>
      </div>

      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {baseItems.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}

        {user.role === "admin" && (
          <>
            <div className="pt-3 pb-1 px-3">
              <div className="text-xs font-medium text-gray-400 uppercase tracking-wide">관리자</div>
            </div>
            {adminItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </>
        )}

        {user.role === "project_admin" && (
          <>
            <div className="pt-3 pb-1 px-3">
              <div className="text-xs font-medium text-gray-400 uppercase tracking-wide">내 프로젝트</div>
            </div>
            {projectAdminItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </>
        )}
      </nav>

      <div className="px-4 py-3 border-t border-gray-100 text-xs">
        <div className="flex items-center gap-2 text-gray-600 mb-1">
          <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-semibold text-xs shrink-0">
            {initials}
          </span>
          <span className="truncate">{user.email}</span>
        </div>
        <div className="flex items-center justify-between">
          <RoleBadge role={user.role} />
          <button
            onClick={() => startTransition(() => logoutAction())}
            disabled={pending}
            className="text-gray-400 hover:text-gray-600 text-xs disabled:opacity-50"
          >
            로그아웃
          </button>
        </div>
      </div>
    </aside>
  );
}
