"""
BIMRepair — Defect Detector
Rule-based engine that detects common BIM defects in IFC models.
"""
import logging
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import EXPECTED_PROPERTIES, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_CRITICAL
from src.ifc_parser import (
    extract_entities, extract_property_sets, get_spatial_container,
    get_aggregation_parent, get_material_associations, get_all_storeys,
    get_all_buildings,
)

logger = logging.getLogger(__name__)


@dataclass
class Defect:
    defect_id: str
    defect_type: str
    entity_id: int
    entity_guid: str
    entity_type: str
    entity_name: Optional[str]
    severity: str
    description: str
    context: dict = field(default_factory=dict)
    
    def to_dict(self):
        d = asdict(self)
        return d


_defect_counter = 0

def _next_defect_id():
    global _defect_counter
    _defect_counter += 1
    return f"DEF_{_defect_counter:04d}"


def reset_counter():
    global _defect_counter
    _defect_counter = 0


def detect_all_defects(model):
    """Run all defect detection rules and return list of Defect objects."""
    reset_counter()
    defects = []
    
    defects.extend(detect_missing_properties(model))
    defects.extend(detect_broken_spatial_containment(model))
    defects.extend(detect_disconnected_storeys(model))
    defects.extend(detect_invalid_parent_child(model))
    defects.extend(detect_naming_issues(model))
    defects.extend(detect_missing_materials(model))
    
    logger.info(f"Detected {len(defects)} total defects")
    return defects


def detect_missing_properties(model):
    """D001: Check for missing required properties per entity type."""
    defects = []
    
    for entity_type, expected_props in EXPECTED_PROPERTIES.items():
        for entity in model.by_type(entity_type):
            psets = extract_property_sets(model, entity)
            
            for pset_name, prop_name, default_val, severity in expected_props:
                pset_props = psets.get(pset_name, {})
                if prop_name not in pset_props:
                    defects.append(Defect(
                        defect_id=_next_defect_id(),
                        defect_type="missing_property",
                        entity_id=entity.id(),
                        entity_guid=entity.GlobalId,
                        entity_type=entity_type,
                        entity_name=entity.Name,
                        severity=severity,
                        description=f"{entity_type} '{entity.Name or 'unnamed'}' is missing "
                                    f"'{prop_name}' property in {pset_name}",
                        context={
                            "property_set": pset_name,
                            "property_name": prop_name,
                            "default_value": default_val,
                            "existing_psets": list(psets.keys()),
                        }
                    ))
    
    logger.info(f"  Missing properties: {len(defects)}")
    return defects


def detect_broken_spatial_containment(model):
    """D002: Check elements not contained in any spatial structure."""
    defects = []
    check_types = ["IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcColumn", "IfcBeam"]
    
    for etype in check_types:
        for entity in model.by_type(etype):
            container = get_spatial_container(model, entity)
            if container is None:
                defects.append(Defect(
                    defect_id=_next_defect_id(),
                    defect_type="broken_spatial_containment",
                    entity_id=entity.id(),
                    entity_guid=entity.GlobalId,
                    entity_type=etype,
                    entity_name=entity.Name,
                    severity=SEVERITY_HIGH,
                    description=f"{etype} '{entity.Name or 'unnamed'}' is not contained "
                                f"in any IfcBuildingStorey",
                    context={"needs_container": True}
                ))
    
    logger.info(f"  Broken containment: {len(defects)}")
    return defects


def detect_disconnected_storeys(model):
    """D003: Check storeys not aggregated to a building."""
    defects = []
    
    for storey in model.by_type("IfcBuildingStorey"):
        parent = get_aggregation_parent(model, storey)
        if parent is None or not parent.is_a("IfcBuilding"):
            defects.append(Defect(
                defect_id=_next_defect_id(),
                defect_type="disconnected_storey",
                entity_id=storey.id(),
                entity_guid=storey.GlobalId,
                entity_type="IfcBuildingStorey",
                entity_name=storey.Name,
                severity=SEVERITY_CRITICAL,
                description=f"IfcBuildingStorey '{storey.Name or 'unnamed'}' is not "
                            f"aggregated into any IfcBuilding",
                context={
                    "elevation": storey.Elevation if hasattr(storey, "Elevation") else None,
                }
            ))
    
    # Check buildings not aggregated to site
    for building in model.by_type("IfcBuilding"):
        parent = get_aggregation_parent(model, building)
        if parent is None or not parent.is_a("IfcSite"):
            defects.append(Defect(
                defect_id=_next_defect_id(),
                defect_type="disconnected_storey",
                entity_id=building.id(),
                entity_guid=building.GlobalId,
                entity_type="IfcBuilding",
                entity_name=building.Name,
                severity=SEVERITY_CRITICAL,
                description=f"IfcBuilding '{building.Name or 'unnamed'}' is not "
                            f"aggregated into any IfcSite",
                context={}
            ))
    
    logger.info(f"  Disconnected storeys/buildings: {len(defects)}")
    return defects


def detect_invalid_parent_child(model):
    """D004: Check spaces not properly parented."""
    defects = []
    
    for space in model.by_type("IfcSpace"):
        parent = get_aggregation_parent(model, space)
        if parent is None:
            defects.append(Defect(
                defect_id=_next_defect_id(),
                defect_type="invalid_parent_child",
                entity_id=space.id(),
                entity_guid=space.GlobalId,
                entity_type="IfcSpace",
                entity_name=space.Name,
                severity=SEVERITY_HIGH,
                description=f"IfcSpace '{space.Name or 'unnamed'}' is not aggregated "
                            f"into any IfcBuildingStorey",
                context={"needs_parent_storey": True}
            ))
        elif not parent.is_a("IfcBuildingStorey"):
            defects.append(Defect(
                defect_id=_next_defect_id(),
                defect_type="invalid_parent_child",
                entity_id=space.id(),
                entity_guid=space.GlobalId,
                entity_type="IfcSpace",
                entity_name=space.Name,
                severity=SEVERITY_MEDIUM,
                description=f"IfcSpace '{space.Name or 'unnamed'}' is aggregated into "
                            f"{parent.is_a()} instead of IfcBuildingStorey",
                context={"current_parent_type": parent.is_a()}
            ))
    
    logger.info(f"  Invalid parent-child: {len(defects)}")
    return defects


def detect_naming_issues(model):
    """D005: Check for empty, None, or duplicate names."""
    defects = []
    check_types = ["IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", "IfcColumn",
                    "IfcBeam", "IfcSpace", "IfcBuildingStorey"]
    
    for etype in check_types:
        entities = list(model.by_type(etype))
        names_seen = {}
        
        for entity in entities:
            name = entity.Name
            
            # Empty or None name
            if not name or name.strip() == "":
                severity = SEVERITY_MEDIUM if etype in ("IfcSpace", "IfcBuildingStorey") else SEVERITY_LOW
                defects.append(Defect(
                    defect_id=_next_defect_id(),
                    defect_type="naming_inconsistency",
                    entity_id=entity.id(),
                    entity_guid=entity.GlobalId,
                    entity_type=etype,
                    entity_name=name,
                    severity=severity,
                    description=f"{etype} has empty or missing Name attribute",
                    context={"issue": "empty_name"}
                ))
            else:
                # Track for duplicate detection
                if name in names_seen:
                    names_seen[name].append(entity)
                else:
                    names_seen[name] = [entity]
        
        # Duplicate names
        for name, ents in names_seen.items():
            if len(ents) > 1:
                for ent in ents:
                    defects.append(Defect(
                        defect_id=_next_defect_id(),
                        defect_type="naming_inconsistency",
                        entity_id=ent.id(),
                        entity_guid=ent.GlobalId,
                        entity_type=etype,
                        entity_name=name,
                        severity=SEVERITY_LOW,
                        description=f"{etype} name '{name}' is duplicated ({len(ents)} instances)",
                        context={"issue": "duplicate_name", "duplicate_count": len(ents)}
                    ))
    
    logger.info(f"  Naming issues: {len(defects)}")
    return defects


def detect_missing_materials(model):
    """D006: Check elements without material associations."""
    defects = []
    check_types = ["IfcWall", "IfcSlab", "IfcColumn", "IfcBeam"]
    
    for etype in check_types:
        for entity in model.by_type(etype):
            mat = get_material_associations(model, entity)
            if mat is None:
                defects.append(Defect(
                    defect_id=_next_defect_id(),
                    defect_type="missing_material",
                    entity_id=entity.id(),
                    entity_guid=entity.GlobalId,
                    entity_type=etype,
                    entity_name=entity.Name,
                    severity=SEVERITY_MEDIUM,
                    description=f"{etype} '{entity.Name or 'unnamed'}' has no material association",
                    context={"needs_material": True}
                ))
    
    logger.info(f"  Missing materials: {len(defects)}")
    return defects
