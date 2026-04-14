from enum import Enum


class ClaimDomain(str, Enum):
    AUTO = "auto"
    HEALTHCARE = "healthcare"


class DecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    PEND = "pend"
    ESCALATE = "escalate"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    INTAKE_PROCESSING = "intake_processing"
    AWAITING_DOCUMENTS = "awaiting_documents"
    UNDER_EXTRACTION = "under_extraction"
    UNDER_VALIDATION = "under_validation"
    UNDER_COVERAGE_REVIEW = "under_coverage_review"
    UNDER_FRAUD_REVIEW = "under_fraud_review"
    UNDER_DOMAIN_REVIEW = "under_domain_review"
    UNDER_DECISIONING = "under_decisioning"
    PENDING_HUMAN_REVIEW = "pending_human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDED = "pended"
    READY_FOR_SETTLEMENT = "ready_for_settlement"
    CLOSED = "closed"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActorType(str, Enum):
    SYSTEM = "system"
    AGENT = "agent"
    HUMAN = "human"