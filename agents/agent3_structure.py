"""
Agent3: 논문집의 구성과 체제의 완전성 및 가독성 (26점 만점)

세부항목 (config.STRUCTURE_SUBSCORES 참고):
- completeness: 논문집의 구성과 체제의 완전성
- readability: 게재된 논문의 가독성
- affiliation_clarity: 논문 저자의 소속기관과 직위 표기의 명확성

입력:
    state["paper"]["raw_text"]

출력:
    stage3_results에 아래 구조의 결과를 추가한다.

    {
        "agent": "structure",
        "subitems": {
            "completeness": {
                "grade": "A" ~ "F",
                "rationale": "평가 근거"
            },
            "readability": {
                "grade": "A" ~ "F",
                "rationale": "평가 근거"
            },
            "affiliation_clarity": {
                "grade": "A" ~ "F",
                "rationale": "평가 근거"
            }
        },
        "score": 0.0 ~ 26.0
    }

LLM은 각 세부항목의 등급과 평가 근거만 생성한다.
최종 점수는 config.GRADE_TO_RATIO를 사용하여 코드에서 계산한다.
"""

from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config import (
    GEMINI_MODEL_NAME,
    GRADE_TO_RATIO,
    STRUCTURE_MAX_SCORE,
    STRUCTURE_SUBSCORES,
)
from state import Grade, KCIEvalState



# 1. LLM Structured Output Schema
class SubitemEvaluation(BaseModel):
    """Agent3 세부 평가항목 하나에 대한 평가 결과."""

    grade: Grade = Field(
        description="평가 등급. 반드시 A, B, C, D, E, F 중 하나"
    )
    rationale: str = Field(
        description=(
            "해당 등급을 부여한 구체적인 이유. "
            "반드시 제공된 논문 텍스트에서 확인할 수 있는 근거를 사용한다."
        )
    )


class StructureEvaluation(BaseModel):
    """Agent3가 평가하는 세 가지 세부항목."""

    completeness: SubitemEvaluation = Field(
        description="논문집의 구성과 체제의 완전성 평가"
    )
    readability: SubitemEvaluation = Field(
        description="게재 논문의 가독성 평가"
    )
    affiliation_clarity: SubitemEvaluation = Field(
        description="논문 저자의 소속기관과 직위 표기의 명확성 평가"
    )


# 2. Agent3 Prompt
AGENT3_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
당신은 KCI 학술지 내용평가를 수행하는 전문 평가위원입니다.

당신의 담당 항목은 오직
'논문집의 구성과 체제의 완전성 및 가독성'입니다.

논문의 학술적 가치, 연구의 독창성, 연구방법의 타당성,
실험 성능, 연구 결과의 우수성 등은 다른 평가위원의 담당 영역이므로
이 평가에서는 점수에 반영하지 마십시오.

다음 세 가지 항목만 평가하십시오.


[1. completeness — 구성과 체제의 완전성]

다음 사항을 중심으로 평가합니다.

- 제목, 저자, 초록, 주제어 등 기본 요소가 적절하게 존재하는가
- 서론, 본론 또는 연구방법, 결과, 결론, 참고문헌 등
  학술논문에 필요한 주요 구성요소가 갖추어져 있는가
- 장·절 및 하위 항목의 구성이 체계적인가
- 표, 그림, 참고문헌 등이 본문과 적절하게 연결되어 있는가
- 논문 전체의 구성체계가 일관성 있게 유지되는가


[2. readability — 가독성]

다음 사항을 중심으로 평가합니다.

- 문장의 의미가 명확하게 전달되는가
- 문단 간 연결과 논문의 전개 흐름이 자연스러운가
- 동일한 내용이 불필요하게 반복되지 않는가
- 지나치게 길거나 이해하기 어려운 문장이 과도하게 존재하지 않는가
- 표·그림·결과에 대한 본문의 설명이 독자의 이해를 돕는가

주의:
PDF에서 텍스트를 추출하는 과정에서 발생한 것으로 보이는
단순 줄바꿈, 단어 분리, 페이지 번호 등의 오류는
가독성 감점 근거로 사용하지 마십시오.

또한 제공된 입력은 PDF에서 추출한 텍스트이므로
폰트, 실제 그림 해상도, 페이지 디자인 등
텍스트만으로 확인할 수 없는 시각적 요소를 추측하여 평가하지 마십시오.


[3. affiliation_clarity — 저자 소속기관 및 직위 표기의 명확성]

다음 사항을 중심으로 평가합니다.

- 각 저자의 소속기관을 확인할 수 있는가
- 학과·기관 등의 소속정보가 구체적으로 표시되어 있는가
- 저자의 직위 또는 신분을 확인할 수 있는가
- 저자와 각 소속정보의 대응관계가 명확한가

논문에서 확인할 수 없는 정보는 임의로 추론하지 마십시오.


[등급 기준]

A:
평가 기준을 매우 충실하게 충족하며 의미 있는 문제가 거의 없음

B:
전반적으로 우수하나 경미한 문제가 일부 있음

C:
대체로 적절하나 개선이 필요한 부분이 명확하게 존재함

D:
최소한의 요건은 충족하지만 여러 중요한 개선점이 존재함

E:
구성 또는 가독성이 상당히 부족하며 전반적인 개선이 필요함

F:
해당 평가요건을 사실상 충족하지 못하거나,
논문에서 필요한 정보를 확인할 수 없음


[평가 원칙]

1. 반드시 제공된 논문 텍스트만 근거로 평가하십시오.
2. 존재하지 않는 내용을 만들어내지 마십시오.
3. 각 항목의 rationale에는 실제로 확인된 장점 또는 문제점을
   구체적으로 작성하십시오.
4. 학술적 독창성이나 연구 성과 자체는 평가하지 마십시오.
5. 세 항목을 서로 독립적으로 평가하십시오.
""",
        ),
        (
            "human",
            """
다음은 평가 대상 논문의 전체 텍스트입니다.

---------------- 논문 시작 ----------------

{paper_text}

---------------- 논문 끝 ----------------

위 논문을 completeness, readability, affiliation_clarity
세 항목에 대해 각각 A~F 등급으로 평가하고
구체적인 근거를 제시하십시오.
""",
        ),
    ]
)



# 3. Score Calculation
def calculate_structure_score(evaluation: StructureEvaluation) -> float:
    """Agent3의 A~F 평가 결과를 26점 만점 점수로 환산한다."""

    grades = {
        "completeness": evaluation.completeness.grade,
        "readability": evaluation.readability.grade,
        "affiliation_clarity": evaluation.affiliation_clarity.grade,
    }

    raw_score = 0.0

    for subitem, grade in grades.items():
        max_score = STRUCTURE_SUBSCORES[subitem]
        ratio = GRADE_TO_RATIO[grade]

        raw_score += max_score * ratio

    # STRUCTURE_SUBSCORES가 반올림되어
    # 합계가 26.0과 ±0.1 차이 날 수 있으므로
    # 최종적으로 26점 만점에 맞게 정규화한다.
    configured_max = sum(STRUCTURE_SUBSCORES.values())

    normalized_score = (
        raw_score / configured_max * STRUCTURE_MAX_SCORE
    )

    return round(normalized_score, 1)



# 4. Agent3 Node
def agent3_node(state: KCIEvalState) -> dict:
    """논문의 구성·체제·가독성을 평가하고 Agent3 결과를 반환한다."""

    paper = state["paper"] if isinstance(state, dict) else state.paper
    paper_text = paper["raw_text"].strip()

    if not paper_text:
        raise ValueError(
            "Agent3 평가를 수행할 논문 텍스트가 없습니다."
        )

    # Gemini 모델 생성
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        temperature=0,
    )

    # Gemini 출력 형식을 Pydantic 모델로 제한
    structured_llm = llm.with_structured_output(
        StructureEvaluation
    )

    # Prompt -> LLM -> Structured Output
    chain = AGENT3_PROMPT | structured_llm

    evaluation = chain.invoke(
        {
            "paper_text": paper_text,
        }
    )

    # A~F 등급을 실제 26점 기준 점수로 환산
    score = calculate_structure_score(evaluation)

    # state.py의 Stage3AgentResult 구조에 맞게 변환
    result = {
        "agent": "structure",
        "subitems": {
            "completeness": {
                "grade": evaluation.completeness.grade,
                "rationale": evaluation.completeness.rationale,
            },
            "readability": {
                "grade": evaluation.readability.grade,
                "rationale": evaluation.readability.rationale,
            },
            "affiliation_clarity": {
                "grade": evaluation.affiliation_clarity.grade,
                "rationale": evaluation.affiliation_clarity.rationale,
            },
        },
        "score": score,
    }

    # stage3_results에는 Agent2와 Agent3가 각각 list로 결과를 반환하고,
    # state.py의 Annotated[list, add] reducer가 두 결과를 합친다.
    return {
        "stage3_results": [result]
    }