"""Agent3: 논문집의 구성과 체제의 완전성 및 가독성 (26점 만점)

세부항목 (config.STRUCTURE_SUBSCORES 참고):
- completeness: 논문집의 구성과 체제의 완전성
- readability: 게재된 논문의 가독성
- affiliation_clarity: 논문 저자의 소속기관과 직위 표기의 명확성

입력: state["paper"]["raw_text"]
출력: stage3_results 에 {"agent": "structure", "subitems": {...}, "score": ...} append

TODO:
- Pydantic 출력 스키마 정의 (세부항목별 등급 A~F + rationale)
- 프롬프트 작성
- LLM 호출 + 등급 -> 점수 환산 (config.GRADE_TO_RATIO)
"""

from state import KCIEvalState


def agent3_node(state: KCIEvalState) -> dict:
    raise NotImplementedError
