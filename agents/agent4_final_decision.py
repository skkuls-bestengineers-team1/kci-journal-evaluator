"""
Agent4: 종합심의 — 최종 판정 + 코멘트 생성

입력:
    state["stage2_score"]   # 2단계 체계평가 점수 (20점 만점)
    state["stage3_total"]   # 3단계 내용평가 합산 점수 (80점 만점)
    state["stage3_results"] # Agent2/Agent3 세부등급·근거 (코멘트용, 선택)

출력:
    final_score    # stage2_score + stage3_total (100점 만점)
    final_verdict  # "등재후보 선정" | "탈락"
    final_comment  # 판정 근거 코멘트

점수와 판정은 코드 하드룰로만 계산한다.
코멘트는 LLM이 생성하고, 실패 시 템플릿으로 대체한다.
"""

from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config import (
    FINAL_MAX_SCORE,
    FINAL_PASS_THRESHOLD,
    GEMINI_MODEL_NAME,
    STAGE2_MAX_SCORE,
    STAGE3_MAX_SCORE,
)
from state import KCIEvalState, Stage3AgentResult


class FinalComment(BaseModel):
    """종합심의 코멘트. 점수·판정은 변경하지 않는다."""

    comment: str = Field(
        description=(
            "한국어 종합심의 코멘트. 주어진 점수와 판정을 전제로, "
            "2단계·3단계 평가 근거를 요약해 선정/탈락 이유를 설명한다."
        )
    )


AGENT4_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
당신은 KCI 등재후보학술지 종합심의 위원입니다.

점수와 최종 판정은 이미 확정되어 있습니다.
당신은 그 판정을 뒤집거나 점수를 재계산하지 마십시오.
주어진 평가 근거를 바탕으로, 선정 또는 탈락 이유를
심사위원 코멘트 형식으로 작성하십시오.

작성 규칙:
1. 반드시 제공된 점수, 판정, 세부근거만 사용하십시오.
2. 존재하지 않는 논문 내용, 점수, 등급을 만들어내지 마십시오.
3. 판정과 모순되는 결론을 쓰지 마십시오.
4. 한국어로 3~6문장 작성하십시오.
5. 2단계(체계평가)와 3단계(내용평가)를 모두 언급하십시오.
6. 세부항목 등급이 있으면 강점과 약점을 균형 있게 요약하십시오.
7. 합격 기준은 100점 만점 중 {threshold}점입니다.
""",
        ),
        (
            "human",
            """
[확정된 종합심의 결과]
- 최종 점수: {final_score} / {final_max}
- 판정: {verdict}
- 합격 기준: {threshold}점 이상

[2단계 체계평가]
- 점수: {stage2_score} / {stage2_max}
- 주제어 및 초록 외국어화: {foreign_lang_summary}

[3단계 내용평가]
- 합산 점수: {stage3_total} / {stage3_max}
- 세부 평가:
{stage3_summary}

위 내용을 바탕으로 종합심의 코멘트를 작성하십시오.
""",
        ),
    ]
)


def compute_final_decision(
    stage2_score: float,
    stage3_total: float,
) -> tuple[float, str]:
    """2단계+3단계 합산 점수와 최종 판정을 계산한다."""

    final_score = round(float(stage2_score) + float(stage3_total), 1)

    if final_score >= FINAL_PASS_THRESHOLD:
        verdict = "등재후보 선정"
    else:
        verdict = "탈락"

    return final_score, verdict


def _format_foreign_lang_summary(state: KCIEvalState) -> str:
    """2단계 외국어화 판정 요약을 만든다."""

    satisfied = state.get("foreign_lang_satisfied")
    extraction_failed = state.get("foreign_lang_extraction_failed")

    if extraction_failed is True:
        return "초록/주제어 섹션 추출 실패 (오탈락 가능)"
    if satisfied is True:
        return "충족"
    if satisfied is False:
        return "미충족"
    return "정보 없음"


def _format_stage3_summary(state: KCIEvalState) -> str:
    """Agent2/Agent3 세부등급·근거를 코멘트용 텍스트로 정리한다."""

    results = state.get("stage3_results") or []
    if not results:
        return "세부 평가 결과 없음"

    agent_labels = {
        "academic_value": "학술적 가치와 성과",
        "structure": "구성·체제·가독성",
    }

    lines: list[str] = []

    for result in results:
        typed: Stage3AgentResult = result
        agent = typed.get("agent", "unknown")
        label = agent_labels.get(agent, agent)
        score = typed.get("score")
        lines.append(f"- {label}: {score}점")

        subitems = typed.get("subitems") or {}
        for name, evaluation in subitems.items():
            grade = evaluation.get("grade", "?")
            rationale = (evaluation.get("rationale") or "").strip()
            if len(rationale) > 180:
                rationale = rationale[:180].rstrip() + "…"
            lines.append(f"  · {name}: {grade} — {rationale}")

    return "\n".join(lines)


def render_template_comment(
    state: KCIEvalState,
    final_score: float,
    verdict: str,
) -> str:
    """LLM 없이 사용할 템플릿 코멘트."""

    stage2_score = state["stage2_score"]
    stage3_total = state["stage3_total"]
    gap = round(final_score - FINAL_PASS_THRESHOLD, 1)

    if verdict == "등재후보 선정":
        decision_line = (
            f"2단계와 3단계 합산 {final_score}점은 합격 기준 "
            f"{FINAL_PASS_THRESHOLD}점을 {gap}점 상회하므로 등재후보로 선정한다."
        )
    else:
        decision_line = (
            f"2단계와 3단계 합산 {final_score}점은 합격 기준 "
            f"{FINAL_PASS_THRESHOLD}점에 {abs(gap)}점 부족하므로 탈락한다."
        )

    return (
        f"{decision_line}\n"
        f"2단계 체계평가(주제어 및 초록 외국어화)는 "
        f"{stage2_score}/{STAGE2_MAX_SCORE}점({_format_foreign_lang_summary(state)})이다.\n"
        f"3단계 내용평가는 {stage3_total}/{STAGE3_MAX_SCORE}점이다.\n"
        f"{_format_stage3_summary(state)}"
    )


def _generate_llm_comment(
    state: KCIEvalState,
    final_score: float,
    verdict: str,
) -> str:
    """Gemini로 종합심의 코멘트를 생성한다."""

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(FinalComment)
    chain = AGENT4_PROMPT | structured_llm

    result = chain.invoke(
        {
            "final_score": final_score,
            "final_max": FINAL_MAX_SCORE,
            "verdict": verdict,
            "threshold": FINAL_PASS_THRESHOLD,
            "stage2_score": state["stage2_score"],
            "stage2_max": STAGE2_MAX_SCORE,
            "foreign_lang_summary": _format_foreign_lang_summary(state),
            "stage3_total": state["stage3_total"],
            "stage3_max": STAGE3_MAX_SCORE,
            "stage3_summary": _format_stage3_summary(state),
        }
    )

    comment = (result.comment or "").strip()
    if not comment:
        raise ValueError("LLM이 빈 코멘트를 반환했습니다.")
    return comment


def generate_final_comment(
    state: KCIEvalState,
    final_score: float,
    verdict: str,
) -> str:
    """LLM 코멘트를 시도하고, 실패하면 템플릿으로 대체한다."""

    try:
        return _generate_llm_comment(state, final_score, verdict)
    except Exception as error:
        template = render_template_comment(state, final_score, verdict)
        return (
            f"{template}\n"
            f"(코멘트 생성 모델 호출에 실패하여 템플릿으로 대체함: {error})"
        )


def agent4_node(state: KCIEvalState) -> dict:
    """2+3단계 점수를 합산해 최종 판정과 코멘트를 반환한다."""

    stage2_score = state.get("stage2_score")
    stage3_total = state.get("stage3_total")

    if stage2_score is None:
        raise ValueError("Agent4 종합심의를 수행할 stage2_score가 없습니다.")
    if stage3_total is None:
        raise ValueError("Agent4 종합심의를 수행할 stage3_total이 없습니다.")

    final_score, verdict = compute_final_decision(
        stage2_score,
        stage3_total,
    )

    return {
        "final_score": final_score,
        "final_verdict": verdict,
        "final_comment": generate_final_comment(state, final_score, verdict),
    }
