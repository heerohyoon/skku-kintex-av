"""성대 자연과학캠퍼스 → 킨텍스 경로 지도 + 구간별 확대 지도 생성 (docs/images/).

사용법: python3 tools/make_maps.py   (필요: matplotlib, pillow)

배경: OpenStreetMap 표준 타일 (© OpenStreetMap contributors)
경로: OSRM 공개 서버가 계산한 자동차 경로 (route_full.json)
"""
import io
import json
import math
import os
import time
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # 저장소 최상위
OUT = os.path.join(ROOT, "docs", "images")
TILE_DIR = os.path.join(ROOT, ".cache", "tiles")              # 지도 타일 캐시 (git 제외)
os.makedirs(TILE_DIR, exist_ok=True)

font_manager.fontManager.addfont("/System/Library/Fonts/AppleSDGothicNeo.ttc")
plt.rcParams["font.family"] = "Apple SD Gothic Neo"

GREEN = "#0B6E4F"      # 고속도로 표지판 녹색
AMBER = "#F2A900"      # 차선 도색 황색
INK = "#1F2328"

# ── 경로 좌표와 누적 거리 ──
route = json.load(open(os.path.join(ROOT, "data", "route", "route_full.json")))["routes"][0]
coords = route["geometry"]["coordinates"]            # [lon, lat]


def hav(a, b):
    R = 6371000.0
    la1, la2 = math.radians(a[1]), math.radians(b[1])
    dla, dlo = la2 - la1, math.radians(b[0] - a[0])
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


cum = [0.0]
for i in range(1, len(coords)):
    cum.append(cum[-1] + hav(coords[i - 1], coords[i]))
TOTAL_KM = cum[-1] / 1000

# 구간 정의 (경로 시작점 기준 km) — OSRM 단계 정보에서 고른 지점
SEGMENTS = [
    (1, "출발", 0.0, 6.2),     # 캠퍼스 → 수인로 → 수원문산고속도로 진입 합류
    (2, "분기", 23.8, 28.6),   # 고속도로 → 서부간선도로 합류 → 지상/지하 분기
    (3, "한강", 37.0, 44.5),   # 서부간선로 → 한강 횡단 → 강변북로 → 자유로
    (4, "도착", 55.8, 59.4),   # 자유로 → 킨텍스 진출 → 킨텍스로 → 도착
]


def seg_coords(a_km, b_km):
    return [c for c, d in zip(coords, cum) if a_km * 1000 <= d <= b_km * 1000]


# ── 웹 메르카토르 / 타일 ──
def merc(lon, lat):
    x = math.radians(lon) * 6378137.0
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137.0
    return x, y


def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile_bounds(tx, ty, z):
    n = 2 ** z
    lon0 = tx / n * 360 - 180
    lon1 = (tx + 1) / n * 360 - 180
    lat0 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + 1) / n))))
    return lon0, lat1, lon1, lat0          # west, south, east, north


def get_tile(z, x, y):
    path = os.path.join(TILE_DIR, f"{z}_{x}_{y}.png")
    if not os.path.exists(path):
        req = urllib.request.Request(
            f"https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            headers={"User-Agent": "skku-sumo-class-project/1.0 (student slide figure)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            open(path, "wb").write(r.read())
        time.sleep(0.25)
    return Image.open(path).convert("RGB")


def basemap(west, south, east, north, z):
    x0, y0 = tile_xy(west, north, z)
    x1, y1 = tile_xy(east, south, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    W, H = (tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256
    canvas = Image.new("RGB", (W, H))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            canvas.paste(get_tile(z, tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
    w_, s_, _, n_ = tile_bounds(tx0, ty0, z)
    _, s2, e2, _ = tile_bounds(tx1, ty1, z)
    left, top = merc(w_, n_)
    right, bottom = merc(e2, s2)
    return canvas, (left, right, bottom, top)


def draw(ax, pts, **kw):
    xs, ys = zip(*[merc(lon, lat) for lon, lat in pts])
    ax.plot(xs, ys, solid_capstyle="round", solid_joinstyle="round", **kw)


def frame(ax, west, south, east, north):
    l, b = merc(west, south)
    r, t = merc(east, north)
    ax.set_xlim(l, r)
    ax.set_ylim(b, t)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def badge(ax, lon, lat, text, size=13, r=None):
    x, y = merc(lon, lat)
    ax.annotate(text, (x, y), ha="center", va="center", fontsize=size,
                fontweight="bold", color=INK, zorder=10,
                bbox=dict(boxstyle="circle,pad=0.35", fc=AMBER, ec="white", lw=2))


def label(ax, lon, lat, text, dx=0, dy=0, ha="left", size=11):
    x, y = merc(lon, lat)
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points",
                ha=ha, va="center", fontsize=size, fontweight="bold", color=INK, zorder=11,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="none", alpha=0.92))


def dot(ax, lon, lat, color):
    x, y = merc(lon, lat)
    ax.plot([x], [y], "o", ms=11, mfc=color, mec="white", mew=2.5, zorder=9)


# ── 1) 전체 경로 지도 ──
def overview():
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    pad_lon, pad_lat = 0.035, 0.022
    west, east = min(lons) - pad_lon, max(lons) + pad_lon
    south, north = min(lats) - pad_lat, max(lats) + pad_lat
    img, ext = basemap(west, south, east, north, 11)
    l, b = merc(west, south); r, t_ = merc(east, north)
    fig = plt.figure(figsize=(6.6 * (r - l) / (t_ - b), 6.6), dpi=220)   # 지도 비율 그대로
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=ext, alpha=0.55, zorder=0)
    draw(ax, coords, color="white", lw=7.5, zorder=2)
    draw(ax, coords, color=GREEN, lw=4.2, zorder=3)
    for n, _, a, b in SEGMENTS:
        pts = seg_coords(a, b)
        draw(ax, pts, color="white", lw=10, zorder=4)
        draw(ax, pts, color=AMBER, lw=6.5, zorder=5)
        mid = pts[len(pts) // 2]
        off = {1: (-0.020, -0.013), 2: (0.03, -0.004), 3: (0.03, 0.006), 4: (0.03, 0.0)}[n]
        badge(ax, mid[0] + off[0], mid[1] + off[1], str(n))
    dot(ax, *coords[0], GREEN)
    dot(ax, *coords[-1], "#C8102E")
    label(ax, *coords[0], "성균관대 자연과학캠퍼스", dx=-14, dy=22, ha="right")
    label(ax, *coords[-1], "킨텍스 (KINTEX)", dx=12, dy=8)
    frame(ax, west, south, east, north)
    x, y = merc(west, south)
    ax.annotate("© OpenStreetMap contributors · 경로: OSRM", (x, y), xytext=(6, 6),
                textcoords="offset points", fontsize=6.5, color="#444")
    fig.savefig(os.path.join(OUT, "route_overview.png"))
    plt.close(fig)


# ── 2) 구간별 확대 지도 ──
def zoomed(n, name, a, b):
    pts = seg_coords(a, b)
    lons = [c[0] for c in pts]
    lats = [c[1] for c in pts]
    cx, cy = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
    # 가로 4 : 세로 3 비율 박스에 맞춘다 (위도 1° ≈ 경도 1/cos(lat)°)
    k = 1 / math.cos(math.radians(cy))
    half_h = max((max(lats) - min(lats)) / 2, (max(lons) - min(lons)) / 2 / k * 0.75) * 1.25
    half_w = half_h / 0.75 * k
    west, east, south, north = cx - half_w, cx + half_w, cy - half_h, cy + half_h
    span_km = (east - west) * 111 / k
    z = 15 if span_km < 3 else 14 if span_km < 6 else 13
    img, ext = basemap(west, south, east, north, z)
    fig = plt.figure(figsize=(4.0, 3.0), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=ext, alpha=0.75, zorder=0)
    draw(ax, pts, color="white", lw=8, zorder=2)
    draw(ax, pts, color=AMBER, lw=4.5, zorder=3)
    dot(ax, *pts[0], GREEN)
    dot(ax, *pts[-1], "#C8102E")
    frame(ax, west, south, east, north)
    x, y = merc(west, south)
    ax.annotate("© OpenStreetMap contributors", (x, y), xytext=(4, 4),
                textcoords="offset points", fontsize=5.5, color="#444")
    fig.savefig(os.path.join(OUT, f"seg{n}.png"))
    plt.close(fig)
    return span_km, z


if __name__ == "__main__":
    print(f"경로 총 {TOTAL_KM:.1f} km, 좌표 {len(coords)}개")
    overview()
    for n, name, a, b in SEGMENTS:
        span, z = zoomed(n, name, a, b)
        print(f"구간 {n} {name}: {b - a:.1f} km, 지도 폭 {span:.1f} km, zoom {z}")
    print("타일 수:", len(os.listdir(TILE_DIR)))
