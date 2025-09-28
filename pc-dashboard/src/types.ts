export type Id = number;
export type Boolish = 0 | 1 | boolean;
export type Point = { x: number; y: number };

export type Camera = {
  camera_id: Id;
  name: string;
  source_url?: string | null;
  location_note?: string | null;
  is_active: Boolish;
  timestamp: string;
};

export type Area = {
  area_id: Id;
  camera_id: Id;
  area_nama: string;
  deskripsi?: string | null;
  polygon: Point[]; // JSON from backend
  is_active: Boolish;
  timestamp: string;
};

export type EventRow = {
  counting_id: Id;
  timestamp: string;
  camera_id: Id;
  masuk: number | 0;
  keluar: number | 0;
  dalam: number | 0;
};

export type ApiOk<T> = { ok: true; data: T };
export type ApiErr = { ok: false; code: string; message?: string };
export type ApiResp<T> = ApiOk<T> | ApiErr;
