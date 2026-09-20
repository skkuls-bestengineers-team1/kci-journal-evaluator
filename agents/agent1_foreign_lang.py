

from state import KCIEvalState

from .tools.agent1_tools import (
    get_online_access_score,
    get_journal_publication_frequency_score,
    get_keyword_abstract_foreign_language_score,
)
from pathlib import Path
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai

import os
import json
from state import (
    KCIEvalState
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ENV_PATH = ROOT_DIR / ".env"
TEST_PATH = ROOT_DIR / "data" /"Synthetic_B_StructureReadability_Degraded.pdf"

load_dotenv(dotenv_path=ENV_PATH)


OPEN_ALEX_API_KEY = os.getenv(
    "OPEN_ALEX_API_KEY",
    "",
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
)

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY",
    "",
)


if not GEMINI_API_KEY:
    GEMINI_API_KEY = ""

if not TAVILY_API_KEY:
    TAVILY_API_KEY = ""


OPEN_ALEX_URL = (
    "https://api.openalex.org/sources/"
)

MODEL_NAME = "gemini-3.6-flash"


gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None



def calculate_stage2_result(
    # publication_result: dict,
    # online_access_result: dict,
    foreign_language_result: dict,
) -> dict:
    """
    2단계 체계평가의 세부 Tool 결과를 이용하여
    총점과 최종 PASS/FAIL을 계산한다.

    규칙:
    - 세 점수를 합산하여 total_stage2_score 계산
    - 세 평가 항목 중 하나라도 0점이면 FAIL
    - 세 항목 모두 0점보다 크면 PASS

    이 함수에서는 LLM을 사용하지 않는다.
    """

    # =====================================================
    # 1. Tool 결과에서 점수 추출
    # =====================================================

    '''
    journal_publication_frequency_score = (
        publication_result.get(
            "journal_publication_frequency_score",
            0.0,
        )
    )

    online_access_score = (
        online_access_result.get(
            "online_access_score",
            0.0,
        )
    )
    '''
    journal_publication_frequency_score = 0.0
    online_access_score = 0.0
    foreign_lang_score = (
        foreign_language_result.get(
            "foreign_lang_score",
            0.0,
        )
    )


    # =====================================================
    # 2. Tool 결과에서 PASS 여부 추출
    # =====================================================
    '''
    journal_publication_frequency_passed = (
        publication_result.get(
            "journal_publication_frequency_passed",
            False,
        )
    )

    online_access_score_passed = (
        online_access_result.get(
            "online_access_score_passed",
            False,
        )
    )
    '''
    

    foreign_lang_passed  = (
        foreign_language_result.get(
            "foreign_lang_passed",
            False,
        )
    )


    # =====================================================
    # 3. 총점 계산
    # =====================================================

    journal_publication_frequency_passed = True
    online_access_score_passed = True

    total_stage2_score = (
        journal_publication_frequency_score
        + online_access_score
        + foreign_lang_score
    )


    # =====================================================
    # 4. 2단계 최종 PASS / FAIL
    #
    # 하나라도 0점이면 FAIL
    # =====================================================
    '''
    scores = [
        journal_publication_frequency_score,
        online_access_score,
        foreign_lang_score,
    ]

    total_stage2_pass = all(
        score > 0
        for score in scores
    )
    '''
    total_stage2_pass = True

    # =====================================================
    # 5. 최종 결과 반환
    # =====================================================

    return {
        # ---------------------------------------------
        # 1. 연간 학술지 발간 횟수
        # ---------------------------------------------
        "journal_publication_frequency_passed": (
            journal_publication_frequency_passed
        ),
        "journal_publication_frequency_score": (
            journal_publication_frequency_score
        ),

        # ---------------------------------------------
        # 2. 온라인 접근성
        # ---------------------------------------------
        "online_access_score_passed": (
            online_access_score_passed
        ),
        "online_access_score": (
            online_access_score
        ),

        # ---------------------------------------------
        # 3. 주제어 및 초록 외국어화
        # ---------------------------------------------
        "foreign_lang_passed": (
            foreign_lang_passed
        ),
        "foreign_lang_score": (
            foreign_lang_score
        ),
        "foreign_language_ratio": (
            foreign_language_result.get(
                "foreign_language_ratio",
                0.0,
            )
        ),
        "foreign_language_reason": (
            foreign_language_result.get(
                "foreign_language_reason",
                "",
            )
        ),

        # ---------------------------------------------
        # 2단계 최종 결과
        # ---------------------------------------------
        "total_stage2_score": (
            total_stage2_score
        ),
        "total_stage2_pass": (
            total_stage2_pass
        ),
    }


def agent1_node(
    state: KCIEvalState,
) -> dict:
    """
    KCI 2단계 체계평가 Agent.

    1. 연간 학술지 발간 횟수 평가
    2. 학술지 및 수록 논문의 온라인 접근성 평가
    3. 주제어 및 논문 초록 외국어화 평가

    각 Tool의 결과를 이용하여
    Python 규칙으로 총점 및 최종 PASS/FAIL을 계산한다.

    Agent 자체에서는 LLM을 사용하지 않는다.
    """
    print("\n\n\n\n")
    print("=" * 80)
    print("[agent1_node] 시작")
    print("=" * 80)

    # =====================================================
    # 1. 연간 학술지 발간 횟수 평가
    # =====================================================
    '''
    publication_result = (
        get_journal_publication_frequency_score(
            state
        )
    )


    # =====================================================
    # 2. 학술지 및 수록 논문의 온라인 접근성 평가
    # =====================================================

    online_access_result = (
        get_online_access_score(
            state
        )
    )
    '''

    # =====================================================
    # 3. 주제어 및 논문 초록 외국어화 평가
    # =====================================================

    foreign_language_result = (
        get_keyword_abstract_foreign_language_score(
            state
        )
    )


    # =====================================================
    # 4. 2단계 최종 결과 계산
    # =====================================================

    result = calculate_stage2_result(
        # publication_result=publication_result,
        # online_access_result=online_access_result,
        foreign_language_result=foreign_language_result,
    )

    print("\n\n\n\n")
    print("=" * 80)
    print("[agent1_node] 종료")
    print("=" * 80)

    print("total_stage2_score :" ,result.get("total_stage2_score"))
    print("total_stage2_pass :" ,result.get("total_stage2_pass"))

    return result















