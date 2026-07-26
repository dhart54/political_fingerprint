"""IR-native public editorial presentation boundary."""

from .compiler import (
    EditorialPresentationError,
    approval_subject_for_artifact,
    artifact_bytes,
    artifact_digest,
    build_approval_subject,
    compile_public_issue_presentation,
    detached_receipt_matches,
)
from .selector import (
    RECEIPTS_ONLY_BADGE,
    select_public_presentations,
)
from .validation import validate_public_issue_presentation

__all__ = [
    "EditorialPresentationError",
    "RECEIPTS_ONLY_BADGE",
    "approval_subject_for_artifact",
    "artifact_bytes",
    "artifact_digest",
    "build_approval_subject",
    "compile_public_issue_presentation",
    "detached_receipt_matches",
    "select_public_presentations",
    "validate_public_issue_presentation",
]
