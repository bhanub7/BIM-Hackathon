"""
BIMRepair — Repair Applier
Applies validated repair proposals to the IFC model using ifcopenshell.api.
"""
import logging
import ifcopenshell
import ifcopenshell.api

from src.ifc_parser import (
    get_first_storey, get_first_building, extract_property_sets,
    get_spatial_container, get_aggregation_parent,
)

logger = logging.getLogger(__name__)

# Track name counters for unique naming
_name_counters = {}


def apply_repair(model, proposal):
    """
    Apply a validated repair proposal to the IFC model.
    
    Returns:
        dict with status and details
    """
    dtype = proposal.defect_type
    params = proposal.repair_params
    
    try:
        entity = model.by_id(params["entity_id"])
    except Exception as e:
        logger.error(f"Cannot find entity {params['entity_id']}: {e}")
        return {"status": "error", "message": str(e)}
    
    try:
        if dtype == "missing_property":
            return _apply_property_repair(model, entity, params)
        elif dtype == "broken_spatial_containment":
            return _apply_containment_repair(model, entity, params)
        elif dtype == "disconnected_storey":
            return _apply_aggregation_repair(model, entity, params)
        elif dtype == "invalid_parent_child":
            return _apply_parent_child_repair(model, entity, params)
        elif dtype == "naming_inconsistency":
            return _apply_naming_repair(model, entity, params)
        elif dtype == "missing_material":
            return {"status": "flagged", "message": "Material requires manual assignment"}
        else:
            return {"status": "skipped", "message": f"Unknown defect type: {dtype}"}
    except Exception as e:
        logger.error(f"Repair failed for {proposal.defect_id}: {e}")
        return {"status": "error", "message": str(e)}


def _apply_property_repair(model, entity, params):
    """Add a missing property to a property set."""
    pset_name = params["property_set"]
    prop_name = params["property_name"]
    default_value = params["default_value"]
    
    # Find existing pset or create new one
    existing_pset = None
    for rel in model.by_type("IfcRelDefinesByProperties"):
        if entity in rel.RelatedObjects:
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet") and pdef.Name == pset_name:
                existing_pset = pdef
                break
    
    if existing_pset is None:
        # Create new property set
        existing_pset = ifcopenshell.api.run("pset.add_pset", model,
                                              product=entity, name=pset_name)
    
    # Add the property
    ifcopenshell.api.run("pset.edit_pset", model, pset=existing_pset,
                          properties={prop_name: default_value})
    
    logger.info(f"Added {pset_name}.{prop_name} = {default_value} to {entity.Name or entity.GlobalId}")
    return {
        "status": "applied",
        "message": f"Added {prop_name} = {default_value} to {pset_name}",
        "before": f"{pset_name}.{prop_name} = MISSING",
        "after": f"{pset_name}.{prop_name} = {default_value}",
    }


def _apply_containment_repair(model, entity, params):
    """Assign element to the first available storey."""
    # Check if already contained
    existing = get_spatial_container(model, entity)
    if existing is not None:
        return {"status": "skipped", "message": "Already contained"}
    
    storey = get_first_storey(model)
    if storey is None:
        return {"status": "error", "message": "No storey available"}
    
    ifcopenshell.api.run("spatial.assign_container", model,
                          relating_structure=storey, products=[entity])
    
    logger.info(f"Assigned {entity.Name or entity.GlobalId} to storey {storey.Name}")
    return {
        "status": "applied",
        "message": f"Contained in {storey.Name}",
        "before": "No spatial container",
        "after": f"Contained in {storey.Name}",
    }


def _apply_aggregation_repair(model, entity, params):
    """Reconnect a storey to a building or building to site."""
    existing = get_aggregation_parent(model, entity)
    if existing is not None:
        return {"status": "skipped", "message": "Already aggregated"}
    
    if entity.is_a("IfcBuildingStorey"):
        building = get_first_building(model)
        if building is None:
            return {"status": "error", "message": "No building available"}
        
        ifcopenshell.api.run("aggregate.assign_object", model,
                              relating_object=building, products=[entity])
        
        logger.info(f"Aggregated storey {entity.Name} to building {building.Name}")
        return {
            "status": "applied",
            "message": f"Aggregated to {building.Name}",
            "before": "Not aggregated to any building",
            "after": f"Aggregated to {building.Name}",
        }
    
    elif entity.is_a("IfcBuilding"):
        sites = list(model.by_type("IfcSite"))
        if not sites:
            return {"status": "error", "message": "No site available"}
        
        ifcopenshell.api.run("aggregate.assign_object", model,
                              relating_object=sites[0], products=[entity])
        
        logger.info(f"Aggregated building {entity.Name} to site {sites[0].Name}")
        return {
            "status": "applied",
            "message": f"Aggregated to {sites[0].Name}",
            "before": "Not aggregated to any site",
            "after": f"Aggregated to {sites[0].Name}",
        }
    
    return {"status": "skipped", "message": "Unsupported entity type for aggregation"}


def _apply_parent_child_repair(model, entity, params):
    """Assign space to the first available storey."""
    existing = get_aggregation_parent(model, entity)
    if existing is not None and existing.is_a("IfcBuildingStorey"):
        return {"status": "skipped", "message": "Already in a storey"}
    
    storey = get_first_storey(model)
    if storey is None:
        return {"status": "error", "message": "No storey available"}
    
    ifcopenshell.api.run("aggregate.assign_object", model,
                          relating_object=storey, products=[entity])
    
    logger.info(f"Assigned space {entity.Name or entity.GlobalId} to storey {storey.Name}")
    return {
        "status": "applied",
        "message": f"Assigned to {storey.Name}",
        "before": "Not in any storey",
        "after": f"Aggregated to {storey.Name}",
    }


def _apply_naming_repair(model, entity, params):
    """Fix empty or duplicate names."""
    issue = params.get("issue", "empty_name")
    entity_type = entity.is_a()
    old_name = entity.Name
    
    if issue == "empty_name":
        # Generate a name from type + ID
        type_short = entity_type.replace("Ifc", "")
        key = entity_type
        if key not in _name_counters:
            _name_counters[key] = 0
        _name_counters[key] += 1
        new_name = f"{type_short}_{_name_counters[key]:03d}"
        entity.Name = new_name
        
        logger.info(f"Renamed {entity.GlobalId}: '{old_name}' -> '{new_name}'")
        return {
            "status": "applied",
            "message": f"Named as {new_name}",
            "before": f"Name = '{old_name}'",
            "after": f"Name = '{new_name}'",
        }
    
    elif issue == "duplicate_name":
        # Append entity ID to make unique
        new_name = f"{old_name}_{entity.id()}"
        entity.Name = new_name
        
        logger.info(f"De-duplicated {entity.GlobalId}: '{old_name}' -> '{new_name}'")
        return {
            "status": "applied",
            "message": f"Renamed to {new_name}",
            "before": f"Name = '{old_name}' (duplicate)",
            "after": f"Name = '{new_name}'",
        }
    
    return {"status": "skipped", "message": "Unknown naming issue"}
