"""
BIMRepair — End-to-End Pipeline Orchestrator
Ties together all components: parse → detect → retrieve → propose → validate → apply.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    CASE_LIBRARY_PATH, SAMPLE_IFC_PATH, OUTPUT_DIR,
    AUTO_APPLY_CONFIDENCE, FLAG_CONFIDENCE, TOP_K_CASES, MIN_SIMILARITY,
)
from src.ifc_parser import load_model
from src.defect_detector import detect_all_defects
from src.case_library import CaseLibrary
from src.repair_proposer import propose_repair
from src.validator import validate_proposal
from src.repair_applier import apply_repair

logger = logging.getLogger(__name__)


def run_pipeline(ifc_path=None, case_library_path=None, output_path=None):
    """
    Run the full BIMRepair pipeline.
    
    Args:
        ifc_path: Path to input IFC file
        case_library_path: Path to case library JSON
        output_path: Path to save repaired IFC
    
    Returns:
        dict with pipeline results
    """
    start_time = time.time()
    
    # Defaults
    ifc_path = ifc_path or SAMPLE_IFC_PATH
    case_library_path = case_library_path or CASE_LIBRARY_PATH
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"repaired_{ts}.ifc")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("BIMRepair Pipeline Starting")
    logger.info(f"  Input: {ifc_path}")
    logger.info(f"  Cases: {case_library_path}")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 60)
    
    # ── Step 1: Load Model ──
    logger.info("Step 1: Loading IFC model...")
    model = load_model(ifc_path)
    
    # ── Step 2: Detect Defects ──
    logger.info("Step 2: Detecting defects...")
    defects = detect_all_defects(model)
    logger.info(f"  Found {len(defects)} defects")
    
    # ── Step 3: Load Case Library ──
    logger.info("Step 3: Loading case library...")
    case_lib = CaseLibrary(case_library_path)
    
    # ── Step 4: Process Each Defect ──
    logger.info("Step 4: Processing defects...")
    results = []
    
    counters = {"auto_applied": 0, "flagged": 0, "rejected": 0, "error": 0}
    
    for defect in defects:
        # Retrieve similar cases
        similar_cases = case_lib.retrieve(defect, top_k=TOP_K_CASES,
                                           min_similarity=MIN_SIMILARITY)
        
        # Propose repair
        proposal = propose_repair(defect, similar_cases,
                                   auto_threshold=AUTO_APPLY_CONFIDENCE,
                                   case_library=case_lib)
        
        # Validate
        validation = validate_proposal(model, proposal)
        
        # Decide action
        if validation.passed and proposal.safe_to_auto_apply:
            repair_result = apply_repair(model, proposal)
            status = "auto_applied" if repair_result["status"] == "applied" else repair_result["status"]
        elif validation.passed and proposal.confidence >= FLAG_CONFIDENCE:
            status = "flagged_for_review"
            repair_result = {"status": "flagged", "message": "Needs manual review"}
        elif not validation.passed:
            status = "rejected"
            repair_result = {"status": "rejected", "message": "; ".join(validation.errors)}
        else:
            status = "low_confidence"
            repair_result = {"status": "low_confidence",
                           "message": f"Confidence {proposal.confidence:.2f} below threshold"}
        
        counters[status if status in counters else "flagged"] += 1
        
        results.append({
            "defect": defect.to_dict(),
            "similar_cases": [(c["case_id"], c["defect_description"], round(s, 3))
                             for c, s in similar_cases],
            "proposal": proposal.to_dict(),
            "validation": validation.to_dict(),
            "repair_result": repair_result,
            "status": status,
        })
    
    # ── Step 5: Save Repaired Model ──
    logger.info("Step 5: Saving repaired model...")
    model.write(output_path)
    
    # ── Step 6: Summary ──
    elapsed = time.time() - start_time
    summary = {
        "input_file": ifc_path,
        "output_file": output_path,
        "total_defects": len(defects),
        "auto_applied": counters["auto_applied"],
        "flagged_for_review": counters["flagged"],
        "rejected": counters["rejected"],
        "errors": counters["error"],
        "elapsed_seconds": round(elapsed, 2),
    }
    
    logger.info("=" * 60)
    logger.info("Pipeline Complete!")
    logger.info(f"  Total defects: {summary['total_defects']}")
    logger.info(f"  Auto-applied:  {summary['auto_applied']}")
    logger.info(f"  Flagged:       {summary['flagged_for_review']}")
    logger.info(f"  Rejected:      {summary['rejected']}")
    logger.info(f"  Time:          {summary['elapsed_seconds']}s")
    logger.info("=" * 60)
    
    return {
        "summary": summary,
        "results": results,
    }


if __name__ == "__main__":
    import config  # trigger logging setup
    output = run_pipeline()
    
    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE RESULTS")
    print("=" * 60)
    s = output["summary"]
    print(f"Total defects found: {s['total_defects']}")
    print(f"Auto-applied fixes:  {s['auto_applied']}")
    print(f"Flagged for review:  {s['flagged_for_review']}")
    print(f"Rejected:            {s['rejected']}")
    print(f"Errors:              {s['errors']}")
    print(f"Time elapsed:        {s['elapsed_seconds']}s")
    print(f"Repaired file:       {s['output_file']}")
