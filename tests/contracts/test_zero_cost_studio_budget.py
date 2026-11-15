"""Regression tests for the studio's strict zero-cost default."""

from __future__ import annotations

import unittest
from pathlib import Path

from lib.config_model import BudgetMode, OpenMontageConfig
from tools.cost_tracker import BudgetExceededError, CostTracker


class ZeroCostStudioBudgetTests(unittest.TestCase):
    def test_repository_default_budget_is_hard_zero_cap(self) -> None:
        config = OpenMontageConfig.load(Path(__file__).resolve().parents[2] / "config.yaml")

        self.assertEqual(config.budget.mode, BudgetMode.CAP)
        self.assertEqual(config.budget.total_usd, 0.0)
        self.assertEqual(config.budget.reserve_pct, 0.0)

    def test_positive_cost_cannot_be_reserved_under_zero_budget(self) -> None:
        tracker = CostTracker(
            budget_total_usd=0.0,
            reserve_pct=0.0,
            single_action_approval_usd=0.0,
            require_approval_for_new_paid_tool=False,
            mode=BudgetMode.CAP,
        )
        entry_id = tracker.estimate("paid_provider", "paid_operation", 0.01)

        with self.assertRaises(BudgetExceededError):
            tracker.reserve(entry_id)

        self.assertEqual(tracker.budget_reserved_usd, 0.0)
        self.assertEqual(tracker.budget_spent_usd, 0.0)


if __name__ == "__main__":
    unittest.main()
