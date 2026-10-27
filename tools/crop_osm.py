"""OSM XML을 bbox 안쪽만 남도록 자른다. 도로(way)는 bbox 안의 연속 구간으로 쪼갠다."""
import sys, xml.etree.ElementTree as ET
src, dst, w, s, e, n = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
KEEP = ("motorway", "trunk", "primary", "secondary", "tertiary")   # *_link 포함
root = ET.parse(src).getroot()
inside = {}
for nd in root.iter("node"):
    lon, lat = float(nd.get("lon")), float(nd.get("lat"))
    inside[nd.get("id")] = (w <= lon <= e and s <= lat <= n)
out = ET.Element("osm", version="0.6", generator="crop")
ways, used, new_id = [], set(), 10**12
for wy in root.iter("way"):
    tags = [t for t in wy.iter("tag")]
    hw = next((t.get("v") for t in tags if t.get("k") == "highway"), None)
    if not hw or not hw.startswith(KEEP):
        continue
    refs = [nd.get("ref") for nd in wy.iter("nd")]
    runs, cur = [], []
    for r in refs:
        if inside.get(r):
            cur.append(r)
        else:
            if len(cur) >= 2: runs.append(cur)
            cur = []
    if len(cur) >= 2: runs.append(cur)
    for k, run in enumerate(runs):
        nw = ET.Element("way", id=wy.get("id") if k == 0 else str(new_id + k), version="1")
        new_id += 100
        for r in run:
            ET.SubElement(nw, "nd", ref=r); used.add(r)
        for t in tags:
            nw.append(t)
        ways.append(nw)
# ── 좌표 중심 이동 ──
# SUMO의 --simple-projection은 x = 경도 × cos(위도) 를 "절대 경도"(약 127°)로 계산해서
# 위도가 조금만 달라져도 x가 크게 밀린다 (남북 4.9 km에서 6.6 km 기울어짐).
# 영역 중심을 (0, 0)으로 옮기고 경도에 cos(중심 위도)를 미리 곱해 두면
# 간이 변환 결과가 거의 정확한 지역 평면 좌표(m)가 된다.
import math
lon0, lat0 = (w + e) / 2, (s + n) / 2
k = math.cos(math.radians(lat0))
for nd in root.iter("node"):
    if nd.get("id") in used:
        nd.set("lon", f"{(float(nd.get('lon')) - lon0) * k:.8f}")
        nd.set("lat", f"{float(nd.get('lat')) - lat0:.8f}")
        out.append(nd)
open(dst + ".origin", "w").write(f"{lon0} {lat0}\n")
for wy in ways:
    out.append(wy)
ET.ElementTree(out).write(dst, encoding="utf-8", xml_declaration=True)
print(f"남긴 도로 {len(ways)}개, 노드 {len(used)}개")
