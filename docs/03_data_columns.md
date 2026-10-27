# 수집 데이터 컬럼

## 기본 항목 (교수님 공식 표, 반드시 포함)

교수님 6장 문서 2.4절에 올라온 표. 제공된 `collect_pomdp_data.py`가 POMDP transition 단위로 저장한다.

| 항목 | 형태 | 의미 |
|---|---|---|
| `episode` | Integer | Episode 번호 |
| `t` | Integer | Episode 내부 timestep (0.5초) |
| `observation` | Vector | 시점 t에서 AV가 받는 부분 관측 |
| `action_raw` | Vector (2) | Policy 원본 출력 `[가감속, 차선변경]` |
| `action.accel_raw` | Float | 환경에 전달된 가감속 값 |
| `action.lane_change_raw` | Float | 환경에 전달된 차선변경 raw 값 |
| `action.lane_change` | Integer | 실제 명령으로 바뀐 차선변경 `{-1, 0, +1}` |
| `action.lane_change_applied` | Boolean | 차선변경이 실제로 적용됐는지 |
| `reward` | Float | 보상 |
| `terminated` | Boolean | 충돌·도착으로 인한 종료 |
| `truncated` | Boolean | 시간 제한 종료 |
| `state` | Dictionary | SUMO 내부 상태 (AV·모든 차량의 위치, 속도, 차선 등 절대 정보) |
| `detected_vehicles` | List | 관측 시점에 감지된 주변 차량 |
| `event.collided` | Boolean | 충돌 여부 |
| `event.arrived` | Boolean | 목적지 도착 여부 |
| `event.lane_before` / `event.lane_after` | Integer / String | 행동 전후 AV 차선 |
| `next_observation` | Vector | 다음 시점 관측 |
| `next_state` | Dictionary | 다음 시점 SUMO 내부 상태 |

> 공식 표에는 observation이 19차원으로 적혀 있지만 현재 코드는 31차원이다 (주변 5개 차선 정보).
> 어느 기준인지 교수님께 확인 필요.

`state`의 주요 내용 (현재 코드 기준): `ego_x`, `ego_y`(m), `ego_speed`(m/s), `ego_lane`, `ego_lane_id`,
`ego_road_id`, `ego_lane_pos`(m), `vehicles`(모든 차량의 id·위치·속도·차선)

## 추가 제안 (우리 도로에 필요한 항목)

교수님 문서: "각 팀의 도로 구조와 자율주행 문제에 필요한 추가 항목은 자유롭게 확장 가능".
단, 중간발표 이후 컬럼 범위를 제한할 예정이라고 했으므로 확정은 그 뒤에 한다.

| 항목 | 단위 | 의미 | 필요한 이유 |
|---|---|---|---|
| `segment_id` | 1~4 | 구간 번호 | 구간별 성능 비교 |
| `route_progress` | m | 경로상 진행 거리 | 완주율·정체 위치 분석 |
| `dist_to_exit` | m | 다음 분기·출구까지 거리 | 출구 차선 변경 판단의 핵심 |
| `target_lane_offset` | 차선 수 | 지금 차선과 출구 차선의 차이 | 잘못된 경로 진입 방지 |
| `tls_state` | 적·황·녹 | 앞 신호 상태 | 신호 교차로 (구간 1·4) |
| `dist_to_stopline` | m | 정지선까지 거리 | 신호 대기열 뒤 감속 |

## 저장과 규모

- **형식:** NPZ(학습용 배열) + JSONL.GZ(전체 상태) → Hugging Face 공개
- **목표:** 1,000만 개 이상 (단위 확인 필요), 구간별 병렬 수집
- **용량 추정 (3차 과제 측정 기준):** JSONL.GZ 약 2.8 KB/transition → 1,000만 개 약 28 GB,
  NPZ 약 62 B/transition → 약 0.6 GB
