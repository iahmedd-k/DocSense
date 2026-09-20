import type { ApiError } from "./types";

const RAW_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  (import.meta.env.VITE_API_URL as string | undefined) ||
  "";

const cleanUrl = RAW_BASE_URL.trim().replace(/\/+$/, "");
const BASE_URL = cleanUrl
  ? cleanUrl.endsWith("/api/v1")
    ? cleanUrl
    : `${cleanUrl}/api/v1`
  : "/api/v1";

let activeToken: string | null = null;
let authTokenGetter: (() => Promise<string | null>) | null = null;

export function setAuthTokenGetter(getter: () => Promise<string | null>) {
  authTokenGetter = getter;
}

export function setToken(token: string) {
  activeToken = token;
  try {
    localStorage.setItem("token", token);
  } catch {
    // Storage access might be denied in some iframe environments
  }
}

export function clearToken() {
  activeToken = null;
  try {
    localStorage.removeItem("token");
  } catch {
    // Storage access might be denied in some iframe environments
  }
}

export async function getAuthToken(): Promise<string | null> {
  if (authTokenGetter) {
    try {
      const token = await authTokenGetter();
      if (token) {
        activeToken = token;
        return token;
      }
    } catch {
      // Fall back to stored token
    }
  }
  if (activeToken) return activeToken;
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return !!activeToken || !!localStorage.getItem("token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers["Content-Type"]
  ) {
    headers["Content-Type"] = "application/json";
  }

  const url = `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  let res: Response;
  try {
    res = await fetch(url, { ...options, headers });
  } catch (err: unknown) {
    const error: ApiError = {
      status_code: 0,
      message: (err as Error)?.message || "Network error. Please check your connection.",
    };
    throw error;
  }

  if (res.status === 204) {
    return undefined as T;
  }

  let data: any = null;
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      data = await res.json();
    } catch {
      data = null;
    }
  } else {
    try {
      const text = await res.text();
      data = { message: text };
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    if (res.status === 401) {
      clearToken();
    }
    const errorMessage =
      data?.message ||
      data?.detail ||
      (typeof data === "string" ? data : null) ||
      `Request failed (${res.status})`;
    const error: ApiError = {
      status_code: res.status,
      message: errorMessage,
    };
    throw error;
  }

  return (data?.data !== undefined ? data.data : data) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export async function streamChat(
  body: { query: string; evidence: unknown[]; temperature?: number },
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (msg: string) => void,
) {
  const token = await getAuthToken();
  const url = `${BASE_URL}/chat/stream`;
  let res: Response;

  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
  } catch (err: unknown) {
    onError((err as Error)?.message || "Network error while connecting to chat stream.");
    return;
  }

  if (!res.ok) {
    let errText = `Stream failed (${res.status})`;
    try {
      const data = await res.json();
      errText = data?.message || data?.detail || errText;
    } catch {
      // ignore
    }
    if (res.status === 401) {
      clearToken();
    }
    onError(errText);
    return;
  }

  if (!res.body) {
    onError("ReadableStream not supported on this response.");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        const jsonStr = trimmed.slice(6);
        try {
          const evt = JSON.parse(jsonStr);
          if (evt.event === "chunk") {
            onChunk(evt.data);
          } else if (evt.event === "done") {
            onDone();
          } else if (evt.event === "error") {
            onError(evt.data);
            return;
          }
        } catch {
          // skip malformed lines
        }
      }
    }
  } catch (err: unknown) {
    onError((err as Error)?.message || "Error reading stream");
    return;
  }

  onDone();
}
