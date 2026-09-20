"""
Agent3 단독 테스트

목적:
- 원본 논문과 Synthetic A/B/C를 Agent3에 입력한다.
- Agent3가 "논문집의 구성과 체제의 완전성 및 가독성"을
  의도한 방향으로 평가하는지 확인한다.

기대 결과:
- Original     : 높은 점수
- Synthetic A  : Original과 유사한 점수
- Synthetic B  : 점수 하락
- Synthetic C  : 점수 하락
"""

from pathlib import Path

import pdfplumber

from agents.agent3_structure import agent3_node



# 테스트 파일 경로
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

TEST_PAPERS = {
    "Original": DATA_DIR / "Real_Paper.pdf",
    "Synthetic A": DATA_DIR / "Synthetic_A_AcademicValue_Degraded.pdf",
    "Synthetic B": DATA_DIR / "Synthetic_B_StructureReadability_Degraded_v2.pdf",
    "Synthetic C": DATA_DIR / "Synthetic_C_Combined_Degraded_v2.pdf",
}


# PDF 텍스트 추출
def extract_pdf_text(pdf_path: Path) -> str:
    """PDF 전체 페이지에서 텍스트를 추출한다."""

    page_texts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                page_texts.append(text)

    return "\n".join(page_texts)



# Agent3 단일 테스트
def run_agent3_test(name: str, pdf_path: Path) -> dict:
    """PDF 하나를 Agent3에 입력하고 평가 결과를 반환한다."""

    print("\n")
    print("=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)

    # PDF -> raw text
    paper_text = extract_pdf_text(pdf_path)

    print(f"파일: {pdf_path.name}")
    print(f"추출 문자 수: {len(paper_text):,}")

    # Agent3가 사용하는 최소 State 구성
    state = {
        "paper": {
            "paper_id": name,
            "raw_text": paper_text,
        }
    }

    # Agent3 실행
    result = agent3_node(state)

    # Agent3는 stage3_results에 list 형태로 결과를 반환
    agent_result = result["stage3_results"][0]

    print("\n[Agent3 평가 결과]")

    for subitem, evaluation in agent_result["subitems"].items():
        print("\n" + "-" * 80)
        print(f"[{subitem}]")
        print(f"등급: {evaluation['grade']}")
        print(f"근거: {evaluation['rationale']}")

    print("\n" + "-" * 80)
    print(f"총점: {agent_result['score']} / 26")

    return agent_result



# 전체 테스트
def main():
    results = {}

    for name, pdf_path in TEST_PAPERS.items():

        # 파일이 없으면 해당 테스트는 건너뜀
        if not pdf_path.exists():
            print("\n")
            print("=" * 80)
            print(f"[SKIP] {name}")
            print(f"파일을 찾을 수 없습니다: {pdf_path}")
            print("=" * 80)
            continue

        try:
            results[name] = run_agent3_test(
                name=name,
                pdf_path=pdf_path,
            )

        except Exception as error:
            print("\n")
            print("=" * 80)
            print(f"[ERROR] {name}")
            print("=" * 80)
            print(error)

    
    # 최종 점수 비교
    print("\n")
    print("=" * 80)
    print("Agent3 점수 비교")
    print("=" * 80)

    if not results:
        print("정상적으로 완료된 테스트가 없습니다.")
        return

    for name, result in results.items():
        print(
            f"{name:<15}"
            f"{result['score']:>6.1f} / 26"
        )

 
    # 기대 패턴 안내
    print("\n")
    print("=" * 80)
    print("기대 패턴")
    print("=" * 80)
    print("Original ≈ Synthetic A > Synthetic B")
    print("Original ≈ Synthetic A > Synthetic C")
    print()
    print(
        "Synthetic A에서 점수가 크게 하락하면 "
        "Agent3가 Agent2 영역까지 과도하게 평가하고 있을 가능성이 있습니다."
    )
    print(
        "Synthetic B/C에서 점수가 충분히 하락하지 않으면 "
        "Agent3 프롬프트의 구성·가독성 평가 기준을 조정할 필요가 있습니다."
    )


if __name__ == "__main__":
    main()