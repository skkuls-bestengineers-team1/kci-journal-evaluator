"""
Agent2 단독 테스트

목적:
- 원본 논문과 Synthetic A/B/C를 Agent2에 입력한다.
- Agent2가 "게재논문의 학술적 가치와 성과"를
  의도한 방향으로 평가하는지 확인한다.

기대 결과 (data/README_합성데이터_설계_v2.md 기준):
- Original     : 높은 점수
- Synthetic A  : 점수 하락 (학술적 가치/성과 저하)
- Synthetic B  : Original과 유사한 점수 (구성/가독성만 저하)
- Synthetic C  : 점수 하락 (복합 저하)
"""

from pathlib import Path

import pdfplumber

from agents.agent2_academic_value import agent2_node


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# 파일명이 버전(_v2)에 따라 다를 수 있어 후보를 순서대로 탐색한다.
TEST_PAPERS = {
    "Original": ["Real_Paper.pdf"],
    "Synthetic A": ["Synthetic_A_AcademicValue_Degraded.pdf"],
    "Synthetic B": [
        "Synthetic_B_StructureReadability_Degraded_v2.pdf",
        "Synthetic_B_StructureReadability_Degraded.pdf",
    ],
    "Synthetic C": [
        "Synthetic_C_Combined_Degraded_v2.pdf",
        "Synthetic_C_Combined_Degraded.pdf",
    ],
}

# 합성 논문 원문(LangGraph 기반 CrewAI 다중 에이전트 아키텍처)에 맞춘 학술지 분야
JOURNAL_META = {
    "journal_name": "한국정보통신학회논문지",
    "major_research_field": "공학",
    "middle_research_field": "전자/정보통신공학",
}


def find_pdf(candidates: list[str]) -> Path | None:
    for filename in candidates:
        path = DATA_DIR / filename
        if path.exists():
            return path
    return None


def extract_pdf_text(pdf_path: Path) -> str:
    """PDF 전체 페이지에서 텍스트를 추출한다."""

    page_texts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                page_texts.append(text)

    return "\n".join(page_texts)


def run_agent2_test(name: str, pdf_path: Path) -> dict:
    """PDF 하나를 Agent2에 입력하고 평가 결과를 반환한다."""

    print("\n")
    print("=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)

    paper_text = extract_pdf_text(pdf_path)

    print(f"파일: {pdf_path.name}")
    print(f"추출 문자 수: {len(paper_text):,}")

    state = {
        "journal_meta": JOURNAL_META,
        "paper": {
            "paper_id": name,
            "raw_text": paper_text,
        },
    }

    result = agent2_node(state)

    agent_result = result["stage3_results"][0]

    print("\n[Agent2 평가 결과]")

    for subitem, evaluation in agent_result["subitems"].items():
        print("\n" + "-" * 80)
        print(f"[{subitem}]")
        print(f"등급: {evaluation['grade']}")
        print(f"근거: {evaluation['rationale']}")

    print("\n" + "-" * 80)
    print(f"총점: {agent_result['score']} / 54")

    return agent_result


def main():
    results = {}

    for name, candidates in TEST_PAPERS.items():
        pdf_path = find_pdf(candidates)

        if pdf_path is None:
            print("\n")
            print("=" * 80)
            print(f"[SKIP] {name}")
            print(f"파일을 찾을 수 없습니다: {candidates}")
            print("=" * 80)
            continue

        try:
            results[name] = run_agent2_test(
                name=name,
                pdf_path=pdf_path,
            )

        except Exception as error:
            print("\n")
            print("=" * 80)
            print(f"[ERROR] {name}")
            print("=" * 80)
            print(repr(error))

    print("\n")
    print("=" * 80)
    print("Agent2 점수 비교")
    print("=" * 80)

    if not results:
        print("정상적으로 완료된 테스트가 없습니다.")
        return

    print(f"{'':<15}{'recog':>7}{'suit':>7}{'topic':>7}{'총점':>10}")

    for name, result in results.items():
        grades = result["subitems"]
        print(
            f"{name:<15}"
            f"{grades['recognition']['grade']:>7}"
            f"{grades['suitability']['grade']:>7}"
            f"{grades['topic_fit']['grade']:>7}"
            f"{result['score']:>7.1f} / 54"
        )

    print("\n")
    print("=" * 80)
    print("기대 패턴")
    print("=" * 80)
    print("Original ≈ Synthetic B > Synthetic A ≈ Synthetic C")
    print()
    print(
        "Synthetic B에서 점수가 크게 하락하면 "
        "Agent2가 Agent3 영역(구성/가독성)까지 평가하고 있을 가능성이 있습니다."
    )
    print(
        "Synthetic A/C에서 점수가 충분히 하락하지 않으면 "
        "Agent2 프롬프트의 학술적 가치 평가 기준을 점검할 필요가 있습니다."
    )


if __name__ == "__main__":
    main()
