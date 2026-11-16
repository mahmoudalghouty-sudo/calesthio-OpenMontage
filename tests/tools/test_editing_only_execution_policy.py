from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from tools.base_tool import (
    BaseTool,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolTier,
)


class LocalEditTool(BaseTool):
    name = "test_local_edit"
    tier = ToolTier.CORE
    runtime = ToolRuntime.LOCAL
    resource_profile = ResourceProfile(network_required=False)

    def execute(self, inputs: dict) -> ToolResult:
        return ToolResult(success=True, data={"ran": True})


class PaidGenerationTool(BaseTool):
    name = "test_paid_generation"
    tier = ToolTier.GENERATE
    runtime = ToolRuntime.API
    resource_profile = ResourceProfile(network_required=True)

    def execute(self, inputs: dict) -> ToolResult:
        raise AssertionError("blocked tool must never execute")


class NetworkAnalysisTool(BaseTool):
    name = "test_network_analysis"
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    resource_profile = ResourceProfile(network_required=True)

    def execute(self, inputs: dict) -> ToolResult:
        raise AssertionError("network tool must never execute")


class RemoteVideoAnalysisTool(BaseTool):
    name = "video_analyzer"
    tier = ToolTier.ANALYZE
    runtime = ToolRuntime.LOCAL
    resource_profile = ResourceProfile(network_required=False)

    def execute(self, inputs: dict) -> ToolResult:
        return ToolResult(success=True, data={"source": inputs["source"]})


class AllowedStockAcquisitionTool(BaseTool):
    name = "direct_clip_search"
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.HYBRID
    resource_profile = ResourceProfile(network_required=True)

    def execute(self, inputs: dict) -> ToolResult:
        return ToolResult(success=True, data={"acquired": True})


class EditingOnlyExecutionPolicyTests(unittest.TestCase):
    def test_local_editing_tool_is_allowed(self) -> None:
        with patch.dict(os.environ, {"OPENMONTAGE_PROFILE": "editing_only"}):
            result = LocalEditTool().execute({})
        self.assertTrue(result.success)

    def test_generation_api_tool_is_blocked_before_execution(self) -> None:
        with patch.dict(os.environ, {"OPENMONTAGE_PROFILE": "editing_only"}):
            with self.assertRaisesRegex(PermissionError, "test_paid_generation"):
                PaidGenerationTool().execute({})

    def test_network_dependent_analysis_tool_is_blocked(self) -> None:
        with patch.dict(os.environ, {"OPENMONTAGE_PROFILE": "editing_only"}):
            with self.assertRaisesRegex(PermissionError, "network_required"):
                NetworkAnalysisTool().execute({})

    def test_remote_video_reference_is_blocked_but_local_file_is_allowed(self) -> None:
        tool = RemoteVideoAnalysisTool()
        with patch.dict(os.environ, {"OPENMONTAGE_PROFILE": "editing_only"}):
            with self.assertRaisesRegex(PermissionError, "remote_video_source"):
                tool.execute({"source": "https://example.com/reference.mp4"})

            result = tool.execute({"source": "/workspace/input.mp4"})

        self.assertTrue(result.success)

    def test_asset_acquisition_profile_allows_only_stock_search_tool(self) -> None:
        with patch.dict(os.environ, {"OPENMONTAGE_PROFILE": "asset_acquisition"}):
            result = AllowedStockAcquisitionTool().execute({})
            self.assertTrue(result.success)
            with self.assertRaisesRegex(PermissionError, "asset_acquisition"):
                NetworkAnalysisTool().execute({})

    def test_asset_acquisition_profile_rejects_paid_generation(self) -> None:
        with patch.dict(os.environ, {"OPENMONTAGE_PROFILE": "asset_acquisition"}):
            with self.assertRaisesRegex(PermissionError, "asset_acquisition"):
                PaidGenerationTool().execute({})

    def test_profile_is_opt_in_for_existing_workflows(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            result = LocalEditTool().execute({})
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
