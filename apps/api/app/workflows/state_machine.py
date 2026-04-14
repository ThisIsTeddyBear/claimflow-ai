from __future__ import annotations

from collections import defaultdict


class ClaimStateMachine:
    def __init__(self) -> None:
        self.transitions = defaultdict(set)
        self._register_defaults()

    def can_transition(self, current: str, target: str) -> bool:
        if current == target:
            return True
        return target in self.transitions[current]

    def _register_defaults(self) -> None:
        self._allow("draft", "submitted")
        self._allow("submitted", "intake_processing")
        self._allow("intake_processing", "awaiting_documents")
        self._allow("intake_processing", "under_extraction")
        self._allow("intake_processing", "pended")
        self._allow("under_extraction", "under_validation")
        self._allow("under_validation", "under_coverage_review")
        self._allow("under_coverage_review", "under_fraud_review")
        self._allow("under_fraud_review", "under_domain_review")
        self._allow("under_domain_review", "under_decisioning")
        self._allow("under_decisioning", "approved")
        self._allow("under_decisioning", "rejected")
        self._allow("under_decisioning", "pended")
        self._allow("under_decisioning", "pending_human_review")
        self._allow("pending_human_review", "approved")
        self._allow("pending_human_review", "rejected")
        self._allow("pending_human_review", "pended")
        self._allow("approved", "ready_for_settlement")
        self._allow("ready_for_settlement", "closed")
        self._allow("rejected", "closed")
        self._allow("pended", "submitted")
        self._allow("approved", "intake_processing")
        self._allow("rejected", "intake_processing")
        self._allow("pended", "intake_processing")
        self._allow("pending_human_review", "intake_processing")
        self._allow("closed", "intake_processing")

    def _allow(self, from_status: str, to_status: str) -> None:
        self.transitions[from_status].add(to_status)
