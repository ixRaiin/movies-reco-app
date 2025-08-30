export type ApiErrorEnvelope = {
  code: string
  message: string
  hint?: string | null
  dependency?: string | null
  trace_id?: string
}

export async function parseApiError(e: unknown): Promise<ApiErrorEnvelope> {
  // if a Response was thrown
  if (e instanceof Response) {
    try {
      const data = await e.clone().json()
      return data
    } catch {
      const txt = await e.text()
      return { code: `http_${e.status}`, message: txt || e.statusText }
    }
  }

  // if our api.ts threw Error(await res.text())
  if (e && typeof e === "object" && "message" in e) {
    const msg = String((e as any).message || "")
    try {
      const data = JSON.parse(msg)
      return data
    } catch {
      return { code: "client_error", message: msg || "Unknown error" }
    }
  }

  // fallback
  return { code: "unknown_error", message: String(e ?? "Unknown error") }
}
