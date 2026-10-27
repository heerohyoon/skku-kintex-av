# 실제 지도 → SUMO 도로 변환 방법

```
① OpenStreetMap 원본 받기 → ② 영역 자르기·좌표 보정 → ③ netconvert 변환 → ④ 로드뷰 보정 → ⑤ 검증
```

## 교수님 기준과의 관계

교수님 5장 문서(5.3절)는 도로 구현 방법으로 두 가지를 허용한다.

| 방법 | 내용 |
|---|---|
| A | `road_builder.py`를 확장해 파이썬 설정값으로 도로 생성 |
| **B** | **netedit 또는 외부 도로 파일 사용.** 완성한 `.net.xml`, `.rou.xml`, `.sumocfg`를 저장소에 포함 |

우리는 **방법 B**다. 지도 데이터를 변환한 도로망이 "외부 도로 파일"이고, 보정은 netedit으로 한다.
교수님 `road_builder.py`도 마지막에 netconvert로 도로를 만든다 — 우리는 입력이 손으로 쓴 좌표가 아니라
지도 데이터일 뿐이다. 조건인 **"누구나 저장소를 받아 같은 환경을 재현"**은 구간별 `build.sh`와
보정 완료 도로 파일을 저장소에 넣어 맞춘다.

## ① 원본: OpenStreetMap

전 세계 사용자가 함께 만드는 공개 지도. 출처 표기(© OpenStreetMap contributors) 조건으로 자유롭게 사용 가능.

```bash
curl -A "skku-kintex-av" -o seg2.osm.xml \
  "https://api.openstreetmap.org/api/0.6/map?bbox=서,남,동,북"
```

| 요소 | 의미 | 예 |
|---|---|---|
| 노드 | 위도·경도가 있는 점 | 교차점, 도로 꺾이는 점 |
| 웨이 | 노드를 이은 선 | 도로, 건물, 보도 |
| 태그 | 웨이의 속성 | `highway=trunk`, `lanes=2`, `maxspeed=80`, `layer=-4`(지하) |

**SUMO 도로의 차선 수·제한속도는 태그에서 나온다.** 태그가 없으면 도로 등급별 기본값을 쓴다
(간선 2차선, 램프 1차선 등) → 이 부분을 ④에서 보정한다.

## ② 영역 자르기·좌표 보정 (`tools/crop_osm.py`)

1. **큰길만 남김:** 3차로급(tertiary) 이상 도로와 램프. 건물·보도·골목 제외
2. **영역 밖 잘라냄:** OSM 서버는 영역에 걸친 긴 도로를 통째로 준다 (자르지 않으면 18 km × 14 km가 됨)
3. **좌표를 영역 중심으로 이동:** 아래 주의 참고

> **주의: 맥 소스 빌드 SUMO의 좌표 문제**
> 설치 가이드대로 빌드한 맥 SUMO에는 좌표 변환 라이브러리(PROJ)가 빠져 있어 `--simple-projection`을 써야 한다.
> 이 방식은 절대 경도(약 127°)로 계산해서, 남북 5 km 영역이 **6.6 km 비틀린다.**
> 영역 중심을 원점으로 옮기고 경도에 cos(위도)를 곱해 두면 오차가 몇 m 이내로 줄어든다.
> 윈도우 공식 설치본은 PROJ가 들어 있어 이 문제가 없다.

## ③ 변환: netconvert

```bash
netconvert --osm-files seg2.crop.osm.xml --simple-projection \
  --geometry.remove --ramps.guess --junctions.join \
  --tls.guess-signals --tls.discard-simple --tls.join --edges.join \
  --output.street-names true --no-turnarounds.except-deadend true \
  -o seg2.net.xml
```

| 옵션 | 하는 일 |
|---|---|
| `--ramps.guess` | 고속도로 진출입로를 찾아 가속·감속 차선을 붙임 |
| `--junctions.join` | 가까이 붙은 점들을 교차로 하나로 합침 |
| `--tls.guess-signals` 외 | 지도의 신호등 표시를 교차로 신호로 만듦 |
| `--edges.join`, `--geometry.remove` | 잘게 쪼개진 도로를 이어 단순화 |
| `--output.street-names` | 도로 이름 유지 |

SUMO 도로 ID가 OSM 웨이 번호 그대로라서(`975888370#1`), 어느 도로가 지도의 어떤 선에서 왔는지 되짚을 수 있다.

## ④ 로드뷰 보정 (netedit)

지도를 그대로 쓰면 차선 수가 틀리고 신호가 빠져 정체가 생긴다. 보정 없이는 평가 1순위
"실제 도로 특징 반영"과 "비정상 정체 없음"을 못 맞춘다.

확인 대상 (구간 2 예: `docs/images/seg2_check_map.png`)

1. 차선 수가 지도에 없는 도로 (빨간색)
2. 지도 값이 의심스러운 도로 (예: 서부간선도로 일부가 1차선)
3. 정체·순간이동이 생기는 교차로 (신호 누락 의심)

**보정 기록은 반드시 남긴다.** 최종발표 "발견한 문제와 해결 과정"의 재료가 된다.

| 구간 | 위치 (도로 ID / 이름) | 지도 값 | 로드뷰 확인 | 수정 내용 | 수정 후 결과 |
|---|---|---|---|---|---|
| 2 | 금하로 교차로 | 신호 없음 | | | |

## ⑤ 검증

1. **경로 연결:** 실제 경로(OSRM)를 SUMO 도로 위에 겹쳐 출발 → 도착이 이어지는지
2. **차량 주행:** 일반 차량 + 경로 차량을 넣고 순간이동·정체가 없는지 (`sumo ... --duration-log.statistics true`)
3. **보정 전후 비교:** 같은 차량으로 정체·순간이동 수가 줄었는지
