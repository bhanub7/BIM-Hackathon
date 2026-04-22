"""
BIMRepair - Parametric Synthetic Dataset Generator
Produces 500+ diverse defect->repair case pairs for training and retrieval.
"""
import json, csv, os, sys, random, uuid, hashlib
from itertools import product as cartprod

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATA_DIR

random.seed(42)

# ---------------------------------------------------------------------------
# Template pools
# ---------------------------------------------------------------------------
ELEMENT_TYPES = ["IfcWall","IfcSlab","IfcDoor","IfcWindow","IfcColumn","IfcBeam",
                 "IfcCurtainWall","IfcStair","IfcRamp","IfcRailing","IfcRoof",
                 "IfcFooting","IfcPile","IfcPlate","IfcMember"]

SPATIAL_TYPES = ["IfcSpace","IfcBuildingStorey","IfcBuilding","IfcSite"]

PSET_MAP = {
    "IfcWall":        ("Pset_WallCommon",    ["LoadBearing","IsExternal","FireRating","Reference","ThermalTransmittance","AcousticRating","Combustible","SurfaceSpreadOfFlame","ExtendToStructure"]),
    "IfcSlab":        ("Pset_SlabCommon",    ["LoadBearing","IsExternal","FireRating","Reference","ThermalTransmittance","AcousticRating","Combustible","PitchAngle"]),
    "IfcDoor":        ("Pset_DoorCommon",    ["FireRating","IsExternal","Reference","AcousticRating","SecurityRating","HandicapAccessible","FireExit","SmokeStop","SelfClosing"]),
    "IfcWindow":      ("Pset_WindowCommon",  ["FireRating","IsExternal","Reference","AcousticRating","ThermalTransmittance","GlazingAreaFraction","SmokeStop"]),
    "IfcColumn":      ("Pset_ColumnCommon",  ["LoadBearing","IsExternal","FireRating","Reference","Slope"]),
    "IfcBeam":        ("Pset_BeamCommon",    ["LoadBearing","IsExternal","FireRating","Reference","Slope","Span"]),
    "IfcCurtainWall": ("Pset_CurtainWallCommon",["IsExternal","FireRating","Reference","ThermalTransmittance","AcousticRating"]),
    "IfcStair":       ("Pset_StairCommon",   ["FireRating","IsExternal","Reference","NumberOfRiser","NumberOfTreads","HandicapAccessible"]),
    "IfcRamp":        ("Pset_RampCommon",    ["FireRating","IsExternal","Reference","HandicapAccessible"]),
    "IfcRoof":        ("Pset_RoofCommon",    ["IsExternal","FireRating","Reference","ThermalTransmittance","ProjectedArea"]),
    "IfcFooting":     ("Pset_FootingCommon", ["LoadBearing","Reference"]),
    "IfcRailing":     ("Pset_RailingCommon", ["IsExternal","Reference","Height"]),
}

BOOL_PROPS = {"LoadBearing","IsExternal","Combustible","FireExit","SmokeStop",
              "SelfClosing","HandicapAccessible","ExtendToStructure"}
NUM_PROPS  = {"ThermalTransmittance","AcousticRating","GlazingAreaFraction",
              "Slope","Span","PitchAngle","NumberOfRiser","NumberOfTreads",
              "ProjectedArea","Height"}
STR_PROPS  = {"FireRating","Reference","SecurityRating","SurfaceSpreadOfFlame"}

FIRE_RATINGS = ["","REI30","REI60","REI90","REI120","EI30","EI60","EI90","E30","E60"]
MATERIALS = ["Concrete","Steel","Timber","Masonry","Glass","Aluminium",
             "Brick","Gypsum","Composite","Precast Concrete","Stone"]
STOREY_NAMES = ["Basement 2","Basement 1","Ground Floor","Level 01","Level 02",
                "Level 03","Level 04","Level 05","Mezzanine","Roof Level","Penthouse"]
SPACE_NAMES  = ["Office","Corridor","Stairwell","Lobby","Bathroom","Kitchen",
                "Meeting Room","Server Room","Storage","Plant Room","Reception",
                "Elevator Shaft","Parking","Loading Dock","Mechanical Room"]

CLASH_PAIRS = [("IfcWall","IfcColumn"),("IfcWall","IfcBeam"),("IfcSlab","IfcColumn"),
               ("IfcWall","IfcWall"),("IfcBeam","IfcBeam"),("IfcSlab","IfcBeam"),
               ("IfcDoor","IfcWall"),("IfcWindow","IfcColumn"),("IfcColumn","IfcColumn"),
               ("IfcWall","IfcDoor"),("IfcSlab","IfcWall"),("IfcBeam","IfcColumn")]

# ---------------------------------------------------------------------------
# Helper: random geometry bbox
# ---------------------------------------------------------------------------
def _rand_bbox(base_x=0, base_y=0, base_z=0, w_range=(0.2,6), d_range=(0.2,6), h_range=(0.3,4)):
    w = round(random.uniform(*w_range),2)
    d = round(random.uniform(*d_range),2)
    h = round(random.uniform(*h_range),2)
    x = round(base_x + random.uniform(-10,10),2)
    y = round(base_y + random.uniform(-10,10),2)
    z = round(base_z,2)
    return {"min":[x,y,z],"max":[round(x+w,2),round(y+d,2),round(z+h,2)]}

def _rand_guid():
    return hashlib.md5(uuid.uuid4().bytes).hexdigest()[:22]

def _default_for_prop(p):
    if p in BOOL_PROPS:   return random.choice([True,False])
    if p in NUM_PROPS:    return round(random.uniform(0.1,5.0),2)
    if p in STR_PROPS:
        if p=="FireRating": return random.choice(FIRE_RATINGS)
        return ""
    return ""

# ---------------------------------------------------------------------------
# Case generators by defect family
# ---------------------------------------------------------------------------
ALL_CASES = []

def _add(c):
    c["case_id"] = f"SC_{len(ALL_CASES)+1:04d}"
    # build search text
    c["search_text"] = " ".join(filter(None,[
        c.get("defect_type",""), c.get("entity_type",""),
        c.get("defect_description",""), c.get("repair_action",""),
        c.get("property_set",""), c.get("property_name",""),
        " ".join(c.get("element_types",[])),
    ]))
    ALL_CASES.append(c)


def gen_missing_property_cases():
    """Generate missing-property cases for every entity-type x property combo."""
    for etype, (pset, props) in PSET_MAP.items():
        for prop in props:
            dv = _default_for_prop(prop)
            guid = _rand_guid()
            sev = "high" if prop=="LoadBearing" else ("medium" if prop in ("FireRating","IsExternal") else "low")
            _add({
                "defect_type":"missing_property","entity_type":etype,
                "element_types":[etype],"severity":sev,"safe_to_auto_apply":True,
                "defect_description":f"{etype} is missing '{prop}' in {pset}",
                "property_set":pset,"property_name":prop,
                "default_value":dv,"value_type":"IfcBoolean" if prop in BOOL_PROPS else ("IfcReal" if prop in NUM_PROPS else "IfcLabel"),
                "repair_action":f"Add property '{prop}' with default value to {pset}",
                "explanation":f"{prop} is required by IFC schema for {etype}. A safe default is applied.",
                "geometry_context":_rand_bbox(),
                "property_context":{"pset":pset,"existing_props":random.sample(props,min(3,len(props)))},
                "relationship_context":{"container":"IfcBuildingStorey","storey":random.choice(STOREY_NAMES)},
                "before_state":{"entity":etype,"guid":guid,"pset":pset,"properties":{p:_default_for_prop(p) for p in props if p!=prop}},
                "after_state":{"entity":etype,"guid":guid,"pset":pset,"properties":{p:(_default_for_prop(p) if p!=prop else dv) for p in props}},
            })


def gen_broken_containment_cases():
    """Elements not in any storey."""
    for etype in ELEMENT_TYPES[:10]:
        for storey in random.sample(STOREY_NAMES,min(4,len(STOREY_NAMES))):
            guid = _rand_guid()
            name = f"{etype.replace('Ifc','')}_{random.randint(1,999):03d}"
            _add({
                "defect_type":"broken_spatial_containment","entity_type":etype,
                "element_types":[etype,"IfcBuildingStorey"],"severity":"high",
                "safe_to_auto_apply":True,
                "defect_description":f"{etype} '{name}' is not contained in any IfcBuildingStorey",
                "repair_action":f"Create IfcRelContainedInSpatialStructure linking element to '{storey}'",
                "explanation":"Every physical element must be spatially contained for coordination.",
                "geometry_context":_rand_bbox(base_z=STOREY_NAMES.index(storey)*3.0),
                "property_context":{"element_name":name},
                "relationship_context":{"missing":"IfcRelContainedInSpatialStructure","target_storey":storey},
                "before_state":{"entity":etype,"guid":guid,"name":name,"container":None},
                "after_state":{"entity":etype,"guid":guid,"name":name,"container":storey},
            })


def gen_disconnected_storey_cases():
    """Storeys not linked to building."""
    for storey in STOREY_NAMES:
        guid = _rand_guid()
        elev = round(STOREY_NAMES.index(storey)*3.0 - 6.0, 1)
        _add({
            "defect_type":"disconnected_storey","entity_type":"IfcBuildingStorey",
            "element_types":["IfcBuildingStorey","IfcBuilding"],"severity":"critical",
            "safe_to_auto_apply":True,
            "defect_description":f"IfcBuildingStorey '{storey}' not aggregated into any IfcBuilding",
            "repair_action":"Create IfcRelAggregates linking storey to building",
            "explanation":"Storeys must be children of a building in the spatial hierarchy.",
            "geometry_context":{"elevation":elev,"storey_name":storey},
            "property_context":{"elevation":elev},
            "relationship_context":{"missing":"IfcRelAggregates","parent_type":"IfcBuilding"},
            "before_state":{"entity":"IfcBuildingStorey","guid":guid,"name":storey,"parent":None,"elevation":elev},
            "after_state":{"entity":"IfcBuildingStorey","guid":guid,"name":storey,"parent":"Demo Building","elevation":elev},
        })


def gen_invalid_parent_child_cases():
    """Spaces not in correct storey or not in any storey."""
    for space_name in SPACE_NAMES:
        for storey in random.sample(STOREY_NAMES,2):
            guid = _rand_guid()
            # Case 1: not in any storey
            _add({
                "defect_type":"invalid_parent_child","entity_type":"IfcSpace",
                "element_types":["IfcSpace","IfcBuildingStorey"],"severity":"high",
                "safe_to_auto_apply":True,
                "defect_description":f"IfcSpace '{space_name}' not aggregated into any storey",
                "repair_action":f"Aggregate space into storey '{storey}'",
                "explanation":"Spaces must belong to a storey for room-based analysis.",
                "geometry_context":_rand_bbox(base_z=STOREY_NAMES.index(storey)*3.0,w_range=(3,8),d_range=(3,8),h_range=(2.5,3.5)),
                "property_context":{"space_name":space_name,"long_name":f"{space_name} {random.randint(100,999)}"},
                "relationship_context":{"missing":"IfcRelAggregates","target_storey":storey},
                "before_state":{"entity":"IfcSpace","guid":guid,"name":space_name,"parent":None},
                "after_state":{"entity":"IfcSpace","guid":guid,"name":space_name,"parent":storey},
            })
            # Case 2: wrong storey
            wrong = random.choice([s for s in STOREY_NAMES if s!=storey])
            _add({
                "defect_type":"wrong_level_assignment","entity_type":"IfcSpace",
                "element_types":["IfcSpace","IfcBuildingStorey"],"severity":"medium",
                "safe_to_auto_apply":False,
                "defect_description":f"IfcSpace '{space_name}' assigned to '{wrong}' but elevation matches '{storey}'",
                "repair_action":f"Reassign space from '{wrong}' to '{storey}' based on elevation",
                "explanation":"Space elevation should match its parent storey. Needs verification.",
                "geometry_context":_rand_bbox(base_z=STOREY_NAMES.index(storey)*3.0),
                "property_context":{"space_name":space_name},
                "relationship_context":{"current_storey":wrong,"correct_storey":storey},
                "before_state":{"entity":"IfcSpace","guid":guid,"name":space_name,"parent":wrong},
                "after_state":{"entity":"IfcSpace","guid":guid,"name":space_name,"parent":storey},
            })


def gen_naming_cases():
    """Empty, None, or duplicate names."""
    for etype in ELEMENT_TYPES + ["IfcSpace","IfcBuildingStorey"]:
        for variant in range(3):
            guid = _rand_guid()
            sev = "medium" if etype in SPATIAL_TYPES else "low"
            if variant == 0:
                desc = f"{etype} has empty Name attribute"
                issue = "empty_name"
                before_name = ""
            elif variant == 1:
                desc = f"{etype} has None Name attribute"
                issue = "empty_name"
                before_name = None
            else:
                dup_name = f"{etype.replace('Ifc','')}_001"
                desc = f"Multiple {etype} entities share name '{dup_name}'"
                issue = "duplicate_name"
                before_name = dup_name

            auto_name = f"{etype.replace('Ifc','')}_{random.randint(1,999):03d}"
            _add({
                "defect_type":"naming_inconsistency","entity_type":etype,
                "element_types":[etype],"severity":sev,
                "safe_to_auto_apply":True,
                "defect_description":desc,
                "repair_action":f"Set Name to '{auto_name}'",
                "explanation":"All elements need unique, meaningful names for schedules and coordination.",
                "geometry_context":_rand_bbox(),
                "property_context":{"issue":issue,"before_name":before_name},
                "relationship_context":{},
                "before_state":{"entity":etype,"guid":guid,"name":before_name},
                "after_state":{"entity":etype,"guid":guid,"name":auto_name},
            })


def gen_missing_material_cases():
    """Elements without material associations."""
    for etype in ["IfcWall","IfcSlab","IfcColumn","IfcBeam","IfcCurtainWall","IfcRoof","IfcFooting","IfcPlate","IfcMember"]:
        for mat in random.sample(MATERIALS,min(3,len(MATERIALS))):
            guid = _rand_guid()
            _add({
                "defect_type":"missing_material","entity_type":etype,
                "element_types":[etype],"severity":"medium",
                "safe_to_auto_apply":False,
                "defect_description":f"{etype} has no material association via IfcRelAssociatesMaterial",
                "repair_action":f"Flag for manual material assignment (suggested: {mat})",
                "explanation":f"Material needed for quantity takeoff and analysis. Suggested: {mat}.",
                "geometry_context":_rand_bbox(),
                "property_context":{"suggested_material":mat},
                "relationship_context":{"missing":"IfcRelAssociatesMaterial"},
                "before_state":{"entity":etype,"guid":guid,"material":None},
                "after_state":{"entity":etype,"guid":guid,"material":mat},
            })


def gen_clash_cases():
    """Geometry clashes between element pairs with resolved after states."""
    
    # Clash configurations with specific repair actions
    clash_scenarios = [
        # (TypeA, TypeB, ClashType, SafeAutoApply, RepairAction, Explanation, FixLogic)
        ("IfcWall", "IfcColumn", "hard", True, "Adjust wall length to abut column face", "Wall should stop at structural column face. Shortening wall geometry.", "shorten_a"),
        ("IfcWall", "IfcColumn", "overlap", False, "Flag for structural review", "Major overlap detected between wall and column. Needs engineer review.", "manual"),
        ("IfcWall", "IfcBeam", "hard", False, "Cut opening in wall for beam penetration", "Beam intersects wall. Opening profile required but needs MEP/Structural coordination.", "manual"),
        ("IfcSlab", "IfcColumn", "hard", True, "Create slab void around column profile", "Slab must flow around structural columns. Void geometry generated.", "void_a"),
        ("IfcWall", "IfcDoor", "misaligned", True, "Align door frame with wall opening", "Door geometry extends beyond wall thickness. Snapping to opening plane.", "align_b"),
        ("IfcBeam", "IfcSlab", "soft", False, "Adjust beam elevation to sit below slab", "Beam soffit intrudes slab. Elevation drop required.", "drop_a"),
        ("IfcSpace", "IfcSpace", "overlap", True, "Resolve space boundary overlap", "Spaces share overlapping volume. Splitting along centerline.", "split_both"),
        ("IfcDuctSegment", "IfcBeam", "hard", False, "Reroute duct below structural beam", "MEP element clashes with structural frame. Needs rerouting.", "manual"),
        ("IfcPipeSegment", "IfcWall", "near-miss", True, "Enlarge wall opening for pipe clearance", "Pipe lacks sufficient clearance. Opening expanded by 50mm.", "enlarge_void_b"),
        ("IfcWindow", "IfcWall", "misaligned", True, "Snap window to host wall face", "Window placement offset from host wall. Snapping to align.", "align_a")
    ]
    
    for (typeA, typeB, clash_type, safe_to_auto_apply, repair_action, explanation, fix_logic) in clash_scenarios:
        # Generate 15 variations for each scenario to reach 150 diverse clash cases
        for _ in range(15):
            guidA, guidB = _rand_guid(), _rand_guid()
            nameA = f"{typeA.replace('Ifc','')}_{random.randint(1,999):03d}"
            nameB = f"{typeB.replace('Ifc','')}_{random.randint(1,999):03d}"
            
            bboxA = _rand_bbox()
            
            # Generate the overlap/clash geometry based on the clash type
            if clash_type == "hard":
                overlap = round(random.uniform(0.1, 0.4), 2)
            elif clash_type in ("soft", "near-miss"):
                overlap = round(random.uniform(0.01, 0.05), 2)
            else: # overlap or misaligned
                overlap = round(random.uniform(0.2, 0.8), 2)
                
            bboxB = {
                "min": [bboxA["max"][0] - overlap, bboxA["min"][1], bboxA["min"][2] + round(random.uniform(-0.1, 0.1), 2)],
                "max": [bboxA["max"][0] - overlap + 2, bboxA["max"][1] + 2, bboxA["max"][2] + 1]
            }
            
            # Compute the AFTER state geometry based on the fix logic
            after_bboxA = {"min": list(bboxA["min"]), "max": list(bboxA["max"])}
            after_bboxB = {"min": list(bboxB["min"]), "max": list(bboxB["max"])}
            
            repair_action_specific = repair_action
            
            if fix_logic == "shorten_a":
                after_bboxA["max"][0] = bboxB["min"][0]
                repair_action_specific = f"{repair_action} (adjusted length by -{overlap}m)"
            elif fix_logic == "void_a":
                # Slab void logic, represented by a void property for simplicity
                repair_action_specific = f"{repair_action} (void size: {round(bboxB['max'][0]-bboxB['min'][0],2)}x{round(bboxB['max'][1]-bboxB['min'][1],2)}m)"
            elif fix_logic == "align_b" or fix_logic == "align_a":
                # Snap B to A's plane
                after_bboxB["min"][0] = bboxA["min"][0]
                repair_action_specific = f"{repair_action} (snapped +{overlap}m)"
            elif fix_logic == "drop_a":
                after_bboxA["max"][2] = bboxB["min"][2]
                after_bboxA["min"][2] = bboxB["min"][2] - 0.5
                repair_action_specific = f"{repair_action} (dropped by {overlap}m)"
            elif fix_logic == "split_both":
                midpoint = bboxA["max"][0] - (overlap / 2)
                after_bboxA["max"][0] = midpoint
                after_bboxB["min"][0] = midpoint
                repair_action_specific = f"{repair_action} (split at x={midpoint:.2f})"
            elif fix_logic == "enlarge_void_b":
                after_bboxB["min"][0] -= 0.05
                after_bboxB["max"][0] += 0.05
                after_bboxB["min"][1] -= 0.05
                after_bboxB["max"][1] += 0.05
                repair_action_specific = f"{repair_action} (expanded by 50mm)"
                
            sev = "critical" if clash_type == "hard" else "high" if clash_type == "overlap" else "medium"
            storey = random.choice(STOREY_NAMES)
            
            _add({
                "defect_type": "geometry_clash",
                "entity_type": typeA,
                "element_types": [typeA, typeB],
                "severity": sev,
                "safe_to_auto_apply": safe_to_auto_apply,
                "defect_description": f"{clash_type.capitalize()} clash between {typeA} '{nameA}' and {typeB} '{nameB}' (overlap {overlap}m)",
                "repair_action": repair_action_specific,
                "explanation": explanation,
                "geometry_context": {
                    "element_a": {"type": typeA, "name": nameA, "bbox": bboxA},
                    "element_b": {"type": typeB, "name": nameB, "bbox": bboxB},
                    "overlap_distance": overlap,
                    "clash_type": clash_type
                },
                "property_context": {"storey": storey},
                "relationship_context": {"resolution": "automatic" if safe_to_auto_apply else "manual_review"},
                "before_state": {
                    "entities": [
                        {"type": typeA, "name": nameA, "bbox": bboxA},
                        {"type": typeB, "name": nameB, "bbox": bboxB}
                    ],
                    "clashing": True
                },
                "after_state": {
                    "entities": [
                        {"type": typeA, "name": nameA, "bbox": after_bboxA},
                        {"type": typeB, "name": nameB, "bbox": after_bboxB}
                    ],
                    "clashing": False if safe_to_auto_apply else True
                }
            })


def gen_invalid_reference_cases():
    """Broken references / orphan type objects."""
    for etype in ELEMENT_TYPES[:8]:
        guid = _rand_guid()
        type_name = etype + "Type"
        _add({
            "defect_type":"invalid_reference","entity_type":etype,
            "element_types":[etype,type_name],"severity":"medium",
            "safe_to_auto_apply":False,
            "defect_description":f"{etype} references a {type_name} that does not exist in the model",
            "repair_action":f"Remove broken type reference or create missing {type_name}",
            "explanation":"Orphan type references break downstream tools.",
            "geometry_context":_rand_bbox(),
            "property_context":{"broken_ref":type_name},
            "relationship_context":{"missing_target":type_name},
            "before_state":{"entity":etype,"guid":guid,"type_ref":"#INVALID"},
            "after_state":{"entity":etype,"guid":guid,"type_ref":None},
        })
        # Also: element referencing deleted owner history
        _add({
            "defect_type":"invalid_reference","entity_type":etype,
            "element_types":[etype],"severity":"low",
            "safe_to_auto_apply":True,
            "defect_description":f"{etype} has OwnerHistory pointing to deleted entity",
            "repair_action":"Reassign OwnerHistory to project default",
            "explanation":"Broken OwnerHistory causes export failures.",
            "geometry_context":_rand_bbox(),
            "property_context":{},
            "relationship_context":{"broken_ref":"IfcOwnerHistory"},
            "before_state":{"entity":etype,"guid":guid,"owner_history":"#DELETED"},
            "after_state":{"entity":etype,"guid":guid,"owner_history":"#1"},
        })


def gen_wrong_level_cases():
    """Elements assigned to wrong storey based on z-coordinate."""
    for etype in ["IfcWall","IfcDoor","IfcWindow","IfcColumn"]:
        for _ in range(3):
            guid = _rand_guid()
            correct_idx = random.randint(0,len(STOREY_NAMES)-2)
            wrong_idx = (correct_idx + random.randint(1,3)) % len(STOREY_NAMES)
            correct = STOREY_NAMES[correct_idx]
            wrong = STOREY_NAMES[wrong_idx]
            z = round(correct_idx * 3.0, 1)
            name = f"{etype.replace('Ifc','')}_{random.randint(1,999):03d}"
            _add({
                "defect_type":"wrong_level_assignment","entity_type":etype,
                "element_types":[etype,"IfcBuildingStorey"],"severity":"medium",
                "safe_to_auto_apply":False,
                "defect_description":f"{etype} '{name}' at z={z}m assigned to '{wrong}' instead of '{correct}'",
                "repair_action":f"Reassign from '{wrong}' to '{correct}'",
                "explanation":"Element placement doesn't match assigned storey elevation.",
                "geometry_context":_rand_bbox(base_z=z),
                "property_context":{"element_name":name,"z_coordinate":z},
                "relationship_context":{"current_storey":wrong,"correct_storey":correct},
                "before_state":{"entity":etype,"guid":guid,"name":name,"container":wrong,"z":z},
                "after_state":{"entity":etype,"guid":guid,"name":name,"container":correct,"z":z},
            })


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate_full_dataset():
    """Generate all case families and save."""
    ALL_CASES.clear()

    gen_missing_property_cases()
    gen_broken_containment_cases()
    gen_disconnected_storey_cases()
    gen_invalid_parent_child_cases()
    gen_naming_cases()
    gen_missing_material_cases()
    gen_clash_cases()
    gen_invalid_reference_cases()
    gen_wrong_level_cases()

    random.shuffle(ALL_CASES)

    # Assign sequential IDs and splits
    n_total = len(ALL_CASES)
    n_train = int(n_total * 0.8)
    n_val = int(n_total * 0.1)

    for i, c in enumerate(ALL_CASES):
        c["case_id"] = f"SC_{i+1:04d}"
        if i < n_train:
            c["split"] = "train"
        elif i < n_train + n_val:
            c["split"] = "val"
        else:
            c["split"] = "test"

    # --- Save JSON (Legacy for pipeline test) ---
    json_path = os.path.join(DATA_DIR, "synthetic_cases.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ALL_CASES, f, indent=2, ensure_ascii=False, default=str)

    # --- Save JSONL Splits (For Training) ---
    for split in ["train", "val", "test", "full"]:
        split_cases = ALL_CASES if split == "full" else [c for c in ALL_CASES if c["split"] == split]
        jsonl_path = os.path.join(DATA_DIR, f"synthetic_cases_{split}.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for c in split_cases:
                f.write(json.dumps(c, ensure_ascii=False, default=str) + "\n")

    # --- Save CSV summary ---
    csv_path = os.path.join(DATA_DIR, "synthetic_cases_full.csv")
    csv_fields = ["case_id", "split", "defect_type", "entity_type", "severity", "safe_to_auto_apply",
                  "defect_description", "repair_action", "explanation"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ALL_CASES)

    # --- Also overwrite the old case_library.json so fallback pipeline works ---
    lib_path = os.path.join(DATA_DIR, "case_library.json")
    with open(lib_path, "w", encoding="utf-8") as f:
        json.dump(ALL_CASES, f, indent=2, ensure_ascii=False, default=str)

    # --- Stats ---
    types = {}
    splits = {"train": 0, "val": 0, "test": 0}
    for c in ALL_CASES:
        types[c["defect_type"]] = types.get(c["defect_type"],0)+1
        splits[c["split"]] += 1

    print(f"Generated {len(ALL_CASES)} synthetic cases")
    print(f"  Splits: Train={splits['train']}, Val={splits['val']}, Test={splits['test']}")
    print(f"  Files saved to: {DATA_DIR}/synthetic_cases_*.jsonl")
    print(f"  Defect types:")
    for k, v in sorted(types.items()):
        print(f"    {k}: {v}")
    return ALL_CASES


if __name__ == "__main__":
    generate_full_dataset()
