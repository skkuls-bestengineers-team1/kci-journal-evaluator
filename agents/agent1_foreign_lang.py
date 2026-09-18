"""Agent1: 주제어 및 논문 초록의 외국어화 판정 (LLM 미사용, 규칙 기반)

입력: state["paper"]["raw_text"]
출력: foreign_lang_satisfied, foreign_lang_extraction_failed, stage2_score

TODO:
- 초록/주제어 섹션 추출 (정규식/키워드 매칭)
- 외국어 여부 판별 로직
- 추출 실패와 "실제 미충족"을 구분해서 foreign_lang_extraction_failed 에 기록
"""

from state import KCIEvalState


def agent1_node(state: KCIEvalState) -> dict:
    raise NotImplementedError
