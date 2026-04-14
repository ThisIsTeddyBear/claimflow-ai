from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    scenarios = json.loads(Path("apps/api/app/seed/scenarios.json").read_text(encoding="utf-8"))
    base = Path("data/sample_claims")

    for scenario in scenarios:
        scenario_dir = base / scenario["domain"] / scenario["scenario_id"]
        scenario_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "scenario_id": scenario["scenario_id"],
            "domain": scenario["domain"],
            "expected_decision": scenario["expected_decision"],
            "incident_or_service_date": scenario["incident_or_service_date"],
            "policy_or_member_id": scenario["policy_or_member_id"],
            "claimant_name": scenario["claimant_name"],
            "estimated_amount": scenario["estimated_amount"],
            "rationale": f"Synthetic scenario for {scenario['expected_decision']} path coverage.",
        }
        (scenario_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        for doc in scenario.get("documents", []):
            (scenario_dir / doc["filename"]).write_text(doc["content"], encoding="utf-8")

    print(f"Generated {len(scenarios)} synthetic claim packets.")


if __name__ == "__main__":
    main()