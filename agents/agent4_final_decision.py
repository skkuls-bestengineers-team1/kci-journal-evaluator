"""Agent4: 종합심의 — 최종 판정 + 코멘트 생성

입력: state["stage2_score"], state["stage3_total"]
출력: final_score, final_verdict ("등재후보 선정" / "탈락"), final_comment

TODO:
- final_score = stage2_score + stage3_total 계산
- FINAL_PASS_THRESHOLD(config.py) 기준으로 판정
- 판정 근거 코멘트 생성 (LLM 또는 템플릿)
"""

from state import KCIEvalState


def agent4_node(state: KCIEvalState) -> dict:
    raise NotImplementedError
