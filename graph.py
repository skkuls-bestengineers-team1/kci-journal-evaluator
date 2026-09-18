"""그래프 조립: 노드 등록 + 엣지 배선 + 게이트 로직

흐름: START -> stage1_gate -> agent1_foreign_lang -> stage2_gate
      -> [agent2_academic_value, agent3_structure] (병렬) -> stage3_aggregator
      -> agent4_final_decision -> END

게이트(stage1_gate, stage2_gate, stage3_aggregator)는 LLM이 아닌 코드 하드룰.
TODO(리드): 게이트 함수 구현 + add_node/add_edge 배선
"""

from langgraph.graph import END, START, StateGraph

from agents.agent1_foreign_lang import agent1_node
from agents.agent2_academic_value import agent2_node
from agents.agent3_structure import agent3_node
from agents.agent4_final_decision import agent4_node
from state import KCIEvalState


def stage1_gate(state: KCIEvalState):
    """1단계 신청자격: stage1_checklist 5개 항목 모두 True인지 확인. 실패 시 탈락."""
    # TODO: 구현
    raise NotImplementedError


def stage2_gate(state: KCIEvalState):
    """2단계 항목과락: stage2_score == 0 이면 즉시 탈락."""
    # TODO: 구현
    raise NotImplementedError


def stage3_aggregator(state: KCIEvalState):
    """3단계 배점과락: stage3_results 합산 후 STAGE3_PASS_THRESHOLD 미만이면 탈락."""
    # TODO: 구현
    raise NotImplementedError


def build_graph():
    workflow = StateGraph(KCIEvalState)

    # TODO: 노드 등록
    # workflow.add_node("stage1_gate", stage1_gate)
    # workflow.add_node("agent1_foreign_lang", agent1_node)
    # workflow.add_node("stage2_gate", stage2_gate)
    # workflow.add_node("agent2_academic_value", agent2_node)
    # workflow.add_node("agent3_structure", agent3_node)
    # workflow.add_node("stage3_aggregator", stage3_aggregator)
    # workflow.add_node("agent4_final_decision", agent4_node)

    # TODO: 엣지 배선 (게이트는 Command(goto=...) 또는 add_conditional_edges 중 택1)

    return workflow.compile()
