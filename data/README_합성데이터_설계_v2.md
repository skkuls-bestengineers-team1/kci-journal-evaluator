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





# 제목 : Agent1 테스트
# 날짜 : 2026.09.20(일)
# 이름 : 최민정


# 1. Agent1 구성 및 평가 방법
Agent1은 3가지 tool을 사용하여 아래의 항목을 평가한다.

(1) 연간 학술지 발간 횟수(tool : get_journal_publication_frequency_score)
- 사용 API : Tavily API
- Input : JournalMetaData.issn, JournalMetaData.eissn, JournalMetaData.journal_name
- 위 input에 대한 "발행간기, 발행주기, 연간 발행횟수"를 구한다.
- 검색 정확성을 위해 issn, eissn이 일치할 경우 2점, 검색 결과에 "발행간기", "발행주기", "frequency", "issuesperyear" 키워드가 존재할 경우
  5점을 더하여 bonus 점수를 계산한다.
  이는 calculate_tavily_relevance_score() 함수로 구현했다.

- 위에서 구한 점수를 내림차순으로 하여 점수가 가장 높은 순서대로 정렬하여 검색 결과에서 "간기" 관련 키워드를 찾는다.
- "간기"와 관련된 키워드가 존재하면 해당 annual_count 키워드를 추출하여 발간 횟수를 구한다.
- 이는 extract_annual_publication_count() 함수로 구현했다.

- annual_count가 4(회 이하 단위는 생략) 이상일 경우 3점, 그 미만일 경우 3이상 4이하일 경우 2점, 1회 이상 3회 미만일 경우 1점을 부여한다.
- annual_count가 0점이거나 연간 발간 횟수 관련 데이터를 찾을 수 없을 경우 0점으로 처리한다.

* 주의사항
- 본 의도는 KCI에서 제공하는 API를 사용할 계획이었으나 API 인증까지 시간이 오래걸리는 이유로 ..
  Tavily 검색 API를 사용하였다.
- 따라서, 본래 계획보다 검색 정확성이 떨어지므로 KCI API Key를 발급받기 전까지만 사용한다.
  검색 정확성을 최대한 보정하기 위해 issn, essn, 간기와 관련하여 보너스 점수를 계산하는 로직을 추가했다.




(2) 학술지 및 수록 논문의 온라인 접근성(tool : get_online_access_score)
- 사용 API : OpenAlex API
- Input : JournalMetaData.iss
- issn와 일치하는 Journal의 메타 데이터를 API를 통해 검색한다.

- 위 검색 결과에 해당 학술지의 homepage_url(학술지 홈페이지), is_oa(무료/유료 공개 여부), last_publication_year(최신 발행 일자)로 발행 제공 연도를 구한다.
- homepage_url, is_oa이 모두 True이며 
    last_publication_year이 9년 이상일 경우 15점, 
    last_publication_year이 6년 이상일 경우 12점,
    last_publication_year이 4년 이상일 경우 9점,
    last_publication_year이 1년 이상일 경우 3점,
    last_publication_year이 1년 미만일 경우 0점을 부여한다.
- is_oa이 False인 경우 0점을 부여한다.





(3) 주제어 및 논문 초록의 외국어화(tool : get_keyword_abstract_foreign_language_score)
- 사용 Model : gemini-3.6-flash
- Input : PaperInput.raw_text
- 논문의 raw_text를 분석하여 외국어 Keywords와 Abstract가 모두 존재하는지 판정하여 비율을 구한다.
- foreign_language_ratio가 100%인 경우 2점, 90% 이상인 경우 1.5점, 80% 이상인 경우 1점
  70%인 이상 0.5점, foreign_lang_scor인 경우 0점을 부여한다.




(4) 평가 결과(agent1_node)
- 위에 기술한 3개의 tool을 사용하여 총점과 최종 PASS/FAIL을 구한다.
- 해당 과정에서는 LLM을 사용하지 않았다.
- 세 항목 모두 0점보다 크면 PASS이고, 하나라도 0점이면 FAIL 처리한다.



(2) Agent1 단위 테스트 결과

[1]
Synthetic_A_AcademicValue_Degraded.pdf
Synthetic_B_StructureReadability_Degraded.pdf
Synthetic_C_Combined_Degraded.pdf

[결과]
- 연간 학술지 발간횟수 : 3.0 / PASS
- 학술지 수록 및 수록 논문의 온라인 접근성 : 3.0 / True
- 주제어 및 논문 초록의 외국화 : 2.0 / PASS

- 해당 테스트 데이터들의 경우 agent1의 경우 통과하도록 설계되어 있다. 
  하여, 당연히 Pass이다.


[2]
- Agent1의 3번째 평가기준인 "주제어 및 논문 초록의 외국어화" 항목을 Fail 되도록 의도적으로
  데이터를 조작하였다.
- 해당 테스트 데이터와 코드는 아래에 주석처리 하였으니, 테스트 시 사용 바란다.


# agent1 테스트용 코드

def get_text_raw_text(path : Path):

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


if __name__ == "__main__":

    state: KCIEvalState = {
        "journal_meta" : {
            "journal_name": "한국정보통신학회논문지",
            "abbreviation": "JKIICE",
            "issn": "2234-4772",
            "eissn": "2288-4165",
            "major_research_field": "공학",
            "middle_research_field": "전자/정보통신공학",
        },

        "paper": {
            "paper_id": "TEST-PAPER-001",
            "raw_text": """

스마트 제조 환경에서의 설비 이상 탐지 시스템 연구

홍길동, 김철수

요약

최근 제조 산업에서는 생산 설비에서 발생하는 데이터를 활용하여
설비의 이상 상태를 사전에 탐지하는 기술의 중요성이 증가하고 있다.

본 연구에서는 제조 설비에서 수집되는 온도, 진동, 전류 데이터를
기반으로 설비 이상 상태를 탐지하는 시스템을 제안한다.

제안 시스템은 센서 데이터를 일정 시간 단위로 수집하고,
데이터의 평균값과 변화량을 이용하여 정상 상태와 이상 상태를
구분하도록 설계하였다.

실험 결과, 제안한 방법은 특정 설비 이상 상황에서 기존의
단순 임계값 기반 방법보다 안정적으로 이상 상태를 탐지할 수 있었다.

본 연구 결과는 향후 제조 현장의 설비 모니터링 및
예지 정비 시스템 구축에 활용될 수 있을 것으로 기대된다.

주제어

스마트 제조, 이상 탐지, 설비 모니터링, 센서 데이터, 예지 정비


1. 서론

최근 제조 산업에서는 생산설비의 자동화와 지능화가 빠르게
진행되고 있다. 특히 다양한 센서를 이용하여 설비 데이터를
실시간으로 수집하고 분석하는 기술이 중요해지고 있다.

설비에서 발생하는 이상 상태를 조기에 발견하지 못할 경우
생산 중단이나 품질 저하 등의 문제가 발생할 수 있다.

따라서 본 논문에서는 센서 데이터를 이용하여 제조 설비의
상태를 분석하고 이상 여부를 판단하는 방법을 제안한다.


2. 관련 연구

기존 설비 이상 탐지 연구에서는 온도, 진동, 전류와 같은
센서 데이터를 이용한 다양한 방법이 제안되었다.

일부 연구에서는 고정된 임계값을 이용하여 이상 상태를
판정하였으며, 최근에는 머신러닝 기법을 적용하는 연구도
진행되고 있다.


3. 제안 방법

본 연구에서는 설비에서 발생하는 센서 데이터를 일정한
시간 간격으로 수집한다.

수집된 데이터에 대하여 평균값과 변화량을 계산한 후,
사전에 설정된 정상 범위와 비교하여 이상 여부를 판단한다.


4. 실험 결과

제안 방법을 테스트 데이터에 적용한 결과,
정상 상태와 비정상 상태를 구분할 수 있었다.

특히 센서값이 급격하게 변화하는 경우 기존 방법보다
빠르게 이상 상태를 확인할 수 있었다.


5. 결론

본 연구에서는 제조 설비의 센서 데이터를 이용한
이상 탐지 방법을 제안하였다.

향후에는 보다 다양한 설비 데이터와 실제 제조 환경을
대상으로 추가적인 연구가 필요하다.


참고문헌

[1] 김철수, 제조 설비 데이터 분석에 관한 연구,
한국산업정보학회논문지, 2024.

[2] 이영희, 스마트팩토리 환경의 설비 모니터링 시스템,
정보처리학회논문지, 2023.

            
            
            """,
        },

        "stage1_checklist": {},
        "stage1_pass": True,
    }

    agent1_node(
        state
    )




