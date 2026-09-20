"""KCI 등재후보 예측 파이프라인 State 정의.

State 필드는 팀 전체 합의 후에만 추가/변경한다 (PR 리뷰 필수).
각 Agent는 자기 담당 필드만 쓰고(write), 다른 필드는 읽기(read)만 한다.
"""

from operator import add
from typing import Annotated, Literal, Optional, TypedDict
from pydantic import BaseModel, Field

Grade = Literal["A", "B", "C", "D", "E", "F"]


class PaperInput(TypedDict):
    paper_id: str
    raw_text: str  # PDF에서 추출한 논문 전문 텍스트


class SubitemGrade(TypedDict):
    grade: Grade
    rationale: str


# ==========================================================
# 2단계 Tool 결과용 BaseModel
# ==========================================================

class ForeignLanguageResult(BaseModel):
    foreign_language_ratio: float = Field(
        ge=0,
        le=100,
        description="주제어 및 논문 초록의 외국어화 비율"
    )

    foreign_language_reason: str = Field(
        description="외국어화 비율 판정 근거"
    )



class Stage3AgentResult(TypedDict):
    agent: Literal["academic_value", "structure"]
    subitems: dict[str, SubitemGrade]
    score: float  # 재배점 기준 환산 점수 (academic_value: 54점 만점, structure: 26점 만점)


class JournalMetadata(BaseModel):
    journal_name: str
    abbreviation: str | None
    issn: str | None
    eissn: str | None
    major_research_field: str | None
    middle_research_field: str | None


class KCIEvalState(BaseModel):
    # 입력
    journal_meta: JournalMetadata  # 학술지 기본정보 (이름, 분야 등)
    paper: PaperInput  # 평가대상 논문 1편. MVP는 다수 논문 집계를 지원하지 않음.

    # 1단계 신청자격: UI 체크리스트, LLM 판단 없이 코드 로직으로만 판정
    stage1_checklist: dict  # {"발행규칙성": True, "심사위원수": True, ...} — UI에서 주입
    stage1_pass: Optional[bool]

    # ------------------------------------------------------
    # 2단계 체계평가
    # ------------------------------------------------------

    journal_publication_frequency_passed: bool
    journal_publication_frequency_score: float


    online_access_score_passed: bool
    online_access_score: float


    foreign_lang_score: float
    foreign_lang_passed: bool
    foreign_language_ratio: float
    foreign_language_reason: str


    total_stage2_score: float
    total_stage2_pass: bool

    
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
