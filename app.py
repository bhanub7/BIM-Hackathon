"""
BIMRepair — Streamlit Dashboard
Interactive demo for the BIM lint & repair pipeline and Case Library Explorer.
"""
import os
import sys
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CASE_LIBRARY_PATH, SAMPLE_IFC_PATH, OUTPUT_DIR, DATA_DIR, BASE_DIR
from src.pipeline import run_pipeline

# ── Page Config ──
st.set_page_config(
    page_title="BIMRepair — BIM Lint & Repair",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .metric-card h2 {
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card p {
        color: #a0aec0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-top: 6px;
    }
    
    .status-auto { color: #48bb78; font-weight: 600; }
    .status-flagged { color: #ecc94b; font-weight: 600; }
    .status-rejected { color: #fc8181; font-weight: 600; }
    .status-error { color: #f56565; font-weight: 600; }
    
    .severity-critical { background: #e53e3e; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; }
    .severity-high { background: #dd6b20; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; }
    .severity-medium { background: #d69e2e; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; }
    .severity-low { background: #38a169; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; }
    
    .header-gradient {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


def plot_geometry_context(case):
    """Render a simple 3D bounding box plot for a case."""
    fig = go.Figure()
    geom = case.get("geometry_context", {})
    
    if not geom:
        return None
    
    def add_bbox(bbox, name, color):
        if not bbox or "min" not in bbox or "max" not in bbox: return
        x = [bbox["min"][0], bbox["max"][0], bbox["max"][0], bbox["min"][0], bbox["min"][0],
             bbox["min"][0], bbox["max"][0], bbox["max"][0], bbox["min"][0], bbox["min"][0]]
        y = [bbox["min"][1], bbox["min"][1], bbox["max"][1], bbox["max"][1], bbox["min"][1],
             bbox["min"][1], bbox["min"][1], bbox["max"][1], bbox["max"][1], bbox["min"][1]]
        z = [bbox["min"][2], bbox["min"][2], bbox["min"][2], bbox["min"][2], bbox["min"][2],
             bbox["max"][2], bbox["max"][2], bbox["max"][2], bbox["max"][2], bbox["max"][2]]
        
        fig.add_trace(go.Mesh3d(
            x=[bbox["min"][0], bbox["min"][0], bbox["max"][0], bbox["max"][0], bbox["min"][0], bbox["min"][0], bbox["max"][0], bbox["max"][0]],
            y=[bbox["min"][1], bbox["max"][1], bbox["max"][1], bbox["min"][1], bbox["min"][1], bbox["max"][1], bbox["max"][1], bbox["min"][1]],
            z=[bbox["min"][2], bbox["min"][2], bbox["min"][2], bbox["min"][2], bbox["max"][2], bbox["max"][2], bbox["max"][2], bbox["max"][2]],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color=color, opacity=0.3, name=name
        ))
        # Add wireframe edges
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines', line=dict(color=color, width=3), showlegend=False))

    if "min" in geom and "max" in geom:
        # Single element
        add_bbox(geom, case.get("entity_type", "Element"), "blue")
    elif "element_a" in geom and "element_b" in geom:
        # Clash
        add_bbox(geom["element_a"].get("bbox"), geom["element_a"].get("name", "A"), "red")
        add_bbox(geom["element_b"].get("bbox"), geom["element_b"].get("name", "B"), "orange")

    if not fig.data:
        return None

    fig.update_layout(
        scene=dict(
            xaxis=dict(showbackground=False),
            yaxis=dict(showbackground=False),
            zaxis=dict(showbackground=False),
        ),
        margin=dict(r=0, l=0, b=0, t=0),
        height=300
    )
    return fig


def show_case_library():
    """Display the Case Library Explorer tab."""
    st.markdown("## 📚 Synthetic Case Library & SLM Training Data")
    st.write("Browse the generated synthetic dataset used for retrieval and SLM fine-tuning.")
    
    # ── Training Manifest ──
    manifest_path = os.path.join(BASE_DIR, "artifacts", "train_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        with st.expander("🧠 View Model Training Evidence (train_manifest.json)", expanded=False):
            st.info("This system uses a lightweight local model trained exclusively on the synthetic dataset below.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Model Type", manifest.get("model_type", "Unknown").split(" ")[0])
            c2.metric("Train Samples", manifest.get("training_samples", 0))
            c3.metric("Val Samples", manifest.get("validation_samples", 0))
            c4.metric("Val Accuracy", f"{manifest.get('metrics', {}).get('val_accuracy', 0)*100:.1f}%")
            st.json(manifest)
    
    if not os.path.exists(CASE_LIBRARY_PATH):
        st.warning("Case library not found. Run generators first.")
        if st.button("🔧 Generate Dataset"):
            with st.spinner("Generating..."):
                _generate_data()
            st.rerun()
        return

    with open(CASE_LIBRARY_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)
    
    df = pd.DataFrame(cases)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Synthetic Cases", len(cases))
    with col2:
        st.metric("Defect Families", df["defect_type"].nunique())
    with col3:
        st.metric("Element Types", len(set(sum(df["element_types"].dropna().tolist(), []))))
    with col4:
        st.metric("Auto-Apply Safe", f"{(df['safe_to_auto_apply'].sum() / len(df) * 100):.1f}%")
        
    st.divider()

    # --- Filters ---
    st.markdown("### 🔍 Filter Cases")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    all_defects = ["All"] + sorted(df["defect_type"].unique().tolist())
    all_severities = ["All"] + sorted(df["severity"].unique().tolist())
    all_entities = ["All"] + sorted(df["entity_type"].unique().tolist())
    
    with f_col1:
        sel_defect = st.selectbox("Defect Type", all_defects)
    with f_col2:
        sel_entity = st.selectbox("Entity Type", all_entities)
    with f_col3:
        sel_severity = st.selectbox("Severity", all_severities)
    with f_col4:
        sel_auto = st.selectbox("Auto Apply Safe?", ["All", "Yes", "No"])

    filtered_df = df.copy()
    if sel_defect != "All": filtered_df = filtered_df[filtered_df["defect_type"] == sel_defect]
    if sel_entity != "All": filtered_df = filtered_df[filtered_df["entity_type"] == sel_entity]
    if sel_severity != "All": filtered_df = filtered_df[filtered_df["severity"] == sel_severity]
    if sel_auto != "All":
        filtered_df = filtered_df[filtered_df["safe_to_auto_apply"] == (sel_auto == "Yes")]

    st.write(f"Showing **{len(filtered_df)}** cases matching criteria.")
    
    # Show dataframe
    display_df = filtered_df[["case_id", "defect_type", "entity_type", "severity", "defect_description", "safe_to_auto_apply"]]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 📖 Case Details Explorer")
    if not filtered_df.empty:
        selected_case_id = st.selectbox("Select a Case to view details", filtered_df["case_id"].tolist())
        case = filtered_df[filtered_df["case_id"] == selected_case_id].iloc[0].to_dict()
        
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown(f"**ID:** `{case['case_id']}`")
            st.markdown(f"**Defect:** `{case['defect_type']}` | **Entity:** `{case['entity_type']}` | **Severity:** `{case['severity'].upper()}`")
            st.markdown(f"**Description:** {case['defect_description']}")
            st.markdown(f"**Repair Action:** {case['repair_action']}")
            st.markdown(f"**Explanation:** {case['explanation']}")
            st.markdown(f"**Auto-Apply:** {'✅ Yes' if case['safe_to_auto_apply'] else '⚠️ No'}")
            
            st.markdown("**Property / Relationship Context:**")
            st.json({
                "property_context": case.get("property_context", {}),
                "relationship_context": case.get("relationship_context", {})
            })
            
        with c_right:
            st.markdown("**Geometry Context:**")
            fig = plot_geometry_context(case)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No 3D geometry available for this case type.")
            
            ba1, ba2 = st.columns(2)
            with ba1:
                st.markdown("**Before State:**")
                st.json(case.get("before_state", {}))
            with ba2:
                st.markdown("**After State:**")
                st.json(case.get("after_state", {}))
    
    # --- Training Export ---
    st.divider()
    st.markdown("### 🧠 SLM Training Data")
    st.info("The synthetic case library is exported to JSONL format for fine-tuning Small Language Models (e.g., Llama-3, Phi-3).")
    jsonl_path = os.path.join(DATA_DIR, "synthetic_cases.jsonl")
    if os.path.exists(jsonl_path):
        with open(jsonl_path, "rb") as f:
            st.download_button("⬇️ Download JSONL for Fine-tuning", f.read(), file_name="synthetic_cases.jsonl", mime="application/jsonlines")


def main():
    # ── Header ──
    st.markdown("<h1 class='header-gradient'>🏗️ BIMRepair</h1>", unsafe_allow_html=True)
    st.markdown("**Automated BIM Lint & Repair Assistant** — Detect, retrieve, repair, and validate IFC model defects")
    
    tab1, tab2 = st.tabs(["🚀 Repair Pipeline", "📚 Case Library & SLM Data"])
    
    with tab2:
        show_case_library()

    with tab1:
        # ── Sidebar ──
        with st.sidebar:
            st.markdown("### ⚙️ Configuration")
            
            # File selection
            source = st.radio("IFC Source", ["Load Sample Model", "Upload IFC File"], index=0)
            
            ifc_path = None
            if source == "Load Sample Model":
                if os.path.exists(SAMPLE_IFC_PATH):
                    ifc_path = SAMPLE_IFC_PATH
                    st.success(f"✅ Sample model ready")
                else:
                    st.warning("⚠️ Sample model not found. Run generators first.")
                    if st.button("🔧 Generate Sample Data"):
                        with st.spinner("Generating..."):
                            _generate_data()
                        st.rerun()
            else:
                uploaded = st.file_uploader("Upload IFC file", type=["ifc"])
                if uploaded:
                    tmp_path = os.path.join(OUTPUT_DIR, "uploaded_model.ifc")
                    os.makedirs(OUTPUT_DIR, exist_ok=True)
                    with open(tmp_path, "wb") as f:
                        f.write(uploaded.getvalue())
                    ifc_path = tmp_path
                    st.success("✅ File uploaded")
            
            st.divider()
            
            # Case library status
            if os.path.exists(CASE_LIBRARY_PATH):
                with open(CASE_LIBRARY_PATH, "r") as f:
                    cases = json.load(f)
                st.info(f"📚 Case Library: **{len(cases)}** cases loaded")
            else:
                st.warning("📚 Case library not found")
                if st.button("📝 Generate Case Library"):
                    with st.spinner("Generating..."):
                        _generate_data()
                    st.rerun()
            
            st.divider()
            st.markdown("### 🎯 Thresholds")
            auto_conf = st.slider("Auto-apply confidence", 0.0, 1.0, 0.70, 0.05)
            flag_conf = st.slider("Flag confidence", 0.0, 1.0, 0.40, 0.05)
            
            st.divider()
            run_btn = st.button("🚀 Run BIMRepair Pipeline", type="primary",
                                disabled=(ifc_path is None), use_container_width=True)
        
        # ── Main Content ──
        if run_btn and ifc_path:
            with st.spinner("🔍 Running BIMRepair pipeline..."):
                try:
                    results = run_pipeline(ifc_path=ifc_path,
                                            case_library_path=CASE_LIBRARY_PATH)
                    st.session_state["results"] = results
                    st.session_state["ifc_path"] = ifc_path
                except Exception as e:
                    st.error(f"❌ Pipeline error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    return
        
        if "results" not in st.session_state:
            # Show landing page
            _show_landing()
            return
        
        results = st.session_state["results"]
        summary = results["summary"]
        items = results["results"]
        
        # ── Summary Cards ──
        st.markdown("## 📊 Pipeline Summary")
        c1, c2, c3, c4, c5 = st.columns(5)
        
        with c1:
            st.markdown(f"""<div class="metric-card">
                <h2>{summary['total_defects']}</h2>
                <p>Total Defects</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <h2>{summary['auto_applied']}</h2>
                <p>Auto-Fixed</p>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <h2>{summary['flagged_for_review']}</h2>
                <p>Flagged</p>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <h2>{summary['rejected']}</h2>
                <p>Rejected</p>
            </div>""", unsafe_allow_html=True)
        with c5:
            st.markdown(f"""<div class="metric-card">
                <h2>{summary['elapsed_seconds']}s</h2>
                <p>Time</p>
            </div>""", unsafe_allow_html=True)
        
        st.divider()
        
        # ── Charts ──
        st.markdown("## 📈 Analysis")
        chart1, chart2 = st.columns(2)
        
        with chart1:
            # Defect types bar chart
            type_counts = {}
            for item in items:
                dt = item["defect"]["defect_type"]
                type_counts[dt] = type_counts.get(dt, 0) + 1
            
            fig1 = px.bar(
                x=list(type_counts.keys()),
                y=list(type_counts.values()),
                labels={"x": "Defect Type", "y": "Count"},
                title="Defects by Type",
                color=list(type_counts.values()),
                color_continuous_scale="Viridis",
            )
            fig1.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with chart2:
            # Status pie chart
            status_counts = {}
            for item in items:
                s = item["status"]
                status_counts[s] = status_counts.get(s, 0) + 1
            
            colors = {
                "auto_applied": "#48bb78",
                "flagged_for_review": "#ecc94b",
                "rejected": "#fc8181",
                "error": "#f56565",
                "low_confidence": "#a0aec0",
                "flagged": "#ecc94b",
                "skipped": "#718096",
            }
            
            fig2 = go.Figure(data=[go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                marker_colors=[colors.get(k, "#667eea") for k in status_counts.keys()],
                hole=0.45,
            )])
            fig2.update_layout(
                title="Repair Status Distribution",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        
        # ── Severity chart ──
        sev_counts = {}
        for item in items:
            s = item["defect"]["severity"]
            sev_counts[s] = sev_counts.get(s, 0) + 1
        
        sev_colors = {"critical": "#e53e3e", "high": "#dd6b20", "medium": "#d69e2e", "low": "#38a169"}
        fig3 = px.bar(
            x=list(sev_counts.keys()),
            y=list(sev_counts.values()),
            title="Defects by Severity",
            labels={"x": "Severity", "y": "Count"},
            color=list(sev_counts.keys()),
            color_discrete_map=sev_colors,
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.divider()
        
        # ── Defect Details Table ──
        st.markdown("## 🔍 Runtime Defect Details")
        
        # Filter
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            all_types = sorted(set(item["defect"]["defect_type"] for item in items))
            selected_types = st.multiselect("Filter by defect type", all_types, default=all_types)
        with filter_col2:
            all_statuses = sorted(set(item["status"] for item in items))
            selected_statuses = st.multiselect("Filter by status", all_statuses, default=all_statuses)
        
        filtered = [item for item in items
                    if item["defect"]["defect_type"] in selected_types
                    and item["status"] in selected_statuses]
        
        for i, item in enumerate(filtered):
            defect = item["defect"]
            proposal = item["proposal"]
            validation = item["validation"]
            repair = item["repair_result"]
            status = item["status"]
            
            # Status badge
            status_class = {
                "auto_applied": "status-auto",
                "flagged_for_review": "status-flagged",
                "flagged": "status-flagged",
                "rejected": "status-rejected",
                "error": "status-error",
            }.get(status, "status-flagged")
            
            sev_class = f"severity-{defect['severity']}"
            
            header = (f"**{defect['defect_id']}** | {defect['entity_type']} "
                      f"'{defect.get('entity_name') or 'unnamed'}' | "
                      f"`{defect['defect_type']}` | {status.upper()}")
            
            with st.expander(header, expanded=(i < 3)):
                col_a, col_b = st.columns([2, 1])
                
                with col_a:
                    st.markdown(f"**Defect:** {defect['description']}")
                    st.markdown(f"**Severity:** "
                                f"<span class='{sev_class}'>{defect['severity'].upper()}</span>",
                                unsafe_allow_html=True)
                    st.markdown(f"**Entity GUID:** `{defect['entity_guid']}`")
                    
                    if item["similar_cases"]:
                        st.markdown("---")
                        st.markdown("**📚 Retrieved Synthetic Case Context:**")
                        best_case_id, best_desc, sim = item["similar_cases"][0]
                        st.markdown(f"- **Top Match (`{best_case_id}`)** (similarity: **{sim:.1%}**) — {best_desc}")
                        
                        # Load full case to get geometry
                        case_lib_path = os.path.join(BASE_DIR, "artifacts", "model", "train_cases.json")
                        best_case = None
                        if os.path.exists(case_lib_path):
                            with open(case_lib_path, "r") as f:
                                all_cases = json.load(f)
                                best_case = next((c for c in all_cases if c["case_id"] == best_case_id), None)
                        
                        if best_case and best_case.get("geometry_context"):
                            fig = plot_geometry_context(best_case)
                            if fig:
                                st.markdown("*Retrieved Geometry Context:*")
                                st.plotly_chart(fig, use_container_width=True, key=f"geom_{defect['defect_id']}")
                
                with col_b:
                    st.markdown(f"**Status:** <span class='{status_class}'>"
                                f"{status.replace('_', ' ').upper()}</span>",
                                unsafe_allow_html=True)
                    st.markdown(f"**Confidence:** {proposal['confidence']:.1%}")
                    st.markdown(f"**Matched Case:** `{proposal.get('matched_case_id', 'N/A')}`")
                    st.markdown(f"**Safe to Auto-Apply:** "
                                f"{'✅ Yes' if proposal['safe_to_auto_apply'] else '⚠️ No'}")
                
                    # Repair details
                    st.markdown("---")
                    st.markdown(f"**🔧 Proposed Repair:** {proposal['repair_action']}")
                    st.markdown(f"**💡 AI Explanation:** {proposal['explanation']}")
                    
                    # Validation
                    if validation["checks"] or validation["warnings"] or validation["errors"]:
                        st.markdown("**🛡️ Validation Layer:**")
                        for check in validation["checks"]:
                            st.markdown(f"  ✅ {check}")
                        for warn in validation["warnings"]:
                            st.markdown(f"  ⚠️ {warn}")
                        for err in validation["errors"]:
                            st.markdown(f"  ❌ {err}")
                
                # Before/After
                if repair.get("before") and repair.get("after"):
                    st.markdown("---")
                    ba1, ba2 = st.columns(2)
                    with ba1:
                        st.markdown("**IFC Before State:**")
                        st.code(repair["before"], language="text")
                    with ba2:
                        st.markdown("**IFC After State:**")
                        st.code(repair["after"], language="text")
        
        st.divider()
        
        # ── Download ──
        st.markdown("## 📥 Download Artifacts")
        col_down1, col_down2 = st.columns(2)
        
        output_file = summary.get("output_file")
        if output_file and os.path.exists(output_file):
            with col_down1:
                with open(output_file, "rb") as f:
                    st.download_button(
                        "⬇️ Download Repaired IFC",
                        data=f.read(),
                        file_name=os.path.basename(output_file),
                        mime="application/octet-stream",
                        type="primary",
                        use_container_width=True
                    )
                st.success(f"Repaired model saved to: `{output_file}`")
        else:
            with col_down1:
                st.info("No repaired file available yet.")
                
        with col_down2:
            report_json = json.dumps(results, indent=2, default=str)
            st.download_button(
                "📄 Download JSON Report",
                data=report_json,
                file_name=f"bimrepair_report_{summary.get('elapsed_seconds', 0)}.json",
                mime="application/json",
                use_container_width=True
            )


def _show_landing():
    """Show the landing page when no results are loaded."""
    st.markdown("## 🚀 Get Started")
    st.markdown("""
    1. **Load** the sample IFC model or upload your own
    2. Click **Run BIMRepair Pipeline** in the sidebar
    3. View detected defects, retrieved cases, and proposed repairs
    4. Download the repaired IFC model
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🔍 Detect
        Rule-based engine finds missing properties, broken relationships,
        disconnected storeys, naming issues, and more.
        """)
    with col2:
        st.markdown("""
        ### 📚 Retrieve
        Case-based retrieval matches defects to a library of 300+ known
        defect→repair pairs using TF-IDF similarity.
        """)
    with col3:
        st.markdown("""
        ### 🔧 Repair
        Validated repairs are auto-applied when safe. Uncertain fixes
        are flagged for manual review.
        """)


def _generate_data():
    """Generate case library and sample IFC."""
    # Ensure dataset is generated if not existing
    try:
        from generators.generate_synthetic_dataset import generate_full_dataset
        generate_full_dataset()
    except Exception as e:
        print(f"Failed to generate synthetic dataset: {e}")
        # fallback to basic
        from generators.generate_cases import generate_case_library
        generate_case_library()
        
    from generators.generate_sample_ifc import generate_sample_ifc
    generate_sample_ifc()


if __name__ == "__main__":
    main()
