"""
Agent2: 게재논문의 학술적 가치와 성과 (54점 만점, 편집위원회 활동 항목 제외)

세부항목 (config.ACADEMIC_VALUE_SUBSCORES 참고):
- recognition: 해당 학문 분야에서의 인지도 및 활용도
- suitability: KCI 등재지로서의 학술적 가치 및 적합성
- topic_fit: 게재논문의 학술지 주제와의 부합도

입력:
    state["paper"]["raw_text"],
    state["journal_meta"](주제 분야 정보)

출력: 
    stage3_results 에
    {
        "agent": "academic_value", 
        "subitems": {
            "recognition": {
                "grade": "A" ~ "F",
                "rationale": "해당 등급을 부여한 구체적인 이유"
            },
            "suitability": {
                "grade": "A" ~ "F",
                "rationale": "해당 등급을 부여한 구체적인 이유"
            },
            "topic_fit": {
                "grade": "A" ~ "F",
                "rationale": "해당 등급을 부여한 구체적인 이유"
            }
        },
        "score": 0.0 ~ 54.0
    } 
    
    append
LLM은 각 세부항목의 등급과 평가 근거만 생성한다.
최종 점수는 config.GRADE_TO_RATIO를 사용하여 코드에서 계산한다.

"""

from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config import (
    GEMINI_MODEL_NAME,
    GRADE_TO_RATIO,
    ACADEMIC_VALUE_MAX_SCORE,
    ACADEMIC_VALUE_SUBSCORES,
)
from state import Grade, KCIEvalState


# ==========================================================
# 1. LLM Structured Output Schema
# ==========================================================

class SubitemEvaluation(BaseModel):
    """Agent2 세부 평가항목 하나에 대한 평가 결과."""

    grade: Grade = Field(
        description="평가 등급. 반드시 A, B, C, D, E, F 중 하나"
    )
    rationale: str = Field(
        description="해당 등급을 부여한 구체적인 이유"
    )


class AcademicValueEvaluation(BaseModel):
    """Agent2가 평가하는 세 가지 세부항목."""

    recognition: SubitemEvaluation = Field(
        description="해당 학문 분야에서의 인지도 및 활용도 평가"
    )
    suitability: SubitemEvaluation = Field(
        description="KCI 등재지로서의 학술적 가치 및 적합성 평가"
    )
    topic_fit: SubitemEvaluation = Field(
        description="게재논문의 학술지 주제와의 부합도 평가"
    )


# ==========================================================
# 2. Agent2 Prompt
# ==========================================================

AGENT2_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
당신은 KCI 학술지 내용평가를 수행하는 전문 평가위원입니다.

당신의 담당 항목은 오직
'게재논문의 학술적 가치와 성과'입니다.

논문집의 구성·체제·가독성, 저자 소속 표기 등은 다른 평가위원의
담당 영역이므로 이 평가에서는 점수에 반영하지 마십시오.

편집위원회의 활동(질적 수준 향상 노력, 전문성·정체성 제고 활동 등)은
논문 원문만으로 확인할 수 없는 정보이므로 이 평가에서 다루지 않습니다.

[평가 범위: 연구 내용과 논문 형식의 구분]

이 평가는 '연구 내용'만 대상으로 합니다.

- 연구 내용: 연구 주제와 필요성, 연구 설계, 자료와 분석 근거,
  결과의 해석, 결론이 근거에 의해 뒷받침되는지 여부
- 논문 형식: 오탈자, 표기 방식, 절 번호·제목, 그림·표의 캡션,
  절과 문단의 배치 순서, 문장·문단의 반복, 원고 편집 상태 등
  글의 겉모습과 편집에 관한 사항

논문 형식에 문제가 있더라도 어떤 항목의 등급에도 반영하지 마십시오.
형식 문제를 '신뢰성 저하', '완결성 부족', '논리적 흐름의 문제' 등으로
바꿔 표현하여 감점 근거로 삼는 것도 허용되지 않습니다.
평가 전에 논문의 형식 문제가 모두 교정되었다고 가정하고,
그 상태에서 남아 있는 연구 내용만 평가하십시오.

그림·표의 실제 이미지는 텍스트로 확인할 수 없으므로,
그림·표가 보이지 않는다는 사실 자체를 근거로 삼지 마십시오.

다음 세 가지 항목만 평가하십시오.


[1. recognition - 해당 학문 분야에서의 인지도 및 활용도]

다음 사항을 중심으로 평가합니다.

- 논문이 다루는 주제가 해당 학문분야에서 중요하거나 필요성이 높은가

주의:
논문 텍스트에서 확인할 수 없는 외부 인용 횟수, 다운로드 수, 학술지의
대외적 평판 등은 임의로 추정하지 마십시오. 확인 가능한 논문 내용(연구 배경,
선행연구와의 관계, 연구의 필요성 서술 등)만으로 판단하십시오.


[2. suitability — KCI 등재지로서의 학술적 가치 및 적합성]

- 동일하거나 유사한 분야의 다른 KCI 등재지 논문과 견주어 손색이 없을
  만큼 우수하고 좋은 내용을 담고 있는가
- 연구 설계와 분석 근거(자료, 분석 절차 등)가 연구 목적에 비추어
  제시되어 있는가
- 결론이 실제로 제시된 근거의 범위를 벗어나 과장되지 않는가

주의:
위 세 가지는 모두 연구 내용에 관한 기준입니다. 논문 형식의 결함은
이 항목의 감점 근거로 사용하지 마십시오.
연구 설계, 분석 근거, 결론의 타당성에서 실제로 확인되는 문제만
감점 근거로 삼으십시오.


[3. topic_fit — 게재논문의 학술지 주제와의 부합도]

- 논문의 연구 주제가 아래 제시되는 학술지의 주제분야(대분야/중분야)에
  부합하는가

학술지 주제분야 정보에 없는 내용을 추측하여 판단하지 마십시오.


[등급 기준]

A: 해당 항목의 평가 기준을 매우 충실하게 충족하며 의미 있는 문제가 거의 없음
B: 전반적으로 우수하나 경미한 문제가 일부 있음
C: 대체로 적절하나 개선이 필요한 부분이 명확하게 존재함
D: 최소한의 요건은 충족하지만 여러 중요한 개선점이 존재함
E: 해당 항목이 상당히 부족하며 전반적인 개선이 필요함
F: 해당 평가요건을 사실상 충족하지 못하거나, 논문에서 필요한 정보를
   확인할 수 없음


[평가 원칙]

1. 반드시 제공된 논문 텍스트와 학술지 주제분야 정보만 근거로 평가하십시오.
2. 존재하지 않는 내용을 만들어내지 마십시오.
3. 각 항목의 rationale에는 실제로 확인된 근거를 구체적으로 작성하십시오.
4. 논문집의 구성·가독성, 편집위원회 활동은 평가하지 마십시오.
   rationale에도 논문 형식 문제를 근거로 쓰지 마십시오.
5. 등급을 정하기 전에 각 감점 근거가 '연구 내용'의 문제인지
   '논문 형식'의 문제인지 구분하고, 형식 문제는 모두 제외하십시오.
   제외한 뒤 감점할 연구 내용상의 문제가 남지 않으면 등급을 낮추지 마십시오.
6. 세 항목을 서로 독립적으로 평가하십시오
""",
        ),
        (
            "human",
            """
학술지 주제분야: {major_research_field} / {middle_research_field}

---------------- 논문 시작 ----------------

{paper_text}

---------------- 논문 끝 ----------------

위 논문을 recognition, suitability, topic_fit
세 항목에 대해 각각 A~F 등급으로 평가하고
구체적인 근거를 제시하십시오.
""",
        ),
    ]
)


# ==========================================================
# 3. Score Calculation
# ==========================================================

def calculate_academic_value_score(evaluation: AcademicValueEvaluation) -> float:
    """Agent2의 A~F 평가 결과를 54점 만점 점수로 환산한다."""

    grades = {
        "recognition": evaluation.recognition.grade,
        "suitability": evaluation.suitability.grade,
        "topic_fit": evaluation.topic_fit.grade,
    }

    raw_score = 0.0

    for subitem, grade in grades.items():
        max_score = ACADEMIC_VALUE_SUBSCORES[subitem]
        ratio = GRADE_TO_RATIO[grade]

        raw_score += max_score * ratio

    configured_max = sum(ACADEMIC_VALUE_SUBSCORES.values())

    normalized_score = (
        raw_score / configured_max * ACADEMIC_VALUE_MAX_SCORE
    )

    return round(normalized_score, 1)


# ==========================================================
# 4. Agent2 Node
# ==========================================================

def _get(obj, key, default=None):
    """dict와 Pydantic 객체를 모두 읽는다 (그래프 안에서는 state가 객체로 전달됨)."""

    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def agent2_node(state: KCIEvalState) -> dict:
    """논문의 학술적 가치와 성과를 평가하고 Agent2 결과를 반환한다."""

    paper = _get(state, "paper", {})
    paper_text = (_get(paper, "raw_text") or "").strip()

    if not paper_text:
        raise ValueError(
            "Agent2 평가를 수행할 논문 텍스트가 없습니다."
        )

    journal_meta = _get(state, "journal_meta", {})
    major_research_field = _get(journal_meta, "major_research_field") or ""
    middle_research_field = _get(journal_meta, "middle_research_field") or ""

    llm = ChatGoogleGenerativeAI(
        model = GEMINI_MODEL_NAME,
        temperature = 0
    )

    structured_llm = llm.with_structured_output(
        AcademicValueEvaluation
    )

    chain = AGENT2_PROMPT | structured_llm

    evaluation = chain.invoke(
        {
            "paper_text": paper_text,
            "major_research_field": major_research_field,
            "middle_research_field": middle_research_field
        }
    )
    score = calculate_academic_value_score(evaluation)

    result = {
        "agent": "academic_value",
        "subitems": {
            "recognition": {
                "grade": evaluation.recognition.grade,
                "rationale": evaluation.recognition.rationale,
            },
            "suitability": {
                "grade": evaluation.suitability.grade,
                "rationale": evaluation.suitability.rationale,
            },
            "topic_fit": {
                "grade": evaluation.topic_fit.grade,
                "rationale": evaluation.topic_fit.rationale,
            },
        },
        "score": score,
    }
    # stage3_results에는 Agent2와 Agent3가 각각 list로 결과를 반환하고,
    # state.py의 Annotated[list, add] reducer가 두 결과를 합친다.
    return {
        "stage3_results": [result]
    }
