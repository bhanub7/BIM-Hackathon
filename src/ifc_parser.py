"""
BIMRepair — IFC Parser
Loads IFC files and extracts entities, relationships, properties, and spatial hierarchy.
"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def load_model(path):
    """Load an IFC model from file path."""
    import ifcopenshell
    logger.info(f"Loading IFC model: {path}")
    model = ifcopenshell.open(path)
    schema = model.schema
    logger.info(f"Loaded model with schema {schema}, {len(list(model))} entities")
    return model


def extract_entities(model, entity_types=None):
    """Extract all relevant building entities as structured dicts."""
    if entity_types is None:
        entity_types = [
            "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow",
            "IfcColumn", "IfcBeam", "IfcSpace",
            "IfcBuildingStorey", "IfcBuilding", "IfcSite",
        ]
    
    entities = []
    for etype in entity_types:
        for entity in model.by_type(etype):
            info = {
                "id": entity.id(),
                "global_id": entity.GlobalId,
                "type": entity.is_a(),
                "name": entity.Name if hasattr(entity, "Name") else None,
                "description": entity.Description if hasattr(entity, "Description") else None,
                "entity": entity,  # Keep reference for repair
            }
            entities.append(info)
    
    logger.info(f"Extracted {len(entities)} entities")
    return entities


def extract_property_sets(model, entity):
    """Extract all property sets and their properties for an entity."""
    psets = {}
    
    # Get through IfcRelDefinesByProperties
    for rel in model.by_type("IfcRelDefinesByProperties"):
        if entity in rel.RelatedObjects:
            pset_def = rel.RelatingPropertyDefinition
            if pset_def.is_a("IfcPropertySet"):
                props = {}
                for prop in pset_def.HasProperties:
                    if prop.is_a("IfcPropertySingleValue"):
                        val = prop.NominalValue.wrappedValue if prop.NominalValue else None
                        props[prop.Name] = val
                psets[pset_def.Name] = props
    
    return psets


def get_spatial_container(model, entity):
    """Get the spatial structure element that contains this entity."""
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        if entity in rel.RelatedElements:
            return rel.RelatingStructure
    return None


def get_aggregation_parent(model, entity):
    """Get the parent element via IfcRelAggregates."""
    for rel in model.by_type("IfcRelAggregates"):
        if entity in rel.RelatedObjects:
            return rel.RelatingObject
    return None


def extract_spatial_hierarchy(model):
    """Build the full spatial hierarchy tree."""
    hierarchy = {"sites": []}
    
    for site in model.by_type("IfcSite"):
        site_data = {"entity": site, "name": site.Name, "buildings": []}
        
        for rel in model.by_type("IfcRelAggregates"):
            if rel.RelatingObject == site:
                for child in rel.RelatedObjects:
                    if child.is_a("IfcBuilding"):
                        bldg_data = {"entity": child, "name": child.Name, "storeys": []}
                        
                        for rel2 in model.by_type("IfcRelAggregates"):
                            if rel2.RelatingObject == child:
                                for storey in rel2.RelatedObjects:
                                    if storey.is_a("IfcBuildingStorey"):
                                        storey_data = {
                                            "entity": storey,
                                            "name": storey.Name,
                                            "elevation": storey.Elevation if hasattr(storey, "Elevation") else None,
                                            "elements": [],
                                            "spaces": [],
                                        }
                                        # Get contained elements
                                        for rel3 in model.by_type("IfcRelContainedInSpatialStructure"):
                                            if rel3.RelatingStructure == storey:
                                                for elem in rel3.RelatedElements:
                                                    storey_data["elements"].append({
                                                        "entity": elem,
                                                        "type": elem.is_a(),
                                                        "name": elem.Name,
                                                    })
                                        # Get aggregated spaces
                                        for rel3 in model.by_type("IfcRelAggregates"):
                                            if rel3.RelatingObject == storey:
                                                for space in rel3.RelatedObjects:
                                                    if space.is_a("IfcSpace"):
                                                        storey_data["spaces"].append({
                                                            "entity": space,
                                                            "name": space.Name,
                                                        })
                                        bldg_data["storeys"].append(storey_data)
                        
                        site_data["buildings"].append(bldg_data)
        
        hierarchy["sites"].append(site_data)
    
    return hierarchy


def get_material_associations(model, entity):
    """Check if entity has material associations."""
    for rel in model.by_type("IfcRelAssociatesMaterial"):
        if entity in rel.RelatedObjects:
            return rel.RelatingMaterial
    return None


def get_all_storeys(model):
    """Get all building storeys in the model."""
    return list(model.by_type("IfcBuildingStorey"))


def get_all_buildings(model):
    """Get all buildings in the model."""
    return list(model.by_type("IfcBuilding"))


def get_first_storey(model):
    """Get the first available storey (for fallback assignment)."""
    storeys = get_all_storeys(model)
    return storeys[0] if storeys else None


def get_first_building(model):
    """Get the first available building."""
    buildings = get_all_buildings(model)
    return buildings[0] if buildings else None
