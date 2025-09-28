# ================== CONFIG ==================
SOURCE = 'https://cctvjss.jogjakota.go.id/malioboro/Malioboro_10_Kepatihan.stream/playlist.m3u8'

MODEL_PATH = 'yolov8s_openvino_model'

CONF = 0.35
IOU = 0.5
DEVICE = 'cpu'            # OpenVINO di CPU
IMGSZ_INFER = 320         # lebih kecil dari 640 untuk speed
PROCESS_EVERY_N = 2       # infer tiap N frame

# Optional capture resize
CAP_SET_W = 640
CAP_SET_H = 360
CAP_BUFFERSIZE = 1

# Polygon ROI
POLYGON = {
    'name': 'Fast ROI',
    'ref_w': 960,
    'ref_h': 540,
    'points': [
        {'x': 120, 'y': 80},
        {'x': 840, 'y': 90},
        {'x': 880, 'y': 420},
        {'x': 100, 'y': 420}
    ]
}

# Drawing and output
SHOW_WINDOW = True
SHOW_IDS = True
SHOW_CONF = False
OUTPUT_JSONL = 'events_fast.jsonl'

# Simple tracker params
ASSIGN_MAX_DIST = 60
TRACK_MAX_AGE = 20
# ===========================================

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from collections import deque

import cv2
import numpy as np
from ultralytics import YOLO   # Ultralytics akan mendeteksi model OpenVINO dari path .xml / folder


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def scale_polygon(points, src_w, src_h, ref_w=None, ref_h=None):
    if not points:
        return []
    if not ref_w or not ref_h:
        ref_w, ref_h = src_w, src_h
    sx = src_w / float(ref_w)
    sy = src_h / float(ref_h)
    out = []
    for p in points:
        x = p['x'] if isinstance(p, dict) else p[0]
        y = p['y'] if isinstance(p, dict) else p[1]
        out.append((int(round(x * sx)), int(round(y * sy))))
    return out


def point_in_polygon(x, y, poly):
    inside = False
    n = len(poly)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def draw_polygon(disp, poly, title=None):
    if not poly or len(poly) < 3:
        return
    overlay = disp.copy()
    pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(overlay, [pts], color=(50, 150, 255))
    cv2.addWeighted(overlay, 0.12, disp, 0.88, 0, disp)
    cv2.polylines(disp, [pts], True, (50, 150, 255), 2)
    if title:
        cv2.putText(disp, title, (pts[0,0,0]+6, pts[0,0,1]+18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50,150,255), 2, cv2.LINE_AA)


def draw_boxes(disp, xyxy, ids, confs, clss, names, inside_flags):
    h, w = disp.shape[:2]
    thick = max(1, int(round((h + w) / 600)))
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.4, (h + w) / 1600.0)
    for i, (x1, y1, x2, y2) in enumerate(xyxy):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cx, cy = int((x1 + x2) * 0.5), int((y1 + y2) * 0.5)
        inside = bool(inside_flags[i]) if inside_flags is not None else False

        color = (0, 200, 0) if inside else (80, 200, 80)
        if ids is not None and i < len(ids) and ids[i] is not None:
            color = (0, 180, 255) if not inside else (0, 220, 180)

        cv2.rectangle(disp, (x1, y1), (x2, y2), color, thick)
        cv2.circle(disp, (cx, cy), max(2, thick + 1), (0, 255, 0) if inside else (0, 0, 255), -1)

        label_cls = int(clss[i]) if clss is not None else -1
        txt = names.get(label_cls, str(label_cls)) if isinstance(names, dict) else str(label_cls)
        if SHOW_CONF and confs is not None and i < len(confs):
            txt += f' {float(confs[i]):.2f}'
        if SHOW_IDS and ids is not None and i < len(ids) and ids[i] is not None:
            txt += f' id:{int(ids[i])}'
        (tw, th), _ = cv2.getTextSize(txt, font, font_scale, thick)
        y_text = max(th + 2, y1 - 4)
        cv2.rectangle(disp, (x1, y_text - th - 4), (x1 + tw + 4, y_text + 2), color, -1)
        cv2.putText(disp, txt, (x1 + 2, y_text), font, font_scale, (0, 0, 0), 1, cv2.LINE_AA)


# ---------- Lightweight centroid tracker -----------
class LightTracker:
    def __init__(self, max_dist=60, max_age=20):
        self.max_dist = max_dist
        self.max_age = max_age
        self.next_id = 1
        self.tracks = {}  # id -> dict(cx, cy, age, inside)

    def update(self, det_centroids, inside_flags):
        assigned = {}
        used_ids = set()

        # try assign each detection to nearest existing track
        for i, (cx, cy) in enumerate(det_centroids):
            best_id, best_d = None, 1e9
            for tid, t in self.tracks.items():
                if tid in used_ids:  # each track used once
                    continue
                d = (t['cx'] - cx)**2 + (t['cy'] - cy)**2
                if d < best_d:
                    best_d = d
                    best_id = tid
            if best_id is not None and best_d <= (self.max_dist**2):
                assigned[i] = best_id
                used_ids.add(best_id)
            else:
                # create new track
                tid = self.next_id; self.next_id += 1
                self.tracks[tid] = {'cx': cx, 'cy': cy, 'age': 0, 'inside': bool(inside_flags[i])}
                assigned[i] = tid
                used_ids.add(tid)

        # update assigned tracks & mark unassigned as aged
        current_ids = set()
        for i, tid in assigned.items():
            cx, cy = det_centroids[i]
            self.tracks[tid]['cx'] = cx
            self.tracks[tid]['cy'] = cy
            self.tracks[tid]['inside'] = bool(inside_flags[i])
            self.tracks[tid]['age'] = 0
            current_ids.add(tid)

        for tid in list(self.tracks.keys()):
            if tid not in current_ids:
                self.tracks[tid]['age'] += 1
                if self.tracks[tid]['age'] > self.max_age:
                    del self.tracks[tid]

        # build id list in same order as detections
        id_list = [assigned.get(i) for i in range(len(det_centroids))]
        return id_list

    def ids_inside(self):
        return [tid for tid, t in self.tracks.items() if t['inside']]


def main():
    # === LOAD MODEL OPENVINO ===
    # Path .xml / folder OpenVINO akan otomatis dipakai backend OpenVINO oleh Ultralytics
    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(SOURCE)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, CAP_BUFFERSIZE)
        if isinstance(SOURCE, int):
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_SET_W)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_SET_H)
    except Exception:
        pass

    if not cap.isOpened():
        raise RuntimeError('Failed to open SOURCE')

    # Polygon scaled to inference/display resolution
    poly = None

    # Tracker & counters
    tracker = LightTracker(max_dist=ASSIGN_MAX_DIST, max_age=TRACK_MAX_AGE)
    last_inside_set = set()
    total_enters = 0
    total_exits = 0

    # Output jsonl
    jf = open(OUTPUT_JSONL, 'w', encoding='utf-8')

    if SHOW_WINDOW:
        cv2.namedWindow('FastPeopleCounting', cv2.WINDOW_NORMAL)

    frame_idx = 0
    t_prev = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            # Resize frame for inference/display to reduce compute
            h0, w0 = frame.shape[:2]
            scale = IMGSZ_INFER / float(max(h0, w0))
            if scale < 1.0:
                new_w = int(w0 * scale)
                new_h = int(h0 * scale)
                disp = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                disp = frame.copy()
                new_h, new_w = disp.shape[:2]

            # Scale polygon once
            if poly is None:
                pts = POLYGON.get('points') or []
                poly = scale_polygon(pts, new_w, new_h, POLYGON.get('ref_w'), POLYGON.get('ref_h'))

            # Run inference on selected frames only
            do_infer = (frame_idx % max(1, PROCESS_EVERY_N) == 0)

            if do_infer:
                # NOTE: OpenVINO backend akan jalan otomatis, cukup set device='cpu'
                res = model.predict(
                    disp,
                    classes=[0],            # 0 = person (COCO)
                    conf=CONF,
                    iou=IOU,
                    imgsz=max(new_w, new_h),
                    device=DEVICE,
                    verbose=False
                )[0]

                if res.boxes is not None and len(res.boxes) > 0:
                    xyxy = res.boxes.xyxy.cpu().numpy().astype(int)
                    conf = (res.boxes.conf.cpu().numpy() if res.boxes.conf is not None else None)
                    cls = (res.boxes.cls.cpu().numpy() if res.boxes.cls is not None else None)

                    inside_flags = []
                    centroids = []
                    for (x1, y1, x2, y2) in xyxy:
                        cx, cy = int((x1 + x2) * 0.5), int((y1 + y2) * 0.5)
                        centroids.append((cx, cy))
                        inside_flags.append(point_in_polygon(cx, cy, poly) if poly else False)

                    # Update tracker & transitions
                    ids = tracker.update(centroids, inside_flags)
                    inside_set = set([tid for i, tid in enumerate(ids) if tid is not None and inside_flags[i]])
                    enter_ids = sorted(list(inside_set - last_inside_set))
                    exit_ids = sorted(list(last_inside_set - inside_set))
                    if enter_ids:
                        total_enters += len(enter_ids)
                    if exit_ids:
                        total_exits += len(exit_ids)
                    last_inside_set = inside_set

                    # Draw
                    draw_polygon(disp, poly, POLYGON.get('name'))
                    draw_boxes(disp, xyxy, ids, conf, cls, res.names, inside_flags)

                    # Output JSON
                    payload = {
                        'ts': now_iso(),
                        'frame': frame_idx,
                        'inside_ids': sorted(list(inside_set)),
                        'inside_count': int(len(inside_set)),
                        'enter_ids': enter_ids,
                        'exit_ids': exit_ids
                    }
                else:
                    # No detections
                    draw_polygon(disp, poly, POLYGON.get('name'))
                    payload = {
                        'ts': now_iso(),
                        'frame': frame_idx,
                        'inside_ids': [],
                        'inside_count': 0,
                        'enter_ids': [],
                        'exit_ids': []
                    }
            else:
                # skipped frame
                draw_polygon(disp, poly, POLYGON.get('name'))
                payload = {
                    'ts': now_iso(),
                    'frame': frame_idx,
                    'inside_ids': sorted(list(last_inside_set)),
                    'inside_count': int(len(last_inside_set)),
                    'enter_ids': [],
                    'exit_ids': []
                }

            # print & write
            print(json.dumps(payload, ensure_ascii=False), flush=True)
            jf.write(json.dumps(payload, ensure_ascii=False) + '\n'); jf.flush()

            # FPS
            t_now = time.time()
            dt = t_now - t_prev
            t_prev = t_now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps > 0 else (1.0 / dt)
            cv2.putText(disp, f'FPS:{fps:.1f}  In:{len(last_inside_set)}  Enter:{total_enters} Exit:{total_exits}',
                        (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (10, 10, 240), 2, cv2.LINE_AA)

            if SHOW_WINDOW:
                cv2.imshow('FastPeopleCounting', disp)
                if (cv2.waitKey(1) & 0xFF) == ord('q'):
                    break

    finally:
        try:
            jf.close()
        except Exception:
            pass
        try:
            cap.release()
        except Exception:
            pass
        if SHOW_WINDOW:
            cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
