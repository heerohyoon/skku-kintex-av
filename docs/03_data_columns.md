# 수집 데이터 설계

원칙: **교수님 기본 항목은 바꾸지 않는다. 추가 항목은 "어떤 평가 기준을 증명하는가"를 이유로 단다.**
(조교님 안내: 기본 항목 변경 불가, 이유가 있는 추가는 가능)

## 1. 기본 항목 19개 (교수님 6장 2.4절, 변경 없음)

제공된 `collect_pomdp_data.py`가 POMDP transition 단위로 저장한다.

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
| `state` | Dictionary | SUMO 내부 상태: AV·모든 차량의 위치, 속도, 차선 (절대 정보) |
| `detected_vehicles` | List | 관측 시점에 감지된 주변 차량 |
| `event.collided` | Boolean | 충돌 여부 |
| `event.arrived` | Boolean | 목적지 도착 여부 |
| `event.lane_before` | Integer / String | 행동 전 AV 차선 |
| `event.lane_after` | Integer / String | 행동 후 AV 차선 |
| `next_observation` | Vector | 다음 시점 관측 |
| `next_state` | Dictionary | 다음 시점 SUMO 내부 상태 |

- 수집 코드는 `next_observation`, `next_state`를 JSONL에서 에피소드 마지막 스텝에만 저장하고, 읽을 때 복원한다 (공식 표 설명과 동일).
- 공식 표에는 observation이 19차원으로 적혀 있지만 현재 코드는 31차원이다. 어느 기준인지 교수님께 확인 필요.

## 2. 추가 항목: 평가 기준별

### 핵심 (중간발표에서 제안)

교수님 완주 기준과 평가 조건에서 바로 나온 항목들이다. 경로 관련 항목은 AV 관측에도 필요해서 어차피 계산해야 한다.

| 추가 항목 | 형태·단위 | 의미 | 증명하는 기준 (6장 위치) |
|---|---|---|---|
| `route.on_route` | Boolean | 지금 도로가 계획 경로 위인지 | "잘못된 Route로 빠지지 않는가" (2.2-2) |
| `route.dist_to_decision` | Float, m | 다음 합류·분기·신호까지 거리 | 구조 → 의사결정 연결 (1.3-4) |
| `route.decision_type` | String | 다음 결정 지점 종류: merge / diverge / signal | 상호작용 종류 기록 (동료평가) |
| `route.lane_ok` | Boolean | 지금 차선이 경로를 따라 계속 이어지는지 | 기한 있는 차선변경 판단 |
| `ego.stopped_time` | Float, 초 | 연속 정지 시간 | "비정상 정지·무한 대기" (2.2-2) |
| `traffic.n_nearby` | Integer, 대 | 관측 범위 50 m 안 일반 차량 수 | "평가 시 일반 차량이 일정 수 이상" (2.2-3) |

### 확장 (범위가 허용되면)

| 추가 항목 | 형태·단위 | 의미 | 증명하는 기준 |
|---|---|---|---|
| `interaction.leader_id`, `interaction.follower_id` | String | 같은 차선 앞·뒤 차량 ID | 끼어들기·양보를 데이터에서 찾을 수 있음 ("데이터에 잘 기록") |
| `safety.ttc` | Float, 초 | 앞차와 충돌까지 예상 시간 (가까워지지 않으면 큰 값) | 충돌 외 위험 순간 측정 ("안정적으로 해결") |
| `safety.headway` | Float, 초 | 앞차와의 시간 간격 | 위와 같음 |
| `tls.state`, `tls.dist_to_stopline` | String, m | 앞 신호 상태, 정지선까지 거리 | 신호 교차로 통과 (구간 4·1) |
| `state.ego_lat`, `state.ego_lon` | Float, 도 | AV 실제 위도·경도 | 절대 정보 강조, 구간 간 같은 좌표계 |

`ego_lat`·`ego_lon`은 쉽게 만들 수 있다. 도로 변환 때 좌표를 영역 중심으로 옮겼기 때문에 구간별 기준점만 알면 SUMO 좌표를 실제 위경도로 되돌릴 수 있다.

## 3. 에피소드 정보 (에피소드마다 한 줄)

스텝 데이터와 별도 파일. "Simulation 안정성"과 "수집 조건 제시"를 동시에 증명한다.

| 항목 | 의미 |
|---|---|
| `segment_id` | 구간 번호 |
| `seed` | 난수 시드 (재현용) |
| `traffic_level`, `vehs_per_hour` | 교통량 조건 |
| `hv_mix` | 일반 차량 4종 비율 (Krauss, IDM, EIDM, ACC) |
| `policy` | 수집에 쓴 정책 (학습된 PPO, 무작위성 섞은 PPO, 규칙 기반 등) |
| `outcome` | arrived / collided / wrong_route / stuck / timeout |
| `n_teleports` | 에피소드 중 순간이동 수 |
| `length_steps`, `duration_s` | 길이, 소요 시간 |

## 4. 저장 구조와 규모

교수님 예시 데이터셋(Multi-Square)처럼 **환경별 폴더 → 조건별 폴더**로 나누고, 데이터셋 설명에 프로젝트 페이지·코드 링크와 재현 방법을 단다.

```
dataset/
├── seg2_branch/
│   ├── ppo/            ← 학습된 정책
│   ├── ppo_stochastic/ ← 무작위성 섞은 정책
│   └── rule_based/     ← 규칙 기반 운전
│       ├── *.npz       (학습용 배열: 기본 NPZ 항목 + 추가 항목)
│       ├── *.jsonl.gz  (전체 상태)
│       └── episodes.csv
└── seg4_arrival/
    └── ...
```

| 항목 | 계획 |
|---|---|
| 규모 | 1,000만 transition 이상 (단위는 교수님께 확인) |
| 조건 | 구간 × 교통량(한산·보통·혼잡) × 정책(3종) |
| 예상 용량 | JSONL.GZ 약 2.8 KB/transition → 약 28 GB, NPZ 약 62 B/transition → 약 0.6 GB (3차 과제 측정 기준) |

## 5. 범위 제한 대비

교수님이 중간발표 이후 컬럼 범위를 제한한다고 했다. 핵심 6개는 완주·평가 조건에서 바로 나온 항목이라
유지될 가능성이 높고, 확장 항목은 제한 범위에 맞춰 넣거나 뺀다.
