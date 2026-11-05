"""
qa_rules.py — mechanical execution of the PRD's QA pass/fail rules.

This module is intentionally pure: it takes a *metrics* dictionary (numbers
already extracted from the masks/metadata/band stack) plus the structured
rules from `rules.json` and produces a per-rule evaluation and a final
pass / retry / escalate decision, following PRD sections 2-4:

  - Rules are evaluated in order (rules.json order); the FIRST failing rule
    determines the outcome (PRD section 3: "First matching rule determines
    the outcome for that scene").
  - A rule only applies to the processing levels listed in its `levels`.
  - A check whose metric is missing/unknown is `not_assessable` — it can
    never *fail* the rule, but it is reported so the trace shows exactly
    what could and could not be verified.
  - Retry vs escalate comes from the rule's `routing` (PRD section 4).

No file I/O here — unit tests can drive every rule with synthetic numbers.
"""

from __future__ import annotations

from typing import Any, Optional

CATEGORIES = ("CLOUD", "SENSOR", "GEOM", "RADIO", "MASK_GAP", "INCOMPLETE")

OUTCOMES = ("pass", "retry", "escalate")


def _resolve_threshold(check: dict, platform: dict) -> Optional[float]:
    """Threshold may be a literal number or a reference (e.g. platform.expected_bands)."""
    if "threshold" in check:
        return check["threshold"]
    if "threshold_ref" in check:
        ref = check["threshold_ref"].split(".")
        if ref[0] == "platform":
            return platform.get(ref[1])
    return None


def _compare(metric_value: Any, op: str, threshold: Any) -> bool:
    """Apply the rule's comparison operator. Returns True when the check FAILS."""
    if op == "lt":
        return metric_value < threshold
    if op == "gt":
        return metric_value > threshold
    if op == "eq":
        return metric_value == threshold
    raise ValueError(f"unknown operator: {op}")


def evaluate_rule(rule: dict, metrics: dict, scene: dict) -> dict:
    """Evaluate one rule against the scene's metrics.

    Returns: {
      "rule_id", "name", "category", "routing", "level",
      "status": "pass" | "fail" | "not_assessable" | "not_applicable",
      "checks": [ {metric, observed, threshold, status, reasoning}, ... ],
      "reasoning": human-readable summary
    }
    """
    level = scene.get("processing_level")
    platform = scene.get("platform_spec", {})

    if rule["levels"] and level not in rule["levels"]:
        return {
            "rule_id": rule["id"],
            "name": rule["name"],
            "category": rule["category"],
            "routing": rule["routing"],
            "level": rule["levels"],
            "status": "not_applicable",
            "checks": [],
            "reasoning": f"Rule {rule['id']} applies to {rule['levels']}; scene is {level} — not evaluated at this processing level.",
        }

    check_results = []
    for check in rule["checks"]:
        metric_name = check["metric"]
        observed = metrics.get(metric_name)
        threshold = _resolve_threshold(check, platform)

        if observed is None:
            status = "not_assessable"
            check_results.append({
                "metric": metric_name,
                "observed": None,
                "threshold": threshold,
                "status": status,
                "reasoning": f"{check['reasoning']} — metric '{metric_name}' is not available in this run's inputs.",
            })
            continue

        fails = _compare(observed, check["op"], threshold)
        status = "fail" if fails else "pass"
        check_results.append({
            "metric": metric_name,
            "observed": observed,
            "threshold": threshold,
            "op": check["op"],
            "status": status,
            "reasoning": check["reasoning"],
        })

    failed = [c for c in check_results if c["status"] == "fail"]
    unassessed = [c for c in check_results if c["status"] == "not_assessable"]

    if failed:
        status = "fail"
        reasoning = (
            f"Rule {rule['id']} ({rule['name']}) fired: "
            + "; ".join(
                f"{c['metric']}={c['observed']} {c['op']} threshold={c['threshold']} → FAIL"
                for c in failed
            )
        )
    elif unassessed:
        status = "not_assessable"
        reasoning = (
            f"Rule {rule['id']} ({rule['name']}) could not be fully evaluated: "
            + "; ".join(c["metric"] for c in unassessed)
            + " not available."
        )
    else:
        status = "pass"
        reasoning = (
            f"Rule {rule['id']} ({rule['name']}) passed: "
            + "; ".join(f"{c['metric']}={c['observed']} (threshold {c['threshold']})" for c in check_results)
        )

    return {
        "rule_id": rule["id"],
        "name": rule["name"],
        "category": rule["category"],
        "routing": rule["routing"],
        "level": rule["levels"],
        "status": status,
        "checks": check_results,
        "reasoning": reasoning,
    }


def decide(evaluations: list[dict], metrics: dict, scene: dict) -> dict:
    """Synthesize the final decision from per-rule evaluations (PRD sections 3-5).

    Returns a decision record consumed by the triage agent / dashboard.
    """
    applicable = [e for e in evaluations if e["status"] != "not_applicable"]
    failed = [e for e in applicable if e["status"] == "fail"]
    unassessed = [e for e in applicable if e["status"] == "not_assessable"]

    first_failure = failed[0] if failed else None
    if first_failure is not None:
        outcome = first_failure["routing"]
        retry_count = scene.get("retry_count", 0)
        # PRD section 4: retry only while retries remain; ceiling escalates.
        if outcome == "retry":
            if retry_count >= scene.get("max_retries", 2):
                outcome = "escalate"
            else:
                retry_count += 1
        failure_category = first_failure["category"]
        fired_rule = first_failure["rule_id"]
        reason = first_failure["reasoning"]
    else:
        outcome = "pass"
        retry_count = scene.get("retry_count", 0)
        failure_category = None
        fired_rule = None
        reason = "No QA rule failed. Scene is CLEAN."

    delivery_ready = (
        outcome == "pass"
        and scene.get("processing_level") == "L2A"
        and metrics.get("quality_mask_coverage_pct") == 100.0
        and not scene.get("superseded", False)
    )

    # PRD §5: partial (band-excluded) delivery — only when the SOLE failure is
    # QA-4's band-isolable check, every other rule passes/n-a, and the customer
    # has opted in. Never applies to QA-3/5/6/7 failures: those aren't confined
    # to specific bands, so there's nothing coherent to exclude.
    partial_eligible = (
        len(failed) == 1
        and failed[0]["rule_id"] == "QA-4"
        and any(c["metric"] == "max_high_value_band_interpolated_pct" and c["status"] == "fail"
                for c in failed[0]["checks"])
        and all(c["status"] != "fail" for c in failed[0]["checks"]
                if c["metric"] != "max_high_value_band_interpolated_pct")
        and scene.get("processing_level") == "L2A"
        and metrics.get("quality_mask_coverage_pct") == 100.0
        and not scene.get("superseded", False)
    )
    delivery_ready_partial = partial_eligible and scene.get("partial_delivery_opt_in", False)
    excluded_bands = metrics.get("high_value_band_indices", []) if delivery_ready_partial else []

    if delivery_ready_partial:
        delivery_ready_note = (
            f"Partial delivery: bands {excluded_bands} excluded per PRD §5 "
            "(customer has opted in to partial delivery)."
        )
    elif partial_eligible:
        delivery_ready_note = (
            "Eligible for partial delivery per PRD §5, but scene['partial_delivery_opt_in'] "
            "is not set — partial delivery is opt-in per customer agreement, not automatic."
        )
    elif delivery_ready:
        delivery_ready_note = "Passed on all assessable rules and meets PRD section 5 conditions."
    else:
        delivery_ready_note = "Not delivery ready — see decision/reasoning."

    return {
        "decision": outcome,
        "failure_category": failure_category,
        "fired_rule": fired_rule,
        "reasoning": reason,
        "retry_count": retry_count,
        "delivery_ready": delivery_ready,
        "delivery_ready_partial": delivery_ready_partial,
        "delivery_ready_note": delivery_ready_note,
        "excluded_bands": excluded_bands,
        "not_assessed": [e["rule_id"] for e in unassessed],
        "not_assessed_detail": [e["reasoning"] for e in unassessed],
    }
