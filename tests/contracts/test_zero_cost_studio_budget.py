"""Regression tests for the studio's strict zero-cost default."""

from __future__ import annotations

import unittest
from pathlib import Path

from lib.config_model import BudgetMode, OpenMontageConfig
from tools.cost_tracker import ApprovalRequiredError, BudgetExceededError, CostTracker


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

    def _tracker_from_repository_config(self) -> CostTracker:
        budget = OpenMontageConfig.load(
            Path(__file__).resolve().parents[2] / "config.yaml"
        ).budget
        return CostTracker(
            budget_total_usd=budget.total_usd,
            reserve_pct=budget.reserve_pct,
            single_action_approval_usd=budget.single_action_approval_usd,
            require_approval_for_new_paid_tool=budget.require_approval_for_new_paid_tool,
            mode=budget.mode,
        )

    def test_repository_config_refuses_paid_reservation_as_budget_exceeded(self) -> None:
        tracker = self._tracker_from_repository_config()
        entry_id = tracker.estimate("paid_provider", "paid_operation", 0.01)

        with self.assertRaises(BudgetExceededError):
            tracker.reserve(entry_id)
        self.assertEqual(tracker.budget_reserved_usd, 0.0)

    def test_approving_the_tool_cannot_unlock_spend_under_zero_cap(self) -> None:
        tracker = self._tracker_from_repository_config()
        tracker.approve_tool("paid_provider")
        tracker.single_action_approval_usd = 1_000.0
        entry_id = tracker.estimate("paid_provider", "paid_operation", 0.50)

        with self.assertRaises(BudgetExceededError):
            tracker.reserve(entry_id)
        self.assertEqual(tracker.budget_reserved_usd, 0.0)

    def test_zero_cost_local_operation_is_still_reservable(self) -> None:
        tracker = self._tracker_from_repository_config()
        entry_id = tracker.estimate("ffmpeg_edit", "trim", 0.0)

        tracker.reserve(entry_id)
        tracker.reconcile(entry_id, 0.0)
        self.assertEqual(tracker.budget_spent_usd, 0.0)

    def test_cap_mode_within_budget_still_requires_approval(self) -> None:
        tracker = CostTracker(
            budget_total_usd=5.0,
            reserve_pct=0.0,
            single_action_approval_usd=0.50,
            require_approval_for_new_paid_tool=True,
            mode=BudgetMode.CAP,
        )
        over_threshold = tracker.estimate("paid_provider", "op", 1.00)
        with self.assertRaises(ApprovalRequiredError):
            tracker.reserve(over_threshold)

        new_tool = tracker.estimate("paid_provider", "op", 0.10)
        with self.assertRaises(ApprovalRequiredError):
            tracker.reserve(new_tool)

    def test_warn_mode_keeps_approval_gate_before_warning(self) -> None:
        tracker = CostTracker(
            budget_total_usd=0.0,
            reserve_pct=0.0,
            single_action_approval_usd=0.0,
            require_approval_for_new_paid_tool=False,
            mode=BudgetMode.WARN,
        )
        entry_id = tracker.estimate("paid_provider", "op", 0.01)
        with self.assertRaises(ApprovalRequiredError):
            tracker.reserve(entry_id)

        tracker.single_action_approval_usd = 1.0
        tracker.reserve(entry_id)
        entry = tracker.entries[0]
        self.assertTrue(entry["budget_warning"])


if __name__ == "__main__":
    unittest.main()
