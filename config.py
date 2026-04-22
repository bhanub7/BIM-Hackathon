"""
BIMRepair — Central Configuration
"""
import os

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

CASE_LIBRARY_PATH = os.path.join(DATA_DIR, "case_library.json")
SAMPLE_IFC_PATH = os.path.join(DATA_DIR, "sample_model.ifc")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Repair Thresholds ─────────────────────────────────────────────────
AUTO_APPLY_CONFIDENCE = 0.70   # Auto-apply if confidence >= this
FLAG_CONFIDENCE = 0.40         # Flag for review if confidence >= this (but < auto)
REJECT_BELOW = 0.40            # Reject proposal if confidence < this

# ── Retrieval Settings ─────────────────────────────────────────────────
TOP_K_CASES = 3                # Number of similar cases to retrieve
MIN_SIMILARITY = 0.10          # Minimum TF-IDF cosine similarity to consider

# ── Defect Severity Levels ─────────────────────────────────────────────
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

# ── Expected Property Sets per Entity Type ─────────────────────────────
# Maps IFC entity type → list of (PsetName, PropertyName, DefaultValue, Severity)
EXPECTED_PROPERTIES = {
    "IfcWall": [
        ("Pset_WallCommon", "LoadBearing", False, SEVERITY_HIGH),
        ("Pset_WallCommon", "IsExternal", False, SEVERITY_MEDIUM),
        ("Pset_WallCommon", "FireRating", "", SEVERITY_MEDIUM),
        ("Pset_WallCommon", "Reference", "", SEVERITY_LOW),
    ],
    "IfcSlab": [
        ("Pset_SlabCommon", "LoadBearing", True, SEVERITY_HIGH),
        ("Pset_SlabCommon", "IsExternal", False, SEVERITY_MEDIUM),
        ("Pset_SlabCommon", "FireRating", "", SEVERITY_MEDIUM),
    ],
    "IfcDoor": [
        ("Pset_DoorCommon", "FireRating", "", SEVERITY_MEDIUM),
        ("Pset_DoorCommon", "IsExternal", False, SEVERITY_MEDIUM),
        ("Pset_DoorCommon", "Reference", "", SEVERITY_LOW),
    ],
    "IfcWindow": [
        ("Pset_WindowCommon", "FireRating", "", SEVERITY_MEDIUM),
        ("Pset_WindowCommon", "IsExternal", True, SEVERITY_MEDIUM),
    ],
    "IfcColumn": [
        ("Pset_ColumnCommon", "LoadBearing", True, SEVERITY_HIGH),
        ("Pset_ColumnCommon", "IsExternal", False, SEVERITY_MEDIUM),
    ],
    "IfcBeam": [
        ("Pset_BeamCommon", "LoadBearing", True, SEVERITY_HIGH),
        ("Pset_BeamCommon", "IsExternal", False, SEVERITY_MEDIUM),
    ],
}

# ── Logging ────────────────────────────────────────────────────────────
import logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
