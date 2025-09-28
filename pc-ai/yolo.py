import os
import sys
import cv2
import time
import json
import base64
import signal
import threading
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from dotenv import load_dotenv
import numpy as np
import requests

# YOLO (Ultralytics, PyTorch)
from ultralytics import YOLO
import torch

# --- Async / WS ---
import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

# Windows event-loop policy (stabil websockets di Win10/11)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ---------------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------------
load_dotenv(dotenv_path="./.env")

CONFIG_URL = os.getenv("CONFIG_URL", "http://localhost:3000/api/config")
REPORT_URL = os.getenv("REPORT_URL", "http://localhost:3000/api/counting")
WS_URL     = os.getenv("WS_URL", "ws://127.0.0.1:8080/ws")

YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8s.pt")  # path/alias model
DEVICE     = os.getenv("DEVICE", "auto")            # "cuda" / "cpu" / "auto"
CONF_THR   = float(os.getenv("CONF_THR", "0.25"))

OUT_W, OUT_H = 640, 480
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL_SEC", "10"))
UI_TARGET_FPS  = float(os.getenv("UI_TARGET_FPS", "8.0"))

# COCO: person = class_id 0
PERSON_CLASS_ID = int(os.getenv("PERSON_CLASS_ID", "0"))

# ---------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------
def normalize_polygon(poly_in):
    if poly_in is None:
        raise ValueError("Polygon kosong")
    if isinstance(poly_in, np.ndarray):
        if poly_in.ndim == 2 and poly_in.shape[1] == 2:
            return poly_in.astype(np.int32)
        raise ValueError("Polygon ndarray harus Nx2")
    if len(poly_in) > 0 and isinstance(poly_in[0], dict):
        pts = []
        for p in poly_in:
            x = int(round(float(p["x"]))); y = int(round(float(p["y"])))
            pts.append([x, y])
        return np.array(pts, dtype=np.int32)
    if len(poly_in) > 0 and (isinstance(poly_in[0], (list, tuple)) and len(poly_in[0]) == 2):
        pts = []
        for p in poly_in:
            x = int(round(float(p[0]))); y = int(round(float(p[1])))
            pts.append([x, y])
        return np.array(pts, dtype=np.int32)
    raise ValueError("Format polygon tidak dikenali")

def point_in_polygon(pt: Tuple[int,int], polygon: np.ndarray) -> bool:
    return cv2.pointPolygonTest(polygon, pt, False) >= 0

def iou(b1, b2):
    x1 = max(b1[0], b2[0]); y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2]); y2 = min(b1[3], b2[3])
    inter = max(0, x2-x1) * max(0, y2-y1)
    a1 = (b1[2]-b1[0]) * (b1[3]-b1[1])
    a2 = (b2[2]-b2[0]) * (b2[3]-b2[1])
    union = a1 + a2 - inter + 1e-6
    return inter / union

def centroid(b):
    x1,y1,x2,y2 = b
    return ((x1+x2)//2, (y1+y2)//2)

# ---------------------------------------------------------------------
# Tracker (state via dict)
# ---------------------------------------------------------------------
tracker_state = {
    "next_id": 1,
    "tracks": {},       # tid -> Track
    "max_age": 1.5,
    "iou_thr": 0.3,
}
@dataclass
class Track:
    track_id: int
    bbox: Tuple[int,int,int,int]
    last_seen: float
    inside_poly: bool

def tracker_update(detections: List[Tuple[int,int,int,int]], polygon: np.ndarray) -> Dict[int, Track]:
    t = time.time()
    tracks: Dict[int, Track] = tracker_state["tracks"]
    det_used = [False]*len(detections)

    # match existing
    for tid, tr in list(tracks.items()):
        best_j = -1; best_iou = 0.0
        for j, det in enumerate(detections):
            if det_used[j]: continue
            iou_val = iou(tr.bbox, det)
            if iou_val > best_iou:
                best_iou = iou_val; best_j = j
        if best_j >= 0 and best_iou >= tracker_state["iou_thr"]:
            tr.bbox = detections[best_j]
            tr.last_seen = t
            cx, cy = centroid(detections[best_j])
            tr.inside_poly = point_in_polygon((cx,cy), polygon)
            det_used[best_j] = True

    # spawn new
    for j, det in enumerate(detections):
        if det_used[j]: continue
        tid = tracker_state["next_id"]; tracker_state["next_id"] += 1
        cx, cy = centroid(det)
        tracks[tid] = Track(
            track_id=tid,
            bbox=det,
            last_seen=t,
            inside_poly=point_in_polygon((cx,cy), polygon)
        )

    # prune
    for tid, tr in list(tracks.items()):
        if t - tr.last_seen > tracker_state["max_age"]:
            del tracks[tid]

    return {tid: tracks[tid] for tid in sorted(tracks)}

def tracker_reset():
    tracker_state["next_id"] = 1
    tracker_state["tracks"].clear()

# ---------------------------------------------------------------------
# YOLO detector (fungsi)
# ---------------------------------------------------------------------
_yolo_model = None
_yolo_device = "cpu"

def init_detector(model_path: str, device_pref: str = "auto", conf_thr: float = 0.25):
    global _yolo_model, _yolo_device, CONF_THR
    _yolo_model = YOLO(model_path)
    if device_pref == "cuda" or (device_pref == "auto" and torch.cuda.is_available()):
        _yolo_device = "cuda"; _yolo_model.to("cuda")
    else:
        _yolo_device = "cpu"; _yolo_model.to("cpu")
    CONF_THR = conf_thr
    print(f"[INFO] YOLO device: {_yolo_device}")

def detect_person(frame_bgr: np.ndarray) -> List[Tuple[int,int,int,int]]:
    if _yolo_model is None:
        raise RuntimeError("Detector belum di-init")
    result = _yolo_model(frame_bgr, conf=CONF_THR, verbose=False, device=_yolo_device)[0]
    dets: List[Tuple[int,int,int,int]] = []
    if result.boxes is None or len(result.boxes) == 0:
        return dets
    xyxy = result.boxes.xyxy.cpu().numpy().astype(int)
    clss = result.boxes.cls.cpu().numpy().astype(int)
    h, w = frame_bgr.shape[:2]
    for i, cls_id in enumerate(clss):
        if cls_id != PERSON_CLASS_ID: continue
        x1,y1,x2,y2 = xyxy[i].tolist()
        x1 = max(0, min(w-1, x1)); y1 = max(0, min(h-1, y1))
        x2 = max(0, min(w-1, x2)); y2 = max(0, min(h-1, y2))
        if x2 > x1 and y2 > y1:
            dets.append((x1,y1,x2,y2))
    return dets

# ---------------------------------------------------------------------
# Reporter periodik (fungsi + thread)
# ---------------------------------------------------------------------
_report_lock = threading.Lock()
_report_window_start = time.time()
_report_in = 0
_report_out = 0
_report_inside = 0
_report_stop_evt = threading.Event()
_report_thread = None
_report_session = requests.Session()

def report_add_in(n=1):
    global _report_in
    with _report_lock: _report_in += n

def report_add_out(n=1):
    global _report_out
    with _report_lock: _report_out += n

def report_set_inside(n):
    global _report_inside
    with _report_lock: _report_inside = n

def _report_send(url: str, camera_id: int, payload: dict):
    headers = {"Content-Type": "application/json"}
    try:
        r = _report_session.post(url, headers=headers, json=payload, timeout=10)
        print(f"[REPORT] -> {url} {r.status_code} {r.text[:120]}")
    except Exception as e:
        print(f"[REPORT] error: {e}")

def _report_loop(url: str, interval: int, camera_id: int):
    global _report_window_start, _report_in, _report_out, _report_inside
    # boot ping
    _report_send(url, camera_id, {"camera_id": camera_id, "masuk":0, "keluar":0, "dalam":0})
    while not _report_stop_evt.is_set():
        time.sleep(1)
        if time.time() - _report_window_start >= interval:
            with _report_lock:
                payload = {
                    "camera_id": camera_id,
                    "masuk": _report_in,
                    "keluar": _report_out,
                    "dalam": _report_inside
                }
                _report_window_start = time.time()
                _report_in = 0; _report_out = 0
            _report_send(url, camera_id, payload)

def start_reporter(url: str, interval_sec: int, camera_id: int = 1):
    global _report_thread
    if _report_thread and _report_thread.is_alive(): return
    _report_stop_evt.clear()
    _report_thread = threading.Thread(target=_report_loop, args=(url, interval_sec, camera_id), daemon=True)
    _report_thread.start()
    print(f"[INFO] Reporter started url={url} interval={interval_sec}s cam={camera_id}")

def stop_reporter():
    _report_stop_evt.set()

# ---------------------------------------------------------------------
# WS Client (fungsi)
# ---------------------------------------------------------------------
_ws_loop: Optional[asyncio.AbstractEventLoop] = None
_ws_thread: Optional[threading.Thread] = None
_ws_queue: Optional[asyncio.Queue] = None
_ws_stop_evt = threading.Event()
_ws_connected_evt = threading.Event()
_ws_url = WS_URL

async def _ws_main():
    global _ws_queue
    _ws_queue = asyncio.Queue()
    while not _ws_stop_evt.is_set():
        try:
            async with websockets.connect(_ws_url, max_size=8*1024*1024, ping_interval=30, ping_timeout=30) as ws:
                print(f"[INFO] WS connected to {_ws_url}")
                _ws_connected_evt.set()
                async def sender():
                    while not _ws_stop_evt.is_set():
                        try:
                            msg = await asyncio.wait_for(_ws_queue.get(), timeout=1.0)
                            await ws.send(msg)
                        except asyncio.TimeoutError:
                            continue
                async def receiver():
                    while not _ws_stop_evt.is_set():
                        try:
                            _ = await asyncio.wait_for(ws.recv(), timeout=30)
                        except asyncio.TimeoutError:
                            continue
                send_task = asyncio.create_task(sender())
                recv_task = asyncio.create_task(receiver())
                done, pending = await asyncio.wait({send_task, recv_task}, return_when=asyncio.FIRST_EXCEPTION)
                for t in pending: t.cancel()
        except Exception as e:
            print(f"[WS] warn: {e}")
        finally:
            _ws_connected_evt.clear()
            await asyncio.sleep(2.0)

def ws_start(url: str):
    global _ws_loop, _ws_thread, _ws_url
    _ws_url = url
    if _ws_thread and _ws_thread.is_alive(): return
    def runner():
        global _ws_loop
        _ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_ws_loop)
        try:
            _ws_loop.run_until_complete(_ws_main())
        finally:
            _ws_loop.close()
    _ws_stop_evt.clear()
    _ws_thread = threading.Thread(target=runner, daemon=True)
    _ws_thread.start()
    print(f"[INFO] WS client starting -> {url}")

def ws_send_json(data: dict):
    if not _ws_loop or not _ws_loop.is_running() or not _ws_queue: return
    try:
        msg = json.dumps(data)
    except Exception:
        return
    _ws_loop.call_soon_threadsafe(lambda: _ws_queue.put_nowait(msg))

def ws_stop():
    _ws_stop_evt.set()

# ---------------------------------------------------------------------
# Config (fungsi) + shared state
# ---------------------------------------------------------------------
cfg_lock = threading.Lock()
shared_cfg = {"video_url": "", "polygon": None}
config_version = 0

def fetch_config():
    r = requests.get(CONFIG_URL, timeout=10)
    r.raise_for_status()
    cfg = r.json()
    if isinstance(cfg, list):
        if not cfg: raise ValueError("CONFIG_URL mengembalikan list kosong")
        cfg = cfg[0]
    if not isinstance(cfg, dict): raise ValueError("CONFIG_URL bukan object JSON")
    if "source_url" not in cfg or "polygon" not in cfg:
        raise ValueError("CONFIG_URL tidak memuat kunci 'source_url' dan/atau 'polygon'")
    return cfg["source_url"], normalize_polygon(cfg["polygon"])

def apply_new_config(new_cfg: dict, cap_ref: Dict):
    global config_version
    changed = False
    with cfg_lock:
        if "polygon" in new_cfg and new_cfg["polygon"] is not None:
            if isinstance(new_cfg["polygon"], np.ndarray):
                shared_cfg["polygon"] = new_cfg["polygon"].astype(np.int32)
            else:
                shared_cfg["polygon"] = np.array(new_cfg["polygon"], dtype=np.int32)
            changed = True
        if "video_url" in new_cfg and new_cfg["video_url"]:
            vurl = new_cfg["video_url"]
            if vurl != shared_cfg.get("video_url"):
                try:
                    new_cap = cv2.VideoCapture(vurl)
                    if not new_cap.isOpened():
                        print("[WARN] Stream baru gagal dibuka, abaikan")
                    else:
                        if cap_ref["cap"]: cap_ref["cap"].release()
                        cap_ref["cap"] = new_cap
                        shared_cfg["video_url"] = vurl
                        tracker_reset()
                        changed = True
                        print("[INFO] Stream diganti & tracker di-reset")
                except Exception as e:
                    print("[ERR] Ganti stream error:", e)
        if changed: config_version += 1

# ---------------------------------------------------------------------
# Main loop (fungsi)
# ---------------------------------------------------------------------
def main():
    stop_flag = {"v": False}
    def handle_sig(*_): stop_flag["v"] = True
    try:
        signal.signal(signal.SIGINT, handle_sig)
        signal.signal(signal.SIGTERM, handle_sig)
    except Exception:
        signal.signal(signal.SIGINT, handle_sig)

    # init detector
    init_detector(YOLO_MODEL, DEVICE, CONF_THR)

    # load config
    vurl, poly = fetch_config()
    if poly is None or len(poly) < 3:
        raise RuntimeError("Polygon dari CONFIG_URL tidak valid (None atau titik < 3)")

    cap_ref = {"cap": None}
    apply_new_config({"video_url": vurl, "polygon": poly.tolist()}, cap_ref)

    if not cap_ref["cap"]:
        raise RuntimeError("Gagal membuka video source saat start")

    # start ws + reporter
    ws_start(WS_URL)
    start_reporter(REPORT_URL, REPORT_INTERVAL, camera_id=1)

    last_ui_send = 0.0
    ui_interval = 1.0 / max(1e-3, UI_TARGET_FPS)
    next_status = 0.0
    fail_cnt = 0

    print("[INFO] Start processing...")
    prev_inside_state: Dict[int, bool] = {}

    while not stop_flag["v"]:
        ok, frame = cap_ref["cap"].read()
        if not ok:
            fail_cnt += 1
            if fail_cnt >= 50:
                print("[WARN] Stream putus, mencoba reconnect...")
                try:
                    with cfg_lock:
                        vurl = shared_cfg["video_url"]
                    new_cap = cv2.VideoCapture(vurl)
                    if new_cap.isOpened():
                        if cap_ref["cap"]: cap_ref["cap"].release()
                        cap_ref["cap"] = new_cap
                        fail_cnt = 0
                        print("[INFO] Reconnect berhasil")
                except Exception as e:
                    print("[ERR] Reconnect gagal:", e)
            time.sleep(0.1)
            continue
        else:
            fail_cnt = 0

        frame_resized = cv2.resize(frame, (OUT_W, OUT_H))

        with cfg_lock:
            polygon = shared_cfg["polygon"]
        if polygon is None or len(polygon) < 3:
            time.sleep(0.05)
            continue

        # deteksi
        detections = detect_person(frame_resized)
        # tracker
        tracks = tracker_update(detections, polygon)

        # hitung in/out
        in_events = 0; out_events = 0
        for tid, tr in tracks.items():
            curr_inside = tr.inside_poly
            was_inside = prev_inside_state.get(tid, curr_inside)
            if (not was_inside) and curr_inside: in_events += 1
            elif was_inside and (not curr_inside): out_events += 1
            prev_inside_state[tid] = curr_inside

        if in_events: report_add_in(in_events)
        if out_events: report_add_out(out_events)

        inside_now = sum(1 for tr in tracks.values() if tr.inside_poly)
        report_set_inside(inside_now)

        # overlay
        try:
            cv2.polylines(frame_resized, [polygon], isClosed=True, color=(0,255,0), thickness=2)
        except Exception:
            pass
        for tid, tr in tracks.items():
            x1,y1,x2,y2 = tr.bbox
            cv2.rectangle(frame_resized, (x1,y1), (x2,y2), (255,255,255), 2)
            cx, cy = centroid(tr.bbox)
            cv2.circle(frame_resized, (cx,cy), 3, (0,0,255), -1)
            label = f"ID {tid}{' IN' if tr.inside_poly else ''}"
            cv2.putText(frame_resized, label, (x1, max(15,y1-5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1, cv2.LINE_AA)

        # encode jpeg -> base64
        ok_jpg, buf = cv2.imencode(".jpg", frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if ok_jpg:
            b64 = base64.b64encode(buf.tobytes()).decode("ascii")
        else:
            b64 = None

        now = time.time()
        if b64 and (now - last_ui_send >= ui_interval):
            ws_send_json({
                "masuk": in_events,
                "keluar": out_events,
                "didalam": inside_now,
                "image": b64,
            })
            last_ui_send = now

        if now >= next_status:
            ws_send_json({
                "type": "status",
                "state": "running",
                "video_url": shared_cfg["video_url"],
                "inside": inside_now,
                "fps": round(1.0 / max(1e-3, ui_interval), 2),
                "config_version": config_version
            })
            next_status = now + 5.0

        time.sleep(0.05)

    print("[INFO] Stopping ...")
    stop_reporter()
    ws_stop()
    if cap_ref["cap"]:
        try: cap_ref["cap"].release()
        except: pass

if __name__ == "__main__":
    print("[CFG] CONFIG_URL =", CONFIG_URL)
    print("[CFG] REPORT_URL =", REPORT_URL)
    main()
