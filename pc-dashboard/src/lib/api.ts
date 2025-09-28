import axios from "axios";
import type { ApiResp } from "../types";

export const API_BASE = "http://localhost:3000/api";
export const api = axios.create({ baseURL: API_BASE, timeout: 15000 });

export async function getOk<T>(url: string, config?: any): Promise<T> {
  const r = await api.get<ApiResp<T>>(url, config);
  if (r.data?.ok) return r.data.data as T;
  throw new Error((r.data as any)?.message || "API error");
}

export async function postOk<T>(
  url: string,
  body?: any,
  config?: any
): Promise<T> {
  const r = await api.post<ApiResp<T>>(url, body, config);
  if (r.data?.ok) return r.data.data as T;
  throw new Error((r.data as any)?.message || "API error");
}

export async function putOk<T>(
  url: string,
  body?: any,
  config?: any
): Promise<T> {
  const r = await api.post<ApiResp<T>>(url, body, config);
  if (r.data?.ok) return r.data.data as T;
  throw new Error((r.data as any)?.message || "API error");
}
