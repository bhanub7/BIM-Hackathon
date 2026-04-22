# BIMRepair — Automated BIM Lint & Repair Assistant

An automated case-based BIM quality checking and repair system for IFC files.

## 🏗️ What It Does

BIMRepair parses IFC files, detects common defects, retrieves similar past repair cases, proposes fixes, validates them, and auto-applies safe repairs.

### Target Defect Types
- **Missing Properties** — Required properties absent from standard property sets
- **Broken Spatial Containment** — Elements not contained in any building storey
- **Disconnected Storeys** — Storeys not aggregated to buildings
- **Invalid Parent-Child** — Spaces not properly parented to storeys
- **Naming Inconsistency** — Empty, missing, or duplicate element names
- **Missing Materials** — Elements without material associations

## 🚀 Quick Start

### Option 1: One-Click (Windows)
```
run.bat
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Generate synthetic dataset and sample data (Generates 300+ diverse case library)
python generators/generate_synthetic_dataset.py
python generators/generate_sample_ifc.py

# Run the pipeline (CLI)
python -m src.pipeline

# Launch the dashboard
streamlit run app.py
```

## 📁 Project Structure

```
BIM Hack/
├── app.py                    # Streamlit dashboard
├── config.py                 # Central configuration
├── requirements.txt          # Python dependencies
├── run.bat                   # One-click launcher
├── data/
│   ├── case_library.json       # Current active case library
│   ├── synthetic_cases.jsonl   # Dataset formatted for SLM fine-tuning
│   ├── synthetic_cases.csv     # Tabular summary of cases
│   └── sample_model.ifc        # Sample IFC with seeded defects
├── src/
│   ├── ifc_parser.py         # IFC loading & entity extraction
│   ├── defect_detector.py    # Rule-based defect detection
│   ├── case_library.py       # TF-IDF case retrieval
│   ├── repair_proposer.py    # Case-adapted repair proposals
│   ├── validator.py          # Symbolic validation rules
│   ├── repair_applier.py     # Safe repair application
│   └── pipeline.py           # End-to-end orchestrator
├── generators/
│   ├── generate_cases.py               # Basic case generator (fallback)
│   ├── generate_synthetic_dataset.py   # Parametric synthetic dataset generator (500+ cases)
│   └── generate_sample_ifc.py          # Sample IFC generator
└── output/                   # Repaired IFC files
```

## 🧠 Synthetic Dataset & SLM Training

BIMRepair is not just a hard-coded script; it is a **Data-Driven Architecture**. 

The repository includes a parametric data generator (`generators/generate_synthetic_dataset.py`) that produces **430+ diverse defect-repair cases** across 10 families, including both property/relationship defects (missing properties, broken containment) and **geometry clash defects** (wall-column clashes, slab-column soft clashes, overlapping spatial elements).

This synthetic dataset provides:
1. **Retrieval Index**: Immediately powers the TF-IDF case retrieval engine.
2. **Training Data**: Automatically exported to `synthetic_cases.jsonl` for fine-tuning models like **Llama-3 8B** or **Phi-3** to intrinsically learn BIM topology, structural relationships, and appropriate repair actions.

## 🏛️ Architecture

```
IFC File → Parser → Defect Detector → Case Retriever (TF-IDF)
                                              ↓
                           Case Library ← Similarity Match
                                              ↓
                                      Repair Proposer
                                              ↓
                                    Symbolic Validator
                                              ↓
                                      Repair Applier → Repaired IFC
```

## 🔧 How It Works

1. **Parse**: Load IFC file with ifcopenshell; extract entities, properties, relationships
2. **Detect**: Rule-based engine checks 6 defect categories against IFC schema expectations
3. **Retrieve**: TF-IDF + cosine similarity finds similar defect→repair cases from library
4. **Propose**: Adapts best-matching case repair to current defect context
5. **Validate**: Symbolic rules verify the repair won't break IFC validity
6. **Apply**: Auto-applies high-confidence safe fixes; flags uncertain ones for review

## 📊 Dashboard Features

- Summary cards (total defects, auto-fixed, flagged, rejected)
- Interactive charts (defect types, severity distribution, repair status)
- Expandable defect details with before/after comparison
- Similar case retrieval display with similarity scores
- Validation status and confidence metrics
- Download repaired IFC file

## ⚠️ Limitations

- Geometry clash detection uses bounding-box overlap only (approximate)
- Material assignment requires manual review (not auto-applied)
- Case library is synthetic (36 cases) — expandable with real project data
- Single-file processing only
- No 3D visualization in dashboard
