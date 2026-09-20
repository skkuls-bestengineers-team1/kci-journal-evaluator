"""LangGraph 조립: 노드 등록 + 엣지 배선 + 게이트 로직

흐름:
    START
      -> stage1_gate
      -> agent1_foreign_lang
      -> stage2_gate
      -> [agent2_academic_value, agent3_structure]  (병렬)
      -> stage3_aggregator
      -> agent4_final_decision
      -> END

게이트(stage1_gate, stage2_gate, stage3_aggregator)는 LLM이 아닌 코드 하드룰이다.
과락 시 이후 노드를 건너뛰고 END로 종료한다.
"""

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

import config  # 프로젝트 루트 .env를 Agent import 전에 로드한다.
from agents.agent1_foreign_lang import agent1_node
from agents.agent2_academic_value import agent2_node
from agents.agent3_structure import agent3_node
from agents.agent4_final_decision import agent4_node
from config import STAGE3_PASS_THRESHOLD
from state import KCIEvalState

STAGE1_REQUIRED_KEYS = (
    "발행규칙성",
    "심사위원수",
    "연구윤리",
    "투고다양성",
    "기본체계",
)


def _get(state: Any, key: str, default=None):
    """TypedDict/dict와 Pydantic state를 모두 읽는다."""

    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)


def _stage2_score(state: Any):
    score = _get(state, "total_stage2_score")
    if score is None:
        score = _get(state, "stage2_score")
    return score


def stage1_gate(state: KCIEvalState) -> dict:
    """1단계 신청자격: stage1_checklist 5개 항목 모두 True인지 확인. 실패 시 탈락."""

    checklist = _get(state, "stage1_checklist") or {}
    failed = [key for key in STAGE1_REQUIRED_KEYS if not checklist.get(key)]

    if failed:
        return {
            "stage1_pass": False,
            "final_verdict": "탈락",
            "rejection_reason": f"1단계 신청자격 미충족: {', '.join(failed)}",
        }

    return {"stage1_pass": True}


def route_after_stage1(
    state: KCIEvalState,
) -> Literal["agent1_foreign_lang", "end"]:
    return "agent1_foreign_lang" if _get(state, "stage1_pass") else "end"


def stage2_gate(state: KCIEvalState) -> dict:
    """2단계 항목과락: total_stage2_pass가 False이거나 점수가 0이면 즉시 탈락."""

    passed = _get(state, "total_stage2_pass")
    score = _stage2_score(state)
    if passed is False or score is None or float(score) == 0:
        return {
            "final_score": 0.0,
            "final_verdict": "탈락",
            "rejection_reason": "2단계 항목과락: 체계평가 미충족",
        }

    return {}


def route_after_stage2(state: KCIEvalState) -> Literal["start_stage3", "end"]:
    passed = _get(state, "total_stage2_pass")
    score = _stage2_score(state)
    if passed is False or score is None or float(score) == 0:
        return "end"
    return "start_stage3"


def start_stage3(state: KCIEvalState) -> dict:
    """Agent2·Agent3 병렬 실행을 위한 분기점."""
    return {}


def stage3_aggregator(state: KCIEvalState) -> dict:
    """3단계 배점과락: stage3_results 합산 후 STAGE3_PASS_THRESHOLD 미만이면 탈락."""

    results = _get(state, "stage3_results") or []
    total = round(sum(float(item.get("score") or 0) for item in results), 1)
    stage2_score = float(_stage2_score(state) or 0)

    if total < STAGE3_PASS_THRESHOLD:
        return {
            "stage3_total": total,
            "stage3_pass": False,
            "final_score": round(stage2_score + total, 1),
            "final_verdict": "탈락",
            "rejection_reason": (
                f"3단계 배점과락: {total}점 / 기준 {STAGE3_PASS_THRESHOLD}점"
            ),
        }

    return {
        "stage3_total": total,
        "stage3_pass": True,
    }


def route_after_stage3(
    state: KCIEvalState,
) -> Literal["agent4_final_decision", "end"]:
    return "agent4_final_decision" if _get(state, "stage3_pass") else "end"


def build_graph():
    workflow = StateGraph(KCIEvalState)

    workflow.add_node("stage1_gate", stage1_gate)
    workflow.add_node("agent1_foreign_lang", agent1_node)
    workflow.add_node("stage2_gate", stage2_gate)
    workflow.add_node("start_stage3", start_stage3)
    workflow.add_node("agent2_academic_value", agent2_node)
    workflow.add_node("agent3_structure", agent3_node)
    workflow.add_node("stage3_aggregator", stage3_aggregator)
    workflow.add_node("agent4_final_decision", agent4_node)

    workflow.add_edge(START, "stage1_gate")
    workflow.add_conditional_edges(
        "stage1_gate",
        route_after_stage1,
        {
            "agent1_foreign_lang": "agent1_foreign_lang",
            "end": END,
        },
    )
    workflow.add_edge("agent1_foreign_lang", "stage2_gate")
    workflow.add_conditional_edges(
        "stage2_gate",
        route_after_stage2,
        {
            "start_stage3": "start_stage3",
            "end": END,
        },
    )
    workflow.add_edge("start_stage3", "agent2_academic_value")
    workflow.add_edge("start_stage3", "agent3_structure")
    workflow.add_edge("agent2_academic_value", "stage3_aggregator")
    workflow.add_edge("agent3_structure", "stage3_aggregator")
    workflow.add_conditional_edges(
        "stage3_aggregator",
        route_after_stage3,
        {
            "agent4_final_decision": "agent4_final_decision",
            "end": END,
        },
    )
    workflow.add_edge("agent4_final_decision", END)

    return workflow.compile()
