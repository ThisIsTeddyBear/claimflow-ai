from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RuleMatch:
    rule_id: str
    priority: int
    decision: str | None
    reason: str
    reviewer_queue: str | None = None


class RuleEngine:
    def __init__(self, rules_dir: str) -> None:
        self.rules_dir = Path(rules_dir)

    def evaluate(self, *, domain: str, facts: dict[str, Any]) -> list[RuleMatch]:
        rules = self._load_rules(domain)
        matches: list[RuleMatch] = []
        for rule in rules:
            if self._matches(rule.get("condition", {}), facts):
                action = rule.get("action", {})
                matches.append(
                    RuleMatch(
                        rule_id=rule.get("rule_id", "unknown"),
                        priority=int(rule.get("priority", 0)),
                        decision=action.get("decision"),
                        reason=action.get("reason", "Rule triggered"),
                        reviewer_queue=action.get("reviewer_queue"),
                    )
                )
        return sorted(matches, key=lambda item: item.priority, reverse=True)

    def _load_rules(self, domain: str) -> list[dict]:
        path = self.rules_dir / f"{domain}_rules.yaml"
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if isinstance(data, dict):
            return data.get("rules", [])
        return data

    def _matches(self, condition: dict, facts: dict[str, Any]) -> bool:
        if not condition:
            return False

        if "all" in condition:
            return all(self._predicate(pred, facts) for pred in condition["all"])
        if "any" in condition:
            return any(self._predicate(pred, facts) for pred in condition["any"])
        return self._predicate(condition, facts)

    def _predicate(self, predicate: dict, facts: dict[str, Any]) -> bool:
        fact_name = predicate.get("fact")
        if fact_name is None:
            return False

        fact_value = self._get_fact_value(facts, fact_name)
        if "equals" in predicate:
            return fact_value == predicate["equals"]
        if "not_equals" in predicate:
            return fact_value != predicate["not_equals"]
        if "exists" in predicate:
            should_exist = bool(predicate["exists"])
            exists = fact_value is not None
            return exists == should_exist
        if "in" in predicate:
            return fact_value in predicate["in"]
        if "gt" in predicate:
            return fact_value is not None and fact_value > predicate["gt"]
        if "gte" in predicate:
            return fact_value is not None and fact_value >= predicate["gte"]
        if "lt" in predicate:
            return fact_value is not None and fact_value < predicate["lt"]
        if "lte" in predicate:
            return fact_value is not None and fact_value <= predicate["lte"]
        return False

    @staticmethod
    def _get_fact_value(facts: dict[str, Any], fact_name: str) -> Any:
        value: Any = facts
        for part in fact_name.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
                continue
            return None
        return value