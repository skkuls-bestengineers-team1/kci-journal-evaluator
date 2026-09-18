"""Agent2: 게재논문의 학술적 가치와 성과 (54점 만점, 편집위원회 활동 항목 제외)

세부항목 (config.ACADEMIC_VALUE_SUBSCORES 참고):
- recognition: 해당 학문 분야에서의 인지도 및 활용도
- suitability: KCI 등재지로서의 학술적 가치 및 적합성
- topic_fit: 게재논문의 학술지 주제와의 부합도

입력: state["paper"]["raw_text"]
출력: stage3_results 에 {"agent": "academic_value", "subitems": {...}, "score": ...} append

TODO:
- Pydantic 출력 스키마 정의 (세부항목별 등급 A~F + rationale)
- 프롬프트 작성
- LLM 호출 + 등급 -> 점수 환산 (config.GRADE_TO_RATIO)
"""

from state import KCIEvalState


def agent2_node(state: KCIEvalState) -> dict:
    raise NotImplementedError
