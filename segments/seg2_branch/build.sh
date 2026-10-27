#!/usr/bin/env bash
# 구간 2 (수원문산고속도로 진출 → 서부간선도로 합류 → 서부간선지하도로 분기)
# OpenStreetMap 원본 → 영역 자르기·좌표 보정 → netconvert → 일반 차량 생성
#
# 사용법:  cd segments/seg2_branch && bash build.sh
# 필요:    SUMO (netconvert, sumo), python3, curl, 환경변수 SUMO_HOME
set -euo pipefail
cd "$(dirname "$0")"

BBOX_W=126.87952; BBOX_S=37.42892; BBOX_E=126.90164; BBOX_N=37.47291

# 1) OpenStreetMap 원본 받기 (이미 있으면 건너뜀)
if [ ! -s seg2.osm.xml ]; then
  curl -sS -A "skku-kintex-av (course project)" -o seg2.osm.xml \
    "https://api.openstreetmap.org/api/0.6/map?bbox=${BBOX_W},${BBOX_S},${BBOX_E},${BBOX_N}"
fi

# 2) 영역 안쪽만, 큰길(3차로급 이상 + 램프)만 남기고 좌표를 영역 중심으로 이동
python3 ../../tools/crop_osm.py seg2.osm.xml seg2.crop.osm.xml "$BBOX_W" "$BBOX_S" "$BBOX_E" "$BBOX_N"

# 3) SUMO 도로망으로 변환
netconvert --osm-files seg2.crop.osm.xml --simple-projection \
  --geometry.remove --ramps.guess --junctions.join \
  --tls.guess-signals --tls.discard-simple --tls.join --edges.join \
  --output.street-names true --no-turnarounds.except-deadend true \
  --no-warnings true \
  -o seg2.net.xml

# 4) 시험용 일반 차량 (무작위, 실제 교통량 아님) — 15분 동안 1초에 1대
python3 "$SUMO_HOME/tools/randomTrips.py" -n seg2.net.xml -e 900 -p 1.0 \
  --fringe-factor 10 --min-distance 800 --validate --seed 1 \
  -o bg.trips.xml -r bg.rou.xml >/dev/null

echo "완료: seg2.net.xml (도로망), bg.rou.xml (일반 차량), route.rou.xml (경로 차량)"
echo "확인: sumo-gui -n seg2.net.xml -r bg.rou.xml,route.rou.xml --step-length 0.5"
