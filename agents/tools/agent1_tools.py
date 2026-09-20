import os
import re
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient
from tenacity import retry

from state import (
    KCIEvalState,
    ForeignLanguageResult,
    PaperInput
)


# ==========================================================
# 환경 설정
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent  # agents/tools -> 프로젝트 루트
ENV_PATH = ROOT_DIR / ".env"

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


# ==========================================================
# Client
# ==========================================================

tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# ==========================================================
# Constants
# ==========================================================

FREQUENCY_PATTERNS = [
    r"발행\s*간기\s*[:|]?\s*연\s*(\d+)\s*회",
    r"간행\s*간기\s*[:|]?\s*연\s*(\d+)\s*회",
    r"발행\s*주기\s*[:|]?\s*연\s*(\d+)\s*회",
    r"발간\s*주기\s*[:|]?\s*연\s*(\d+)\s*회",
    r"발행\s*횟수\s*[:|]?\s*연\s*(\d+)\s*회",
    r"연\s*(\d+)\s*회",
]


FOREIGN_LANGUAGE_PROMPT = """
당신은 학술지에 게재된 논문 1편을 분석하여
주제어 및 논문 초록의 외국어화 여부를 판정하는
평가 에이전트입니다.

현재 평가는 학술지 전체가 아니라
입력된 논문 1편만을 대상으로 합니다.

다음 두 조건을 각각 확인하세요.

1. 외국어 주제어(Keywords)가 존재하는가
2. 외국어 초록(Abstract)이 존재하는가

두 조건이 모두 충족된 경우에만
foreign_language_ratio를 100으로 반환하세요.

둘 중 하나라도 충족되지 않으면
foreign_language_ratio를 0으로 반환하세요.

정보 자체를 확인할 수 없다면 임의로 값을 생성하지 마세요.

외국어 제목, 저자명, 소속기관명, 참고문헌, DOI,
학술지 영문명은 평가 근거로 사용하지 마세요.

반드시 입력된 논문 전문 텍스트만 근거로 사용하세요.

출력값:

- foreign_language_ratio
- foreign_language_reason
"""


# ==========================================================
# 공통 함수
# ==========================================================

def get_journal_meta(
    state: KCIEvalState,
) -> dict:
    """
    state에서 학술지 metadata를 가져온다.
    """

    if isinstance(state, dict):
        meta = state.get("journal_meta", {})
    else:
        meta = getattr(state, "journal_meta", {})

    if hasattr(meta, "model_dump"):
        return meta.model_dump()
    return meta or {}


def get_paper_raw_text(
    state: PaperInput,
) -> str:
    """
    state에서 평가 대상 논문의 raw_text를 가져온다.
    """

    if isinstance(state, dict):
        paper = state.get("paper", {})
    else:
        paper = getattr(state, "paper", {})

    if hasattr(paper, "model_dump"):
        paper = paper.model_dump()

    return (paper or {}).get("raw_text", "")


def normalize_issn(
    value: str | None,
) -> str:
    """
    None 등을 빈 문자열로 정규화한다.
    """

    if not value:
        return ""

    return value.strip()


# ==========================================================
# 1. 연간 학술지 발간 횟수
# ==========================================================

def calculate_tavily_relevance_score(
    result: dict,
    issn: str,
    eissn: str,
) -> float:
    """
    Tavily 기본 score에
    ISSN/eISSN/발행간기 관련 키워드 보너스를 추가한다.
    """

    content = (
        result
        .get("content", "")
        .lower()
    )

    tavily_score = result.get(
        "score",
        0.0,
    )

    bonus = 0.0

    if issn and issn.lower() in content:
        bonus += 2.0

    if eissn and eissn.lower() in content:
        bonus += 2.0

    normalized_content = re.sub(
        r"\s+",
        "",
        content,
    )

    if "발행간기" in normalized_content:
        bonus += 5.0

    if "발행주기" in normalized_content:
        bonus += 3.0

    if "frequency" in content:
        bonus += 2.0

    if "issuesperyear" in normalized_content:
        bonus += 3.0

    return tavily_score + bonus


def extract_annual_publication_count(
    content: str,
) -> int | None:
    """
    검색 결과 본문에서 연간 발간 횟수를 추출한다.

    찾지 못하면 None을 반환한다.
    """

    if not content:
        return None

    for pattern in FREQUENCY_PATTERNS:
        match = re.search(
            pattern,
            content,
            flags=re.IGNORECASE,
        )

        if match:
            return int(
                match.group(1)
            )

    # 영어 표현 대응
    normalized = re.sub(
        r"\s+",
        "",
        content.lower(),
    )

    issues_match = re.search(
        r"(\d+)issuesperyear",
        normalized,
    )

    if issues_match:
        return int(
            issues_match.group(1)
        )

    # 간기 명칭 대응
    frequency_map = {
        "monthly": 12,
        "bimonthly": 6,
        "quarterly": 4,
        "semiannual": 2,
        "semi-annual": 2,
        "annual": 1,
        "월간": 12,
        "격월간": 6,
        "계간": 4,
        "반년간": 2,
        "연간": 1,
    }

    for keyword, count in frequency_map.items():
        if keyword in content.lower():
            return count

    return None


def get_journal_publication_frequency_score(
    state: KCIEvalState,
) -> dict:
    """
    Tavily 검색을 이용하여 연간 학술지 발간 횟수를 확인하고
    체계평가 점수를 계산한다.

    검색 실패/추출 실패는 0점, False로 반환한다.
    """
    print("\n\n\n\n")
    print("=" * 80)
    print("[연간 학술지 발간횟수] 시작")
    print("=" * 80)

    journal_meta = get_journal_meta(
        state
    )

    issn = normalize_issn(
        journal_meta.get("issn")
    )

    eissn = normalize_issn(
        journal_meta.get("eissn")
    )

    journal_name = (
        journal_meta.get(
            "journal_name",
            "",
        )
        or ""
    )

    if tavily_client is None or not any([
        journal_name,
        issn,
        eissn,
    ]):
        return {
            "journal_publication_frequency_passed": False,
            "journal_publication_frequency_score": 0.0,
        }

    query = f"""
학술지의 연간 발행 횟수 또는 발행 간기를 찾으세요.

학술지명: {journal_name}
ISSN: {issn}
eISSN: {eissn}

발행간기, 발행주기, 연간 발행횟수,
issues per year, publication frequency 정보를 우선 확인하세요.
"""

    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
        )
    except Exception:
        return {
            "journal_publication_frequency_passed": False,
            "journal_publication_frequency_score": 0.0,
        }

    results = response.get(
        "results",
        [],
    )


    if not results:
        return {
            "journal_publication_frequency_passed": False,
            "journal_publication_frequency_score": 0.0,
        }

    sorted_results = sorted(
        results,
        key=lambda result: (
            calculate_tavily_relevance_score(
                result=result,
                issn=issn,
                eissn=eissn,
            )
        ),
        reverse=True,
    )

    annual_count: int | None = None

    # top 1만 보지 않고 상위 결과들을 순서대로 검사
    for result in sorted_results:
        content = result.get(
            "content",
            "",
        )

        annual_count = (
            extract_annual_publication_count(
                content
            )
        )

        if annual_count is not None:
            break

    if annual_count is None:
        return {
            "journal_publication_frequency_passed": False,
            "journal_publication_frequency_score": 0.0,
        }

    # TODO:
    # 실제 KCI 신청요강의 배점 기준과 반드시 재검증
    if annual_count >= 4:
        score = 3.0

    elif annual_count >= 3:
        score = 2.0

    elif annual_count >= 1:
        score = 1.0

    else:
        score = 0.0


    print("\n\n\n\n")
    print("=" * 80)
    print("[연간 학술지 발간횟수] 종료")
    print("=" * 80)

    print(f"\njournal_publication_frequency_passed : {score > 0}")
    print(f"\njournal_publication_frequency_score : {score}")
    

    return {
        "journal_publication_frequency_passed": (
            score > 0
        ),
        "journal_publication_frequency_score": score,
    }


# ==========================================================
# 2. 학술지 및 수록 논문의 온라인 접근성
# ==========================================================

def get_online_access_score(
    state: KCIEvalState,
) -> dict:

    print("=" * 80)
    print("[학술지 수록 및 수록 논문의 온라인 접근성] 시작")
    print("=" * 80)

    online_access_score = 0.0
    online_access_score_passed = False

    try:
        journal_meta = get_journal_meta(state)

        issn = normalize_issn(
            journal_meta.get("issn")
        )

        if not issn:
            return {
                "online_access_score": 0.0,
                "online_access_score_passed": False,
            }

        try:
            response = requests.get(
                f"{OPEN_ALEX_URL}issn:{issn}",
                params={
                    "api_key": OPEN_ALEX_API_KEY,
                },
                timeout=10,
            )

            response.raise_for_status()

        except requests.RequestException as error:
            print("OPEN ALEX API Error:", error)

            return {
                "online_access_score": 0.0,
                "online_access_score_passed": False,
            }

        data = response.json()

        homepage_url = data.get("homepage_url")
        is_oa = data.get("is_oa")
        last_publication_year = data.get(
            "last_publication_year"
        )

        if not homepage_url:
            return {
                "online_access_score": 0.0,
                "online_access_score_passed": False,
            }

        if not is_oa:
            return {
                "online_access_score": 0.0,
                "online_access_score_passed": False,
            }

        if last_publication_year is None:
            return {
                "online_access_score": 0.0,
                "online_access_score_passed": False,
            }

        try:
            last_publication_year = int(
                last_publication_year
            )
        except (TypeError, ValueError):
            return {
                "online_access_score": 0.0,
                "online_access_score_passed": False,
            }

        current_year = datetime.now().year

        years_since_last_publication = (
            current_year
            - last_publication_year
        )

        if years_since_last_publication >= 9:
            online_access_score = 15.0

        elif years_since_last_publication >= 6:
            online_access_score = 12.0

        elif years_since_last_publication >= 4:
            online_access_score = 9.0

        elif years_since_last_publication >= 1:
            online_access_score = 3.0

        else:
            online_access_score = 0.0

        return {
            "online_access_score": online_access_score,
            "online_access_score_passed": (
                online_access_score > 0
            ),
        }

    finally:
        print("=" * 80)
        print("[학술지 수록 및 수록 논문의 온라인 접근성] 종료")
        print("=" * 80)

        print(f"online_access_score : {online_access_score}")
        print(f"online_access_score_passed : {online_access_score_passed or (online_access_score > 0)}")



# ==========================================================
# 3. 주제어 및 논문 초록의 외국어화
# ==========================================================

def get_keyword_abstract_foreign_language_score(
    state: KCIEvalState,
) -> dict:
    """
    논문 1편의 raw_text를 Gemini가 분석하여
    외국어 Keywords와 Abstract가 모두 존재하는지 판정한다.

    """
    print("\n\n\n\n")
    print("=" * 80)
    print("[주제어 및 논문 초록의 외국화] 시작")
    print("=" * 80)

    raw_text = get_paper_raw_text(
        state
    )

    if not raw_text.strip():
        return {
            "foreign_language_ratio": 0.0,
            "foreign_language_reason": (
                "평가할 논문 전문 텍스트가 없습니다."
            ),
            "foreign_lang_score": 0.0,
            "foreign_lang_passed": False,
        }

    if gemini_client is None:
        return {
            "foreign_language_ratio": 0.0,
            "foreign_language_reason": "GEMINI_API_KEY가 없어 외국어화 평가를 건너뛰었습니다.",
            "foreign_lang_score": 0.0,
            "foreign_lang_passed": False,
        }

    try:
        interaction = (
            gemini_client
            .interactions
            .create(
                model=MODEL_NAME,
                system_instruction=(
                    FOREIGN_LANGUAGE_PROMPT
                ),
                input=raw_text,
                generation_config={
                    "thinking_level": "medium",
                },
                response_format={
                    "type": "text",
                    "mime_type": (
                        "application/json"
                    ),
                    "schema": (
                        ForeignLanguageResult
                        .model_json_schema()
                    ),
                },
            )
        )

        result = (
            ForeignLanguageResult
            .model_validate_json(
                interaction.output_text
            )
        )

    except Exception as error:
        return {
            "foreign_language_ratio": 0.0,
            "foreign_language_reason": (
                f"외국어화 판정 실패: {error}"
            ),
            "foreign_lang_score": 0.0,
            "foreign_lang_passed": False,
        }

    foreign_language_ratio = (
        result.foreign_language_ratio
    )

    foreign_language_reason = (
        result.foreign_language_reason
    )


    if foreign_language_ratio == 100:
        foreign_lang_score = 20
        foreign_lang_passed = True

    elif foreign_language_ratio >= 90:
        foreign_lang_score = 15
        foreign_lang_passed = True

    elif foreign_language_ratio >= 80:
        foreign_lang_score = 10
        foreign_lang_passed = True

    elif foreign_language_ratio >= 70:
        foreign_lang_score = 5
        foreign_lang_passed = True

    else:
        foreign_lang_score = 0
        foreign_lang_passed = False

    print("\n\n\n\n")
    print("=" * 80)
    print("[주제어 및 논문 초록의 외국화] 종료")
    print("=" * 80)

    print(f"\nforeign_language_ratio : {foreign_language_ratio}")
    print(f"\nforeign_language_reason : {foreign_language_reason}")
    print(f"\nforeign_lang_score : {foreign_lang_score}")
    print(f"\nfforeign_lang_passed : {foreign_lang_passed}")
    

    return {
        "foreign_language_ratio": (
            foreign_language_ratio
        ),
        "foreign_language_reason": (
            foreign_language_reason
        ),
        "foreign_lang_score": (
            foreign_lang_score
        ),
        "foreign_lang_passed": (
            foreign_lang_passed
        ),
    }




