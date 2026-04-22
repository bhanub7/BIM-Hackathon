"""
BIMRepair — Symbolic Validator
Validates repair proposals against IFC schema rules before application.
"""
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    passed: bool
    checks: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)


def validate_proposal(model, proposal):
    """
    Validate a repair proposal against IFC rules.
    
    Returns:
        ValidationResult
    """
    result = ValidationResult(passed=True)
    
    # Check 1: Entity still exists in model
    try:
        entity = model.by_id(proposal.repair_params.get("entity_id", 0))
        result.checks.append("Entity exists in model: PASS")
    except Exception:
        result.passed = False
        result.errors.append(f"Entity ID {proposal.repair_params.get('entity_id')} not found in model")
        return result
    
    # Check 2: Defect-type specific validations
    if proposal.defect_type == "missing_property":
        _validate_property_repair(model, entity, proposal, result)
    elif proposal.defect_type == "broken_spatial_containment":
        _validate_containment_repair(model, entity, proposal, result)
    elif proposal.defect_type == "disconnected_storey":
        _validate_aggregation_repair(model, entity, proposal, result)
    elif proposal.defect_type == "invalid_parent_child":
        _validate_parent_child_repair(model, entity, proposal, result)
    elif proposal.defect_type == "naming_inconsistency":
        _validate_naming_repair(model, entity, proposal, result)
    elif proposal.defect_type == "missing_material":
        _validate_material_repair(model, entity, proposal, result)
    
    # Check 3: Confidence threshold
    if proposal.confidence < 0.1:
        result.passed = False
        result.errors.append(f"Confidence too low: {proposal.confidence:.2f}")
    
    if result.passed:
        logger.info(f"Validation PASSED for {proposal.defect_id}")
    else:
        logger.warning(f"Validation FAILED for {proposal.defect_id}: {result.errors}")
    
    return result


def _validate_property_repair(model, entity, proposal, result):
    """Validate adding a property."""
    params = proposal.repair_params
    pset_name = params.get("property_set", "")
    prop_name = params.get("property_name", "")
    
    if not pset_name:
        result.passed = False
        result.errors.append("Missing property_set name in repair params")
        return
    
    if not prop_name:
        result.passed = False
        result.errors.append("Missing property_name in repair params")
        return
    
    # Check value type is reasonable
    value_type = params.get("value_type", "")
    valid_types = ["IfcBoolean", "IfcLabel", "IfcIdentifier", "IfcText", "IfcReal", "IfcInteger"]
    if value_type and value_type not in valid_types:
        result.warnings.append(f"Unusual value type: {value_type}")
    
    result.checks.append(f"Property {pset_name}.{prop_name} repair is valid: PASS")


def _validate_containment_repair(model, entity, proposal, result):
    """Validate spatial containment assignment."""
    from src.ifc_parser import get_first_storey
    
    storey = get_first_storey(model)
    if storey is None:
        result.passed = False
        result.errors.append("No IfcBuildingStorey available to assign container")
        return
    
    result.checks.append("Target storey exists for containment: PASS")


def _validate_aggregation_repair(model, entity, proposal, result):
    """Validate aggregation reconnection."""
    from src.ifc_parser import get_first_building
    
    if entity.is_a("IfcBuildingStorey"):
        building = get_first_building(model)
        if building is None:
            result.passed = False
            result.errors.append("No IfcBuilding available for storey aggregation")
            return
        result.checks.append("Target building exists for aggregation: PASS")
    elif entity.is_a("IfcBuilding"):
        sites = list(model.by_type("IfcSite"))
        if not sites:
            result.passed = False
            result.errors.append("No IfcSite available for building aggregation")
            return
        result.checks.append("Target site exists for aggregation: PASS")


def _validate_parent_child_repair(model, entity, proposal, result):
    """Validate space-to-storey assignment."""
    from src.ifc_parser import get_first_storey
    
    storey = get_first_storey(model)
    if storey is None:
        result.passed = False
        result.errors.append("No IfcBuildingStorey available for space assignment")
        return
    
    result.checks.append("Target storey exists for space: PASS")


def _validate_naming_repair(model, entity, proposal, result):
    """Validate naming fix."""
    result.checks.append("Naming repair is always valid: PASS")


def _validate_material_repair(model, entity, proposal, result):
    """Material repairs are flag-only — always valid but never auto-applied."""
    result.warnings.append("Material cannot be auto-assigned — flagged for manual review")
    result.checks.append("Material flag validation: PASS")
