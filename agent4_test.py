"""
Agent4 단독 테스트

목적:
- 점수 합산과 합격 기준(80점) 판정이 코드 하드룰로 동작하는지 확인한다.
- LLM 없이도 템플릿 코멘트가 생성되는지 확인한다.

기대 결과:
- 20 + 65 = 85.0 -> 등재후보 선정
- 20 + 56 = 76.0 -> 탈락
- 20 + 60 = 80.0 -> 등재후보 선정 (기준 이상)
"""

import unittest
from unittest.mock import patch

from agents.agent4_final_decision import (
    agent4_node,
    compute_final_decision,
    generate_final_comment,
    render_template_comment,
)


def _sample_state(
    stage2_score: float,
    stage3_total: float,
    *,
    foreign_lang_satisfied: bool = True,
    extraction_failed: bool = False,
) -> dict:
    return {
        "stage2_score": stage2_score,
        "stage3_total": stage3_total,
        "foreign_lang_satisfied": foreign_lang_satisfied,
        "foreign_lang_extraction_failed": extraction_failed,
        "stage3_results": [
            {
                "agent": "academic_value",
                "subitems": {
                    "recognition": {
                        "grade": "B",
                        "rationale": "해당 분야 선행연구와의 연결이 분명하다.",
                    },
                    "suitability": {
                        "grade": "C",
                        "rationale": "등재지 수준의 학술적 기여는 보통이다.",
                    },
                    "topic_fit": {
                        "grade": "A",
                        "rationale": "학술지 주제와 잘 부합한다.",
                    },
                },
                "score": 42.0,
            },
            {
                "agent": "structure",
                "subitems": {
                    "completeness": {
                        "grade": "B",
                        "rationale": "서론-방법-결과-결론 구성이 갖추어져 있다.",
                    },
                    "readability": {
                        "grade": "C",
                        "rationale": "일부 문단의 흐름이 끊긴다.",
                    },
                    "affiliation_clarity": {
                        "grade": "A",
                        "rationale": "저자 소속과 직위가 명확하다.",
                    },
                },
                "score": 23.0,
            },
        ],
    }


class Agent4DecisionTests(unittest.TestCase):
    def test_pass_above_threshold(self):
        score, verdict = compute_final_decision(20, 65)
        self.assertEqual(score, 85.0)
        self.assertEqual(verdict, "등재후보 선정")

    def test_fail_below_threshold(self):
        score, verdict = compute_final_decision(20, 56)
        self.assertEqual(score, 76.0)
        self.assertEqual(verdict, "탈락")

    def test_pass_exactly_threshold(self):
        score, verdict = compute_final_decision(20, 60)
        self.assertEqual(score, 80.0)
        self.assertEqual(verdict, "등재후보 선정")

    def test_rounds_to_one_decimal(self):
        score, verdict = compute_final_decision(20, 59.66)
        self.assertEqual(score, 79.7)
        self.assertEqual(verdict, "탈락")

    def test_missing_stage2_score_raises(self):
        with self.assertRaises(ValueError):
            agent4_node({"stage3_total": 60})

    def test_missing_stage3_total_raises(self):
        with self.assertRaises(ValueError):
            agent4_node({"stage2_score": 20})

    def test_template_comment_includes_scores_and_verdict(self):
        state = _sample_state(20, 65)
        comment = render_template_comment(state, 85.0, "등재후보 선정")
        self.assertIn("85.0", comment)
        self.assertIn("등재후보", comment)
        self.assertIn("20", comment)
        self.assertIn("65", comment)
        self.assertIn("학술적 가치", comment)

    def test_llm_failure_falls_back_to_template(self):
        state = _sample_state(20, 56)
        with patch(
            "agents.agent4_final_decision._generate_llm_comment",
            side_effect=RuntimeError("no api key"),
        ):
            comment = generate_final_comment(state, 76.0, "탈락")
        self.assertIn("탈락", comment)
        self.assertIn("템플릿으로 대체", comment)

    def test_node_returns_required_fields(self):
        state = _sample_state(20, 65)
        with patch(
            "agents.agent4_final_decision.generate_final_comment",
            return_value="테스트 코멘트",
        ):
            result = agent4_node(state)

        self.assertEqual(result["final_score"], 85.0)
        self.assertEqual(result["final_verdict"], "등재후보 선정")
        self.assertEqual(result["final_comment"], "테스트 코멘트")
        self.assertEqual(set(result.keys()), {
            "final_score",
            "final_verdict",
            "final_comment",
        })


if __name__ == "__main__":
    unittest.main()
