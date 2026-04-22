"""
BIMRepair — Synthetic Case Library Generator
Generates defect→repair case pairs for the case-based retrieval system.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATA_DIR

CASES = [
    # ── Missing Property Cases ──
    {
        "case_id": "CASE_001", "defect_type": "missing_property", "entity_type": "IfcWall",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcWall is missing the 'LoadBearing' property in Pset_WallCommon",
        "property_set": "Pset_WallCommon", "property_name": "LoadBearing",
        "default_value": False, "value_type": "IfcBoolean",
        "repair_action": "Add property 'LoadBearing' with value FALSE to Pset_WallCommon",
        "explanation": "Walls must declare load-bearing status. Default FALSE is safe when structural analysis is absent."
    },
    {
        "case_id": "CASE_002", "defect_type": "missing_property", "entity_type": "IfcWall",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcWall is missing the 'IsExternal' property in Pset_WallCommon",
        "property_set": "Pset_WallCommon", "property_name": "IsExternal",
        "default_value": False, "value_type": "IfcBoolean",
        "repair_action": "Add property 'IsExternal' with value FALSE to Pset_WallCommon",
        "explanation": "IsExternal distinguishes exterior from interior walls. Default FALSE assumes interior."
    },
    {
        "case_id": "CASE_003", "defect_type": "missing_property", "entity_type": "IfcWall",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcWall is missing 'FireRating' property in Pset_WallCommon",
        "property_set": "Pset_WallCommon", "property_name": "FireRating",
        "default_value": "", "value_type": "IfcLabel",
        "repair_action": "Add property 'FireRating' with empty value to Pset_WallCommon",
        "explanation": "FireRating is required for compliance. Empty string flags it for later review."
    },
    {
        "case_id": "CASE_004", "defect_type": "missing_property", "entity_type": "IfcSlab",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcSlab is missing the 'LoadBearing' property in Pset_SlabCommon",
        "property_set": "Pset_SlabCommon", "property_name": "LoadBearing",
        "default_value": True, "value_type": "IfcBoolean",
        "repair_action": "Add property 'LoadBearing' with value TRUE to Pset_SlabCommon",
        "explanation": "Slabs are typically structural. Default TRUE is the safe assumption."
    },
    {
        "case_id": "CASE_005", "defect_type": "missing_property", "entity_type": "IfcSlab",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcSlab is missing the 'IsExternal' property in Pset_SlabCommon",
        "property_set": "Pset_SlabCommon", "property_name": "IsExternal",
        "default_value": False, "value_type": "IfcBoolean",
        "repair_action": "Add property 'IsExternal' with value FALSE to Pset_SlabCommon",
        "explanation": "IsExternal differentiates roof slabs from floor slabs. Default FALSE assumes floor."
    },
    {
        "case_id": "CASE_006", "defect_type": "missing_property", "entity_type": "IfcDoor",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcDoor is missing the 'FireRating' property in Pset_DoorCommon",
        "property_set": "Pset_DoorCommon", "property_name": "FireRating",
        "default_value": "", "value_type": "IfcLabel",
        "repair_action": "Add property 'FireRating' with empty value to Pset_DoorCommon",
        "explanation": "Doors need fire rating for egress compliance. Empty flags for review."
    },
    {
        "case_id": "CASE_007", "defect_type": "missing_property", "entity_type": "IfcDoor",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcDoor is missing the 'IsExternal' property in Pset_DoorCommon",
        "property_set": "Pset_DoorCommon", "property_name": "IsExternal",
        "default_value": False, "value_type": "IfcBoolean",
        "repair_action": "Add property 'IsExternal' with value FALSE to Pset_DoorCommon",
        "explanation": "IsExternal classifies door exposure. Default FALSE assumes interior door."
    },
    {
        "case_id": "CASE_008", "defect_type": "missing_property", "entity_type": "IfcWindow",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcWindow is missing the 'IsExternal' property in Pset_WindowCommon",
        "property_set": "Pset_WindowCommon", "property_name": "IsExternal",
        "default_value": True, "value_type": "IfcBoolean",
        "repair_action": "Add property 'IsExternal' with value TRUE to Pset_WindowCommon",
        "explanation": "Windows are typically external. Default TRUE is the safe assumption."
    },
    {
        "case_id": "CASE_009", "defect_type": "missing_property", "entity_type": "IfcColumn",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcColumn is missing the 'LoadBearing' property in Pset_ColumnCommon",
        "property_set": "Pset_ColumnCommon", "property_name": "LoadBearing",
        "default_value": True, "value_type": "IfcBoolean",
        "repair_action": "Add property 'LoadBearing' with value TRUE to Pset_ColumnCommon",
        "explanation": "Columns are structural by default. TRUE is the safe assumption."
    },
    {
        "case_id": "CASE_010", "defect_type": "missing_property", "entity_type": "IfcBeam",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcBeam is missing the 'LoadBearing' property in Pset_BeamCommon",
        "property_set": "Pset_BeamCommon", "property_name": "LoadBearing",
        "default_value": True, "value_type": "IfcBoolean",
        "repair_action": "Add property 'LoadBearing' with value TRUE to Pset_BeamCommon",
        "explanation": "Beams are structural by default. TRUE is the safe assumption."
    },
    # ── Broken Spatial Containment Cases ──
    {
        "case_id": "CASE_011", "defect_type": "broken_spatial_containment", "entity_type": "IfcWall",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcWall is not contained in any IfcBuildingStorey via IfcRelContainedInSpatialStructure",
        "repair_action": "Create IfcRelContainedInSpatialStructure linking wall to nearest storey",
        "explanation": "Every physical element must be spatially contained. Assign to the first available storey."
    },
    {
        "case_id": "CASE_012", "defect_type": "broken_spatial_containment", "entity_type": "IfcSlab",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcSlab is not contained in any IfcBuildingStorey via IfcRelContainedInSpatialStructure",
        "repair_action": "Create IfcRelContainedInSpatialStructure linking slab to nearest storey",
        "explanation": "Slabs must belong to a storey for spatial queries and quantity takeoff."
    },
    {
        "case_id": "CASE_013", "defect_type": "broken_spatial_containment", "entity_type": "IfcDoor",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcDoor is not contained in any IfcBuildingStorey via IfcRelContainedInSpatialStructure",
        "repair_action": "Create IfcRelContainedInSpatialStructure linking door to nearest storey",
        "explanation": "Doors need spatial containment for navigation and FM systems."
    },
    {
        "case_id": "CASE_014", "defect_type": "broken_spatial_containment", "entity_type": "IfcWindow",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcWindow is not contained in any IfcBuildingStorey via IfcRelContainedInSpatialStructure",
        "repair_action": "Create IfcRelContainedInSpatialStructure linking window to nearest storey",
        "explanation": "Windows need spatial containment for facade analysis."
    },
    {
        "case_id": "CASE_015", "defect_type": "broken_spatial_containment", "entity_type": "IfcColumn",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcColumn is not contained in any IfcBuildingStorey",
        "repair_action": "Create IfcRelContainedInSpatialStructure linking column to nearest storey",
        "explanation": "Columns must be spatially contained for structural coordination."
    },
    # ── Disconnected Storey Cases ──
    {
        "case_id": "CASE_016", "defect_type": "disconnected_storey", "entity_type": "IfcBuildingStorey",
        "severity": "critical", "safe_to_auto_apply": True,
        "defect_description": "IfcBuildingStorey is not aggregated into any IfcBuilding via IfcRelAggregates",
        "repair_action": "Create IfcRelAggregates linking storey to the building",
        "explanation": "Storeys must be children of a building in the spatial hierarchy."
    },
    {
        "case_id": "CASE_017", "defect_type": "disconnected_storey", "entity_type": "IfcBuilding",
        "severity": "critical", "safe_to_auto_apply": True,
        "defect_description": "IfcBuilding is not aggregated into any IfcSite via IfcRelAggregates",
        "repair_action": "Create IfcRelAggregates linking building to the site",
        "explanation": "Buildings must be children of a site in the spatial hierarchy."
    },
    # ── Invalid Parent-Child Cases ──
    {
        "case_id": "CASE_018", "defect_type": "invalid_parent_child", "entity_type": "IfcSpace",
        "severity": "high", "safe_to_auto_apply": True,
        "defect_description": "IfcSpace is not aggregated into any IfcBuildingStorey",
        "repair_action": "Create IfcRelAggregates linking space to the nearest storey",
        "explanation": "Spaces must belong to a storey for room-based analysis."
    },
    {
        "case_id": "CASE_019", "defect_type": "invalid_parent_child", "entity_type": "IfcSpace",
        "severity": "medium", "safe_to_auto_apply": False,
        "defect_description": "IfcSpace is aggregated into wrong IfcBuildingStorey based on elevation",
        "repair_action": "Reassign space to correct storey based on Z-coordinate comparison",
        "explanation": "Space elevation should match its parent storey. Needs manual verification."
    },
    # ── Naming Inconsistency Cases ──
    {
        "case_id": "CASE_020", "defect_type": "naming_inconsistency", "entity_type": "IfcWall",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "IfcWall has empty or None Name attribute",
        "repair_action": "Set Name to '{EntityType}_{Index}' pattern",
        "explanation": "Empty names break search and reporting. Auto-generated name is better than none."
    },
    {
        "case_id": "CASE_021", "defect_type": "naming_inconsistency", "entity_type": "IfcSlab",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "IfcSlab has empty or None Name attribute",
        "repair_action": "Set Name to 'Slab_{Index}' pattern",
        "explanation": "All elements should have meaningful names for coordination."
    },
    {
        "case_id": "CASE_022", "defect_type": "naming_inconsistency", "entity_type": "IfcDoor",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "IfcDoor has empty or None Name attribute",
        "repair_action": "Set Name to 'Door_{Index}' pattern",
        "explanation": "Doors need names for schedule generation and FM."
    },
    {
        "case_id": "CASE_023", "defect_type": "naming_inconsistency", "entity_type": "IfcWindow",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "IfcWindow has empty or None Name attribute",
        "repair_action": "Set Name to 'Window_{Index}' pattern",
        "explanation": "Windows need names for schedule generation."
    },
    {
        "case_id": "CASE_024", "defect_type": "naming_inconsistency", "entity_type": "IfcSpace",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcSpace has empty or None Name attribute",
        "repair_action": "Set Name to 'Space_{Index}' pattern",
        "explanation": "Spaces need names for room schedules and area calculations."
    },
    {
        "case_id": "CASE_025", "defect_type": "naming_inconsistency", "entity_type": "IfcBuildingStorey",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcBuildingStorey has empty or None Name attribute",
        "repair_action": "Set Name to 'Level_{Index}' pattern",
        "explanation": "Storeys need names for navigation and spatial queries."
    },
    # ── Missing Material Cases ──
    {
        "case_id": "CASE_026", "defect_type": "missing_material", "entity_type": "IfcWall",
        "severity": "medium", "safe_to_auto_apply": False,
        "defect_description": "IfcWall has no material association via IfcRelAssociatesMaterial",
        "repair_action": "Flag wall as missing material — requires manual material assignment",
        "explanation": "Material is needed for quantity takeoff and thermal analysis. Cannot safely auto-assign."
    },
    {
        "case_id": "CASE_027", "defect_type": "missing_material", "entity_type": "IfcSlab",
        "severity": "medium", "safe_to_auto_apply": False,
        "defect_description": "IfcSlab has no material association via IfcRelAssociatesMaterial",
        "repair_action": "Flag slab as missing material — requires manual material assignment",
        "explanation": "Material is essential for structural analysis. Cannot safely auto-assign."
    },
    {
        "case_id": "CASE_028", "defect_type": "missing_material", "entity_type": "IfcColumn",
        "severity": "medium", "safe_to_auto_apply": False,
        "defect_description": "IfcColumn has no material association via IfcRelAssociatesMaterial",
        "repair_action": "Flag column as missing material — requires manual material assignment",
        "explanation": "Structural elements must have material for analysis."
    },
    # ── Additional property cases for richer retrieval ──
    {
        "case_id": "CASE_029", "defect_type": "missing_property", "entity_type": "IfcWall",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "IfcWall is missing the 'Reference' property in Pset_WallCommon",
        "property_set": "Pset_WallCommon", "property_name": "Reference",
        "default_value": "", "value_type": "IfcIdentifier",
        "repair_action": "Add property 'Reference' with empty value to Pset_WallCommon",
        "explanation": "Reference links to type catalog. Empty string is safe placeholder."
    },
    {
        "case_id": "CASE_030", "defect_type": "missing_property", "entity_type": "IfcDoor",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "IfcDoor is missing the 'Reference' property in Pset_DoorCommon",
        "property_set": "Pset_DoorCommon", "property_name": "Reference",
        "default_value": "", "value_type": "IfcIdentifier",
        "repair_action": "Add property 'Reference' with empty value to Pset_DoorCommon",
        "explanation": "Reference links to type catalog. Empty string is safe placeholder."
    },
    {
        "case_id": "CASE_031", "defect_type": "missing_property", "entity_type": "IfcSlab",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcSlab is missing 'FireRating' property in Pset_SlabCommon",
        "property_set": "Pset_SlabCommon", "property_name": "FireRating",
        "default_value": "", "value_type": "IfcLabel",
        "repair_action": "Add property 'FireRating' with empty value to Pset_SlabCommon",
        "explanation": "FireRating is required for fire safety compliance."
    },
    {
        "case_id": "CASE_032", "defect_type": "missing_property", "entity_type": "IfcWindow",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcWindow is missing 'FireRating' property in Pset_WindowCommon",
        "property_set": "Pset_WindowCommon", "property_name": "FireRating",
        "default_value": "", "value_type": "IfcLabel",
        "repair_action": "Add property 'FireRating' with empty value to Pset_WindowCommon",
        "explanation": "FireRating needed for glazing compliance checks."
    },
    {
        "case_id": "CASE_033", "defect_type": "missing_property", "entity_type": "IfcColumn",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcColumn is missing 'IsExternal' property in Pset_ColumnCommon",
        "property_set": "Pset_ColumnCommon", "property_name": "IsExternal",
        "default_value": False, "value_type": "IfcBoolean",
        "repair_action": "Add property 'IsExternal' with value FALSE to Pset_ColumnCommon",
        "explanation": "IsExternal differentiates exposure. Default FALSE assumes interior."
    },
    {
        "case_id": "CASE_034", "defect_type": "missing_property", "entity_type": "IfcBeam",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "IfcBeam is missing 'IsExternal' property in Pset_BeamCommon",
        "property_set": "Pset_BeamCommon", "property_name": "IsExternal",
        "default_value": False, "value_type": "IfcBoolean",
        "repair_action": "Add property 'IsExternal' with value FALSE to Pset_BeamCommon",
        "explanation": "IsExternal classifies beam exposure. Default FALSE is safe."
    },
    # ── Duplicate name cases ──
    {
        "case_id": "CASE_035", "defect_type": "naming_inconsistency", "entity_type": "IfcWall",
        "severity": "low", "safe_to_auto_apply": True,
        "defect_description": "Multiple IfcWall entities share the same Name value",
        "repair_action": "Append unique index suffix to duplicate wall names",
        "explanation": "Duplicate names cause confusion in schedules. Adding index makes them unique."
    },
    {
        "case_id": "CASE_036", "defect_type": "naming_inconsistency", "entity_type": "IfcBuildingStorey",
        "severity": "medium", "safe_to_auto_apply": True,
        "defect_description": "Multiple IfcBuildingStorey entities share the same Name value",
        "repair_action": "Append unique index suffix to duplicate storey names",
        "explanation": "Duplicate storey names break spatial navigation. Must be unique."
    },
]


def generate_case_library():
    """Generate the case library JSON file."""
    output_path = os.path.join(DATA_DIR, "case_library.json")
    
    # Enrich cases with computed fields
    for case in CASES:
        # Build searchable text for TF-IDF
        case["search_text"] = " ".join([
            case.get("defect_type", ""),
            case.get("entity_type", ""),
            case.get("defect_description", ""),
            case.get("repair_action", ""),
            case.get("property_set", ""),
            case.get("property_name", ""),
        ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(CASES, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(CASES)} cases -> {output_path}")
    return output_path


if __name__ == "__main__":
    generate_case_library()
