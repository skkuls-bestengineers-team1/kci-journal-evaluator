# KCI 내용평가용 합성 데이터 설계

기준 원문: `LangGraph 기반 CrewAI 다중 에이전트 통합 아키텍처`

본 데이터는 KCI 등재후보학술지 평가 프로젝트에서 Agent별 평가 기능을 검증하기 위해 원문 논문을 통제 변형하여 만든 synthetic degraded manuscript이다.

---

## 데이터 구성

### Original - 기준 원문

- 실제 원본 논문
- Agent2, Agent3 평가 결과 비교를 위한 기준 데이터
- GitHub에는 업로드하지 않고 로컬 테스트용으로만 사용
- `.gitignore`에 아래 경로 추가

```gitignore
data/Real_Paper.pdf
```

---

## Synthetic A - 학술적 가치/성과 저하

### 목적

Agent2가 학술적 가치와 성과 저하를 감지하는지 확인한다.

### 변형 내용

- 실험 데이터를 소수 예시 중심으로 제한
- 데이터 선정 기준 및 표본 규모 미고정
- 반복 실험 및 랜덤 시드 통제 미실시
- 통계적 유의성 검정 및 신뢰구간 미적용
- 외부 전문가 및 독립 평가 집단 검증 미실시
- 일부 평가 지표의 정의 및 산출 절차 미제시
- 결과를 탐색적 비교 수준으로 약화

### 기대 결과

- Agent1: Original과 동일하게 통과
- Agent2: Original 대비 점수 하락
- Agent3: Original과 유사한 수준 유지

---

## Synthetic B v2 - 구성/체제/가독성 저하

### 목적

Agent3가 논문 구성과 체제의 완전성 및 가독성 저하를 감지하는지 확인한다.

기존 B 버전은 Agent3 점수가 Synthetic A와 거의 차이가 나지 않아, 구조와 가독성 저하가 더 명확하게 드러나도록 수정하였다.

### 기존 변형 내용

- 실험 절 제목 체계 단순화 및 일관성 저하
- Fig. 1, Fig. 2 캡션을 `Results` 수준으로 과도하게 축약
- Table 1 캡션을 과도하게 축약
- 심층 분석 절 제목을 `추가 내용`으로 변경
- 결론 절 제목 형식 변경
- 결론에 의미가 반복되는 문장을 추가

### v2 추가 변형 내용

- 장·절 배치 순서를 의도적으로 어긋나게 구성
- 결론이 먼저 등장한 뒤 다시 `Ⅳ. 실험 및 평가` 절이 나오도록 순서 오류 추가
- 동일한 문장 및 문단을 반복 배치하여 가독성 저하 강화
- `추가 내용`, `결론 및 요약`과 같은 비표준 섹션 제목을 반복적으로 배치
- `Fig. 3 Results.`, `Table 2 Results.`와 같이 설명이 부족한 캡션 추가
- 본문 내 논리적 흐름이 끊기도록 일부 내용 순서를 재배치
- 저자 소속 및 직위 정보는 유지하여 affiliation 평가에는 영향을 주지 않도록 구성

### 기대 결과

- Agent1: Original과 동일하게 통과
- Agent2: 가능한 한 Original과 유사한 수준 유지
- Agent3: Original 대비 점수 하락

---

## Synthetic C v2 - 복합 저하

### 목적

Agent2와 Agent3의 평가 영역이 동시에 저하되었을 때 각 Agent가 담당 영역의 문제를 독립적으로 감지하는지 확인한다.

### 변형 내용

Synthetic C v2는 다음 두 종류의 저하 요소를 모두 포함한다.

- Synthetic A의 학술적 가치/성과 저하 요소
- Synthetic B v2의 구성/체제/가독성 저하 요소

### 기대 결과

- Agent1: Original과 동일하게 통과
- Agent2: Original 대비 점수 하락
- Agent3: Original 대비 점수 하락
- 3단계 내용평가 총점이 과락 기준인 56/80 미만으로 내려갈 가능성 확인

---

## Agent별 기대 패턴

### Agent1

Agent1은 외국어 초록 및 외국어 키워드 충족 여부를 평가한다.

이번 합성 데이터에서는 해당 영역을 변형하지 않았으므로 아래와 같은 결과를 기대한다.

```text
Original ≈ A ≈ B ≈ C
```

### Agent2

Agent2는 학술적 가치 및 성과를 평가한다.

```text
Original ≈ B > A ≈ C
```

### Agent3

Agent3는 논문 구성, 체제의 완전성, 가독성, 저자 소속 및 직위 표기의 명확성을 평가한다.

```text
Original ≈ A > B ≈ C
```

---

## Agent3 테스트 결과

수정된 B/C v2를 기준으로 Agent3 단독 테스트를 수행하였다.

| 데이터 | completeness | readability | affiliation_clarity | 총점 |
|---|---|---|---|---:|
| Original | C | B | A | 22.8 / 26 |
| Synthetic A | C | C | A | 22.0 / 26 |
| Synthetic B v2 | D | E | A | 19.1 / 26 |
| Synthetic C v2 | E | E | A | 17.9 / 26 |

### 해석

- Synthetic A는 Agent2 평가 영역만 저하시켰기 때문에 Agent3 점수가 Original과 유사하게 유지되었다.
- Synthetic B v2는 구성 및 가독성 저하를 강화한 결과 Agent3 점수가 명확하게 하락하였다.
- Synthetic C v2는 Agent2와 Agent3 저하 요소를 모두 포함하며 Agent3에서도 낮은 점수를 보였다.
- affiliation 관련 정보는 변형하지 않았기 때문에 모든 데이터에서 `A`를 유지하였다.

---

## GitHub 업로드 기준

공통 테스트 데이터로 아래 파일을 `data/` 폴더에 저장한다.

```text
data/
├── Synthetic_A_AcademicValue_Degraded.pdf
├── Synthetic_B_StructureReadability_Degraded_v2.pdf
├── Synthetic_C_Combined_Degraded_v2.pdf
└── README.md
```

실제 원본 논문은 로컬 테스트용으로만 사용하며 GitHub에는 업로드하지 않는다.

```gitignore
data/Real_Paper.pdf
```

---

## 사용 시 주의

- 본 파일들은 실제 탈락 논문이 아니라 평가 Agent 검증을 위해 원문을 통제 변형한 synthetic degraded manuscripts이다.
- 절대적인 기대 점수를 정답으로 두기보다 Agent별 상대적 변화와 역할 분리를 확인하는 용도로 사용한다.
- Synthetic 데이터에 맞춰 특정 문구를 탐지하도록 프롬프트를 과도하게 조정하지 않는다.
- 최종 공통 데이터로 확정하기 전에 Agent2에서도 `Original ≈ B > A ≈ C` 패턴이 나타나는지 확인한다.
