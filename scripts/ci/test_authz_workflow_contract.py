"""Structural guardrails for the mandatory native-authorization CI path."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _workflow(name: str) -> dict:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))
    # YAML 1.1 treats the unquoted GitHub Actions key `on` as a boolean.
    workflow["on"] = workflow.pop(True)
    return workflow


def test_ci_requires_both_team_sharing_jobs_when_selected():
    workflow = _workflow("ci.yml")
    triggers = workflow["on"]
    for trigger in ("workflow_call", "workflow_dispatch"):
        inputs = triggers[trigger]["inputs"]
        assert {"ref", "base-ref", "frontend-tests-folder", "run-all-tests", "docker-runs-on"} <= set(inputs)

    jobs = workflow["jobs"]
    backend = jobs["test-authz-backend"]
    browser = jobs["test-authz-e2e"]
    assert backend["name"] == "Run Team Sharing Backend Tests"
    assert browser["name"] == "Run Team Sharing E2E"
    assert "authz-sharing" in backend["if"]
    assert "run-all-tests" in backend["if"]
    assert "authz-sharing" in browser["if"]
    assert "run-all-tests" in browser["if"]
    assert backend.get("continue-on-error") is None
    assert browser.get("continue-on-error") is None
    assert backend["strategy"]["matrix"] == {
        "python-version": ["3.10", "3.14"],
        "database": ["sqlite", "postgresql"],
    }
    assert backend["services"]["postgres"]["image"] == "postgres:16"

    browser_inputs = browser["with"]
    assert browser_inputs["authz-mode"] is True
    assert browser_inputs["tests_folder"] == "tests/core/features/authz"
    assert set(yaml.safe_load(browser_inputs["suites"])) == {"api", "database", "workspace"}

    success = jobs["ci_success"]
    assert {"test-authz-backend", "test-authz-e2e"} <= set(success["needs"])
    exit_contract = success["env"]["EXIT_CODE"]
    assert "needs.test-authz-backend.result != 'success'" in exit_contract
    assert "needs.test-authz-e2e.result != 'success'" in exit_contract


def test_full_validation_includes_candidate_docker_job_and_ref():
    workflow = _workflow("ci.yml")
    docker = workflow["jobs"]["test-docker"]
    assert "run-all-tests" in docker["if"]
    assert docker["with"]["ref"] == "${{ inputs.ref || github.ref }}"
    assert "docker-runs-on" in docker["with"]["runs-on"]


def test_authz_browser_mode_is_exact_serial_and_collision_free():
    workflow = _workflow("typescript_test.yml")
    triggers = workflow["on"]
    for trigger in ("workflow_call", "workflow_dispatch"):
        assert triggers[trigger]["inputs"]["authz-mode"]["type"] == "boolean"

    assert workflow["env"]["LANGFLOW_E2E_AUTHZ"] == "${{ inputs['authz-mode'] && 'true' || 'false' }}"
    jobs = workflow["jobs"]
    discovery = next(step for step in jobs["determine-test-suite"]["steps"] if step.get("id") == "setup-matrix")
    discovery_script = discovery["run"]
    assert 'TEST_COUNT" != "8' in discovery_script
    assert "inspectAuthzJourneyTitles" in discovery_script
    assert "SHARD_COUNT=1" in discovery_script

    execution = next(
        step for step in jobs["setup-and-test"]["steps"] if step.get("name") == "Execute Playwright Tests"
    )["run"]
    assert "WORKERS=1" in execution
    assert "RETRIES=0" in execution
    assert '--retries="$RETRIES"' in execution
    assert jobs["setup-and-test"]["continue-on-error"].startswith("${{ !inputs['authz-mode']")
    assert jobs["report-gate"]["continue-on-error"].startswith("${{ !inputs['authz-mode']")

    rendered = (ROOT / ".github" / "workflows" / "typescript_test.yml").read_text(encoding="utf-8")
    artifact_prefixes = (
        "blob-report-",
        "playwright-coverage-",
        "playwright-server-log-",
        "html-report-",
        "json-report-",
    )
    for artifact_prefix in artifact_prefixes:
        assert f"{artifact_prefix}${{{{ env.PLAYWRIGHT_ARTIFACT_NAMESPACE }}}}" in rendered


def test_authz_journey_inventory_has_all_exact_ids_once_without_skips():
    spec = (
        ROOT / "src" / "frontend" / "tests" / "core" / "features" / "authz" / "authz-team-sharing.spec.ts"
    ).read_text(encoding="utf-8")
    ids = re.findall(r"\[AUTHZ-JOURNEY-(\d{2})\]", spec)
    assert ids == [f"{index:02d}" for index in range(1, 9)]
    assert spec.count('tag: ["@authz", "@api", "@database", "@workspace", "@release"]') == 8
    assert "test.skip" not in spec
    assert "describe.skip" not in spec


def test_authz_path_filter_covers_every_contract_layer():
    filters = yaml.safe_load((ROOT / ".github" / "changes-filter.yaml").read_text(encoding="utf-8"))
    paths = set(filters["authz-sharing"])
    assert {
        "src/backend/base/langflow/services/authorization/**",
        "src/backend/base/langflow/alembic/**",
        "src/lfx/src/lfx/services/authorization/**",
        "src/frontend/tests/core/features/authz/**",
        "scripts/ci/authz_endpoint_matrix.json",
        ".github/workflows/ci.yml",
        ".env.example",
        "AGENTS.md",
    } <= paths
