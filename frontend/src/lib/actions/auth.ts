"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const BACKEND = process.env.BACKEND_API_URL ?? "http://localhost:8000";
const COOKIE_NAME = "access_token";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

export interface UserRead {
  id: string;
  login_id: string;
  display_name: string;
  role: string;
  is_active: boolean;
  must_change_password: boolean;
}

export async function getCurrentUser(): Promise<UserRead | null> {
  const token = cookies().get(COOKIE_NAME)?.value;
  if (!token) return null;

  try {
    const res = await fetch(`${BACKEND}/auth/me`, {
      headers: {
        Cookie: `${COOKIE_NAME}=${token}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = await res.json();
    return body.ok ? (body.data as UserRead) : null;
  } catch {
    return null;
  }
}

export async function loginAction(loginId: string, password: string): Promise<UserRead> {
  const res = await fetch(`${BACKEND}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ login_id: loginId, password }),
    cache: "no-store",
  });

  const body = await res.json();
  if (!body.ok) {
    const code = body.error?.code ?? "UNKNOWN";
    const message = body.error?.message ?? "로그인에 실패했습니다.";
    throw new Error(`${code}:${message}`);
  }

  const setCookieHeader = res.headers.get("set-cookie");
  if (setCookieHeader) {
    const match = setCookieHeader.match(/access_token=([^;]+)/);
    if (match) {
      cookies().set(COOKIE_NAME, match[1], {
        httpOnly: true,
        sameSite: "lax",
        maxAge: COOKIE_MAX_AGE,
        path: "/",
      });
    }
  }

  return body.data as UserRead;
}

export async function changePasswordAction(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  const token = cookies().get(COOKIE_NAME)?.value;
  if (!token) throw new Error("UNAUTHORIZED:로그인이 필요합니다.");

  const res = await fetch(`${BACKEND}/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Cookie: `${COOKIE_NAME}=${token}`,
    },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    cache: "no-store",
  });

  const body = await res.json();
  if (!body.ok) {
    const code = body.error?.code ?? "UNKNOWN";
    const message = body.error?.message ?? "비밀번호 변경에 실패했습니다.";
    throw new Error(`${code}:${message}`);
  }
}

export async function logoutAction(): Promise<void> {
  const token = cookies().get(COOKIE_NAME)?.value;
  if (token) {
    await fetch(`${BACKEND}/auth/logout`, {
      method: "POST",
      headers: { Cookie: `${COOKIE_NAME}=${token}` },
      cache: "no-store",
    }).catch(() => {});
  }
  cookies().delete(COOKIE_NAME);
  redirect("/login");
}
