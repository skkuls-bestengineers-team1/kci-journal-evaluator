"""KCI 등재후보 예측 파이프라인 State 정의.

State 필드는 팀 전체 합의 후에만 추가/변경한다 (PR 리뷰 필수).
각 Agent는 자기 담당 필드만 쓰고(write), 다른 필드는 읽기(read)만 한다.
"""

from operator import add
from typing import Annotated, Literal, Optional, TypedDict

Grade = Literal["A", "B", "C", "D", "E", "F"]


class PaperInput(TypedDict):
    paper_id: str
    raw_text: str  # PDF에서 추출한 논문 전문 텍스트


class SubitemGrade(TypedDict):
    grade: Grade
    rationale: str


class Stage3AgentResult(TypedDict):
    agent: Literal["academic_value", "structure"]
    subitems: dict[str, SubitemGrade]
    score: float  # 재배점 기준 환산 점수 (academic_value: 54점 만점, structure: 26점 만점)


class KCIEvalState(TypedDict):
    # 입력
    journal_meta: dict  # 학술지 기본정보 (이름, 분야 등)
    paper: PaperInput  # 평가대상 논문 1편. MVP는 다수 논문 집계를 지원하지 않음.

    # 1단계 신청자격: UI 체크리스트, LLM 판단 없이 코드 로직으로만 판정
    stage1_checklist: dict  # {"발행규칙성": True, "심사위원수": True, ...} — UI에서 주입
    stage1_pass: Optional[bool]

    # 2단계 체계평가: 원본 3개 항목 중 "주제어 및 초록 외국어화"만 구현.
    # 나머지 2개 항목(연간 발간횟수, 온라인 접근성)을 생략하는 대신
    # 이 항목이 2단계 배점 20점 전체를 대표하도록 재배점했다 (원배점 2점 -> 20점).
    foreign_lang_satisfied: Optional[bool]  # 초록+주제어 모두 외국어 표기 여부 (논문 1편 기준 이진 판정)
    foreign_lang_extraction_failed: Optional[bool]  # 초록/주제어 섹션 추출 자체가 실패했는지 (오탈락 진단용, "실제 미충족"과 구분)
    stage2_score: Optional[float]  # 20점 또는 0점
    stage2_pass: Optional[bool]

    # 3단계 내용평가: Agent2(학술적 가치, 54점)·Agent3(구성/가독성, 26점) 병렬 실행.
    # 둘 다 stage3_results에 append하므로 Annotated + add reducer로 병합한다.
    stage3_results: Annotated[list[Stage3AgentResult], add]
    stage3_total: Optional[float]
    stage3_pass: Optional[bool]

    # 4단계 종합심의
    final_score: Optional[float]  # stage2_score + stage3_total (100점 만점)
    final_verdict: Optional[Literal["등재후보 선정", "탈락"]]
    final_comment: Optional[str]

    # 탈락 시 사유 (게이트 어디서 걸렸는지 UI에 표시하기 위함)
    rejection_reason: Optional[str]
