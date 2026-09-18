"""배점 상수 및 임계값 정의.

이름 규칙: 두 개의 "80점"이 서로 다른 의미이므로 반드시 상수명으로 구분해서 참조할 것.
- STAGE3_MAX_SCORE = 3단계(내용평가) 재배점 만점 (54+26=80)
- FINAL_PASS_THRESHOLD = 4단계 종합심의 합격 기준 점수 (100점 만점 중 80점)
"""

import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3.7-flash")

# --- 2단계 체계평가 ---
# 원본 3개 항목 중 "주제어 및 초록 외국어화"만 구현, 나머지 2개 항목 생략분을 흡수해
# 2단계 배점(20점) 전체를 이 항목 혼자 대표하도록 재배점했다 (원배점 2점 -> 20점).
STAGE2_MAX_SCORE = 20

# --- 3단계 내용평가 ---
# Agent2: 게재논문의 학술적 가치와 성과 (원배점 20점 -> 54점)
# 원본 4개 세부항목 중 "편집위원회 활동"(원 3점)은 논문 본문만으로 판단 불가하여 제외.
# 나머지 3개 항목(합 17점)을 54점 기준으로 비례 재배점.
ACADEMIC_VALUE_MAX_SCORE = 54
ACADEMIC_VALUE_SUBSCORES = {
    "recognition": round(3 / 17 * ACADEMIC_VALUE_MAX_SCORE, 1),  # 인지도 및 활용도 (원 3점) ≈ 9.5
    "suitability": round(10 / 17 * ACADEMIC_VALUE_MAX_SCORE, 1),  # KCI 등재지로서의 학술적 가치·적합성 (원 10점) ≈ 31.8
    "topic_fit": round(4 / 17 * ACADEMIC_VALUE_MAX_SCORE, 1),  # 학술지 주제와의 부합도 (원 4점) ≈ 12.7
}

# Agent3: 논문집의 구성과 체제의 완전성 및 가독성 (원배점 9점 -> 26점)
STRUCTURE_MAX_SCORE = 26
STRUCTURE_SUBSCORES = {
    "completeness": round(4 / 9 * STRUCTURE_MAX_SCORE, 1),  # 구성과 체제의 완전성 (원 4점) ≈ 11.6
    "readability": round(3 / 9 * STRUCTURE_MAX_SCORE, 1),  # 가독성 (원 3점) ≈ 8.7
    "affiliation_clarity": round(2 / 9 * STRUCTURE_MAX_SCORE, 1),  # 저자 소속·직위 표기 명확성 (원 2점) ≈ 5.8
}
# 참고: 위 세부항목 반올림 때문에 합계가 26.0에서 ±0.1 오차가 날 수 있음 (허용 오차).

STAGE3_MAX_SCORE = ACADEMIC_VALUE_MAX_SCORE + STRUCTURE_MAX_SCORE  # 80

# 3단계 배점과락 기준 (70% 미만이면 탈락)
STAGE3_PASS_RATIO = 0.7
STAGE3_PASS_THRESHOLD = STAGE3_MAX_SCORE * STAGE3_PASS_RATIO  # 56점

# --- 4단계 종합심의 ---
FINAL_MAX_SCORE = STAGE2_MAX_SCORE + STAGE3_MAX_SCORE  # 100
FINAL_PASS_THRESHOLD = 80  # 2+3단계 합산 100점 중 80점 이상이면 "등재후보 선정"

# 등급 -> 배점 비율 환산표 (원본 방식: 각 등급은 구간이나, 구간 하한값으로 단순화해서 사용)
GRADE_TO_RATIO = {
    "A": 1.00,
    "B": 0.90,
    "C": 0.80,
    "D": 0.70,
    "E": 0.60,
    "F": 0.00,
}
