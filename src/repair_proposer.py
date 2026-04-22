"""
BIMRepair — Repair Proposer
Adapts retrieved case-based repairs to the current defect context.
"""
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class RepairProposal:
    defect_id: str
    defect_type: str
    entity_guid: str
    entity_type: str
    repair_action: str
    explanation: str
    confidence: float
    safe_to_auto_apply: bool
    matched_case_id: Optional[str] = None
    matched_similarity: float = 0.0
    repair_params: dict = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)


def propose_repair(defect, similar_cases, auto_threshold=0.70, case_library=None):
    """
    Generate a repair proposal by adapting the best matching case.
    
    Args:
        defect: Defect object
        similar_cases: List of (case_dict, similarity_score) from retrieval
        auto_threshold: Confidence threshold for auto-apply
        case_library: The CaseLibrary instance containing the surrogate classifier
    
    Returns:
        RepairProposal object
    """
    if not similar_cases:
        return RepairProposal(
            defect_id=defect.defect_id,
            defect_type=defect.defect_type,
            entity_guid=defect.entity_guid,
            entity_type=defect.entity_type,
            repair_action="No similar case found — manual review required",
            explanation="The case library has no matching repair pattern for this defect.",
            confidence=0.0,
            safe_to_auto_apply=False,
        )
    
    best_case, best_score = similar_cases[0]
    
    # Adapt the repair action to the current entity
    repair_action = _adapt_repair_action(defect, best_case)
    explanation = best_case.get("explanation", "No explanation available.")
    
    # Calculate confidence
    confidence = _calculate_confidence(defect, best_case, best_score)
    
    # Use surrogate classifier if available
    is_safe_pred = False
    if case_library and hasattr(case_library, "classifier"):
        query_text = " ".join(filter(None, [defect.defect_type, defect.entity_type, defect.description]))
        query_vec = case_library.vectorizer.transform([query_text])
        is_safe_pred = bool(case_library.classifier.predict(query_vec)[0])
        prob_safe = case_library.classifier.predict_proba(query_vec)[0][1]
        
        # Blend similarity confidence with classifier probability
        confidence = (confidence * 0.4) + (prob_safe * 0.6)
    
    # Determine if safe to auto-apply based on classifier and threshold
    safe = is_safe_pred and (confidence >= auto_threshold)
    
    # Override safe if the defect type doesn't match the retrieved case
    if best_case.get("defect_type") != defect.defect_type:
        safe = False
    
    # Build repair parameters
    repair_params = _build_repair_params(defect, best_case)
    
    proposal = RepairProposal(
        defect_id=defect.defect_id,
        defect_type=defect.defect_type,
        entity_guid=defect.entity_guid,
        entity_type=defect.entity_type,
        repair_action=repair_action,
        explanation=explanation,
        confidence=confidence,
        safe_to_auto_apply=safe,
        matched_case_id=best_case.get("case_id"),
        matched_similarity=best_score,
        repair_params=repair_params,
    )
    
    logger.info(f"Proposal for {defect.defect_id}: confidence={confidence:.2f}, "
                f"auto_apply={safe}, case={best_case.get('case_id')}")
    
    return proposal


def _adapt_repair_action(defect, case):
    """Adapt the case's repair action to the current defect's entity."""
    action = case.get("repair_action", "")
    
    # Substitute entity name if present
    entity_name = defect.entity_name or "unnamed"
    action = action.replace("{EntityType}", defect.entity_type)
    action = action.replace("{Index}", str(defect.entity_id))
    
    return action


def _calculate_confidence(defect, case, similarity_score):
    """Calculate overall confidence for the repair proposal."""
    confidence = similarity_score
    
    # Boost if defect type matches exactly
    if case.get("defect_type") == defect.defect_type:
        confidence = min(confidence + 0.15, 1.0)
    
    # Boost if entity type matches exactly
    if case.get("entity_type") == defect.entity_type:
        confidence = min(confidence + 0.10, 1.0)
    
    # Slight penalty if case says not safe to auto-apply
    if not case.get("safe_to_auto_apply", False):
        confidence *= 0.8
    
    return round(confidence, 3)


def _build_repair_params(defect, case):
    """Build concrete repair parameters from defect context and case template."""
    params = {
        "entity_id": defect.entity_id,
        "entity_guid": defect.entity_guid,
        "entity_type": defect.entity_type,
    }
    
    # For missing properties, extract pset/prop details
    if defect.defect_type == "missing_property":
        params["property_set"] = defect.context.get("property_set",
                                    case.get("property_set", ""))
        params["property_name"] = defect.context.get("property_name",
                                     case.get("property_name", ""))
        params["default_value"] = defect.context.get("default_value",
                                     case.get("default_value", ""))
        params["value_type"] = case.get("value_type", "IfcLabel")
    
    # For spatial containment
    elif defect.defect_type == "broken_spatial_containment":
        params["action"] = "assign_container"
    
    # For disconnected storey
    elif defect.defect_type == "disconnected_storey":
        params["action"] = "aggregate_to_parent"
    
    # For invalid parent-child
    elif defect.defect_type == "invalid_parent_child":
        params["action"] = "assign_to_storey"
    
    # For naming
    elif defect.defect_type == "naming_inconsistency":
        params["action"] = "fix_name"
        params["issue"] = defect.context.get("issue", "empty_name")
    
    # For missing material
    elif defect.defect_type == "missing_material":
        params["action"] = "flag_missing_material"
    
    return params
