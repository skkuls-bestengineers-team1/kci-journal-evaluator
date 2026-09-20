"""LangGraph 게이트 단독 테스트"""

import unittest

from config import STAGE3_PASS_THRESHOLD
from graph import (
    build_graph,
    stage1_gate,
    stage2_gate,
    stage3_aggregator,
)


PASSING_CHECKLIST = {
    "발행규칙성": True,
    "심사위원수": True,
    "연구윤리": True,
    "투고다양성": True,
    "기본체계": True,
}


class GraphGateTests(unittest.TestCase):
    def test_stage1_pass(self):
        result = stage1_gate({"stage1_checklist": PASSING_CHECKLIST})
        self.assertEqual(result, {"stage1_pass": True})

    def test_stage1_fail_lists_missing_items(self):
        checklist = dict(PASSING_CHECKLIST)
        checklist["연구윤리"] = False
        result = stage1_gate({"stage1_checklist": checklist})
        self.assertFalse(result["stage1_pass"])
        self.assertEqual(result["final_verdict"], "탈락")
        self.assertIn("연구윤리", result["rejection_reason"])

    def test_stage2_fail_on_zero(self):
        result = stage2_gate({"total_stage2_score": 0, "total_stage2_pass": False})
        self.assertEqual(result["final_verdict"], "탈락")

    def test_stage2_pass_on_full_score(self):
        result = stage2_gate({"total_stage2_score": 20, "total_stage2_pass": True})
        self.assertEqual(result, {})

    def test_stage3_fail_below_threshold(self):
        result = stage3_aggregator(
            {
                "total_stage2_score": 20,
                "stage3_results": [
                    {"agent": "academic_value", "subitems": {}, "score": 30},
                    {"agent": "structure", "subitems": {}, "score": 10},
                ],
            }
        )
        self.assertEqual(result["stage3_total"], 40.0)
        self.assertLess(result["stage3_total"], STAGE3_PASS_THRESHOLD)
        self.assertFalse(result["stage3_pass"])
        self.assertEqual(result["final_verdict"], "탈락")
        self.assertEqual(result["final_score"], 60.0)

    def test_stage3_pass_at_or_above_threshold(self):
        result = stage3_aggregator(
            {
                "total_stage2_score": 20,
                "stage3_results": [
                    {"agent": "academic_value", "subitems": {}, "score": 40},
                    {"agent": "structure", "subitems": {}, "score": 20},
                ],
            }
        )
        self.assertEqual(result, {"stage3_total": 60.0, "stage3_pass": True})

    def test_build_graph_compiles(self):
        graph = build_graph()
        self.assertIsNotNone(graph)


if __name__ == "__main__":
    unittest.main()
