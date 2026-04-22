"""
BIMRepair — Sample IFC Model Generator
Creates a minimal IFC4 model with intentional defects for testing.
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATA_DIR

try:
    import ifcopenshell
    import ifcopenshell.api
    HAS_IFC = True
except ImportError:
    HAS_IFC = False


def new_guid():
    return ifcopenshell.guid.compress(uuid.uuid4().hex)


def generate_sample_ifc():
    """Create a minimal IFC4 model with seeded defects."""
    if not HAS_IFC:
        print("ifcopenshell not installed. Generating fallback IFC manually.")
        return generate_fallback_ifc()

    model = ifcopenshell.api.run("project.create_file", version="IFC4")

    # ── Project hierarchy ──
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="BIMRepair Demo")
    
    # Units
    ifcopenshell.api.run("unit.assign_unit", model)
    
    # Context
    ctx = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body = ifcopenshell.api.run("context.add_context", model,
        context_type="Model", context_identifier="Body",
        target_view="MODEL_VIEW", parent=ctx)

    # Site
    site = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSite", name="Demo Site")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=project, products=[site])

    # Building
    building = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuilding", name="Demo Building")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=site, products=[building])

    # Storeys
    storey1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Ground Floor")
    storey1.Elevation = 0.0
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey1])

    storey2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="First Floor")
    storey2.Elevation = 3000.0
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=building, products=[storey2])

    # DEFECT: Disconnected storey (not aggregated to building)
    storey3 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Roof Level")
    storey3.Elevation = 6000.0
    # Intentionally NOT aggregating storey3 to building

    # ── Walls ──
    # Good wall with properties
    wall1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall_001")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[wall1])
    pset1 = ifcopenshell.api.run("pset.add_pset", model, product=wall1, name="Pset_WallCommon")
    ifcopenshell.api.run("pset.edit_pset", model, pset=pset1, properties={
        "LoadBearing": True, "IsExternal": True, "FireRating": "REI60"
    })

    # DEFECT: Wall missing properties
    wall2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall_002")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[wall2])
    # No Pset_WallCommon — missing properties

    # DEFECT: Wall with empty name
    wall3 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[wall3])

    # DEFECT: Wall not contained in any storey
    wall4 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall_004")
    # Intentionally NOT assigning spatial container

    # Wall on second floor
    wall5 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWall", name="Wall_005")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey2, products=[wall5])

    # ── Slabs ──
    slab1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="Slab_001")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[slab1])
    pset_slab = ifcopenshell.api.run("pset.add_pset", model, product=slab1, name="Pset_SlabCommon")
    ifcopenshell.api.run("pset.edit_pset", model, pset=pset_slab, properties={
        "LoadBearing": True, "IsExternal": False
    })

    # DEFECT: Slab with no container and no properties
    slab2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSlab", name="")
    # No container, no properties, empty name

    # ── Doors ──
    door1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcDoor", name="Door_001")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[door1])

    # DEFECT: Door with no name, no container
    door2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcDoor", name="")
    # No container

    # ── Windows ──
    window1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcWindow", name="Window_001")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[window1])

    # ── Columns ──
    col1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcColumn", name="Column_001")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[col1])

    # ── Spaces ──
    space1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSpace", name="Office_001")
    ifcopenshell.api.run("aggregate.assign_object", model, relating_object=storey1, products=[space1])

    # DEFECT: Space not in any storey
    space2 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSpace", name="")
    # Not aggregated to any storey

    # ── Beams ──
    beam1 = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcBeam", name="Beam_001")
    ifcopenshell.api.run("spatial.assign_container", model, relating_structure=storey1, products=[beam1])

    # Save
    output_path = os.path.join(DATA_DIR, "sample_model.ifc")
    model.write(output_path)
    print(f"Generated sample IFC -> {output_path}")
    print("Seeded defects:")
    print("  - Storey 'Roof Level' not connected to building")
    print("  - Wall_002 missing Pset_WallCommon properties")
    print("  - Wall with empty name")
    print("  - Wall_004 not in any storey")
    print("  - Slab with no container, no properties, empty name")
    print("  - Door with empty name, no container")
    print("  - Space not in any storey, empty name")
    print("  - Multiple elements missing material associations")
    print("  - Multiple elements missing standard property sets")
    return output_path


def generate_fallback_ifc():
    """Generate a minimal IFC file as plain text if ifcopenshell isn't available."""
    output_path = os.path.join(DATA_DIR, "sample_model.ifc")
    content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('sample_model.ifc','2024-01-01',('BIMRepair'),('BIMRepair'),'ifcopenshell','BIMRepair','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0001',#2,'BIMRepair Demo',$,$,$,$,$,#8);
#2=IFCOWNERHISTORY(#3,#6,$,.ADDED.,$,$,$,0);
#3=IFCPERSONANDORGANIZATION(#4,#5,$);
#4=IFCPERSON($,'BIMRepair',$,$,$,$,$,$);
#5=IFCORGANIZATION($,'BIMRepair',$,$,$);
#6=IFCAPPLICATION(#5,'1.0','BIMRepair','BIMRepair');
#7=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#8=IFCUNITASSIGNMENT((#7));
#10=IFCSITE('0010',#2,'Demo Site',$,$,$,$,$,.ELEMENT.,$,$,$,$,$);
#11=IFCBUILDING('0011',#2,'Demo Building',$,$,$,$,$,.ELEMENT.,$,$,$);
#12=IFCBUILDINGSTOREY('0012',#2,'Ground Floor',$,$,$,$,$,.ELEMENT.,0.0);
#13=IFCBUILDINGSTOREY('0013',#2,'First Floor',$,$,$,$,$,.ELEMENT.,3000.0);
#14=IFCBUILDINGSTOREY('0014',#2,'Roof Level',$,$,$,$,$,.ELEMENT.,6000.0);
#20=IFCRELAGGREGATES('0020',#2,$,$,#1,(#10));
#21=IFCRELAGGREGATES('0021',#2,$,$,#10,(#11));
#22=IFCRELAGGREGATES('0022',#2,$,$,#11,(#12,#13));
#30=IFCWALL('0030',#2,'Wall_001',$,$,$,$,$,$);
#31=IFCWALL('0031',#2,'Wall_002',$,$,$,$,$,$);
#32=IFCWALL('0032',#2,'',$,$,$,$,$,$);
#33=IFCWALL('0033',#2,'Wall_004',$,$,$,$,$,$);
#40=IFCSLAB('0040',#2,'Slab_001',$,$,$,$,$,$,$);
#41=IFCSLAB('0041',#2,'',$,$,$,$,$,$,$);
#50=IFCDOOR('0050',#2,'Door_001',$,$,$,$,$,$,$,$);
#51=IFCDOOR('0051',#2,'',$,$,$,$,$,$,$,$);
#60=IFCWINDOW('0060',#2,'Window_001',$,$,$,$,$,$,$,$);
#70=IFCCOLUMN('0070',#2,'Column_001',$,$,$,$,$,$);
#80=IFCBEAM('0080',#2,'Beam_001',$,$,$,$,$,$);
#90=IFCSPACE('0090',#2,'Office_001',$,$,$,$,$,.ELEMENT.,$,$);
#91=IFCSPACE('0091',#2,'',$,$,$,$,$,.ELEMENT.,$,$);
#100=IFCRELCONTAINEDINSPATIALSTRUCTURE('0100',#2,$,$,(#30,#31,#32),#12);
#101=IFCRELCONTAINEDINSPATIALSTRUCTURE('0101',#2,$,$,(#40,#50,#60,#70,#80),#12);
#102=IFCRELAGGREGATES('0102',#2,$,$,#12,(#90));
ENDSEC;
END-ISO-10303-21;
"""
    with open(output_path, "w") as f:
        f.write(content)
    print(f"Generated fallback IFC -> {output_path}")
    return output_path


if __name__ == "__main__":
    generate_sample_ifc()
