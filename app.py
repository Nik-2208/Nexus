"""
NEXUS: AI Failure Intelligence Engine
Streamlit Application Shell
"""

import streamlit as st
import os
from nexus.config import DEFAULT_MODEL_FILENAME, BASE_DIR
from nexus.engine.workflow import NexusWorkflowEngine
from nexus.providers.demo import DemoProvider
from nexus.providers.local_gemma import LocalGemmaProvider
from nexus.providers.gemini import GeminiProvider
from nexus.ui.components import render_graph_figure
from nexus.security.redaction import sanitize_for_plain_display

# Set page config
st.set_page_config(
    page_title="NEXUS — AI Failure Intelligence Engine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling: Warm ivory background, restrained borders, editorial typography
st.markdown(
    """
    <style>
    .stApp {
        background-color: #faf9f6;
        color: #1c1917;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .nexus-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #e7e5e4;
        color: #44403c;
    }
    .nexus-badge-secure {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .nexus-badge-remote {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .nexus-card {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "workflow_engine" not in st.session_state:
    st.session_state.workflow_engine = NexusWorkflowEngine()
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "consent_granted" not in st.session_state:
    st.session_state.consent_granted = False

# Sidebar Navigation and Connection Status
with st.sidebar:
    st.title("🔬 NEXUS")
    st.caption("AI Failure Intelligence Engine")
    st.markdown("---")

    nav_selection = st.radio(
        "Navigation",
        ["Overview", "Failure Analysis", "Decision Graph", "Experiments", "Run History", "Settings"],
        index=0,
    )

    st.markdown("---")
    st.markdown("### Runtime & Locality")

    # Inspect Model Candidate
    model_candidate_path = BASE_DIR / DEFAULT_MODEL_FILENAME
    model_exists = model_candidate_path.exists()

    if model_exists:
        st.markdown(f"**Model Candidate:** Found (`{DEFAULT_MODEL_FILENAME}`)")
        st.caption(f"Size: {round(os.path.getsize(model_candidate_path) / (1024**3), 2)} GB")
    else:
        st.markdown(f"**Model Candidate:** Not found in searched directory")

    # Local Server Health
    import shutil
    runtime_installed = shutil.which("llama-server") is not None

    if runtime_installed:
        st.markdown("**Inference Runtime:** Found (`llama-server`)")
    else:
        st.markdown("**Inference Runtime:** `Runtime missing` (llama-server not on PATH)")

    local_provider = LocalGemmaProvider()
    local_status = local_provider.check_health()

    if local_status.is_connected:
        st.success("Local Gemma Server: Connected (127.0.0.1:8080)")
    elif runtime_installed:
        st.info("Local Gemma Server: Disconnected (Run `start_local_model.bat`)")
    else:
        st.warning("Local Gemma Server: Offline (Runtime missing)")

    st.markdown("---")
    st.markdown(
        "<div class='nexus-badge nexus-badge-secure'>🛡️ LOCAL-FIRST: No silent egress</div>",
        unsafe_allow_html=True,
    )

workflow = st.session_state.workflow_engine

# --- TAB 1: OVERVIEW ---
if nav_selection == "Overview":
    st.header("See how AI systems fail.")
    st.write(
        "NEXUS traces the structural origin of AI failure modes across four integrated lenses: "
        "**BeliefBlast Radius**, **ContextFlip**, **GoalRot**, and **AssumptionDebt**."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            ### Core Diagnostic Pillars
            - **BeliefBlast Radius:** Map the blast radius of contradicted or revised claims onto downstream decisions and configuration files.
            - **ContextFlip:** Empirically discover whether subtle context shifts invert plans and abandon constraints.
            - **GoalRot:** Deterministically detect when proposed actions violate explicit user objectives.
            - **AssumptionDebt:** Surface unverified assumptions and test them with safe, allowlisted empirical checks.
            """
        )

    with col2:
        st.markdown("### Quick Actions")
        if st.button("🚀 Run Failure Analysis", type="primary", use_container_width=True):
            with st.spinner("Executing failure analysis pipeline..."):
                report = workflow.run_analysis(provider=DemoProvider())
                st.session_state.current_report = report
            st.success("Analysis complete! Open 'Failure Analysis' or 'Decision Graph'.")

    st.markdown("---")
    st.markdown("### Four Integrated Modules")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**BeliefBlast Radius**")
        st.caption("Blast radius impact tracing")
    with c2:
        st.markdown("**ContextFlip**")
        st.caption("Context sensitivity testing")
    with c3:
        st.markdown("**GoalRot**")
        st.caption("Constraint violation detection")
    with c4:
        st.markdown("**AssumptionDebt**")
        st.caption("Unverified assumption audit")

# --- TAB 2: FAILURE ANALYSIS ---
elif nav_selection == "Failure Analysis":
    st.header("Failure Analysis Studio")
    st.caption("Evaluate plan divergence, invariant violations, and downstream impact.")

    colA, colB = st.columns([3, 1])
    with colA:
        scenario_choice = st.selectbox(
            "Scenario Selection",
            ["Offline Coding Agent — Hidden Cloud Dependency (Signature Scenario)"],
        )
    with colB:
        provider_choice = st.selectbox("Provider Mode", ["Demo Mode (Deterministic Fixture)", "Local Gemma (Loopback)", "Gemini API (Remote)"])

    # Consent confirmation if Remote Gemini selected
    provider = DemoProvider()
    if provider_choice == "Local Gemma (Loopback)":
        provider = LocalGemmaProvider()
    elif provider_choice == "Gemini API (Remote)":
        st.warning("⚠️ Remote Provider Selected: Analysis data will leave your device and be sent to Google Gemini API.")
        consent = st.checkbox("I explicitly consent to transmit analysis prompts to Google Gemini API.")
        st.session_state.consent_granted = consent
        provider = GeminiProvider(consent_granted=consent)

    if st.button("Run Failure Analysis", type="primary"):
        with st.spinner("Analyzing graph, constraints, and dependencies..."):
            try:
                report = workflow.run_analysis(provider=provider)
                st.session_state.current_report = report
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Analysis Failed: {sanitize_for_plain_display(str(e))}")

    report = st.session_state.current_report
    if report:
        st.markdown("---")
        st.subheader(f"Findings: {report.scenario_title}")
        st.caption(f"Provider: {report.provider_name} | Timestamp: {report.timestamp}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Critical Violations", report.metrics.get("critical_violations", 0))
        m2.metric("High Risks", report.metrics.get("high_severity_risks", 0))
        m3.metric("Decision Flips", report.metrics.get("observed_decision_flips", 0))
        m4.metric("Assumptions Tested", len(report.assumption_tests))

        st.markdown("### Findings Breakdown")
        for finding in report.findings:
            sev_badge = "🔴" if finding.severity.value == "critical" else "🟠" if finding.severity.value == "high" else "🔵"
            with st.expander(f"{sev_badge} [{finding.module.value}] {finding.title}"):
                st.markdown(f"**Severity:** `{finding.severity.value.upper()}` — *{sanitize_for_plain_display(finding.severity_rationale)}*")
                st.markdown(f"**Provenance:** `{finding.provenance.value}` | **Deterministic Check:** `{finding.deterministic_check_executed}`")
                st.write(sanitize_for_plain_display(finding.description))
                if finding.remediation_suggestion:
                    st.info(f"**Remediation:** {sanitize_for_plain_display(finding.remediation_suggestion)}")

# --- TAB 3: DECISION GRAPH ---
elif nav_selection == "Decision Graph":
    st.header("Decision & Assumption Graph")
    st.caption("Interactive causal and dependency graph mapping requirements, assumptions, decisions, and artifacts.")

    report = st.session_state.current_report
    if not report:
        st.info("No active report. Running default scenario analysis...")
        report = workflow.run_analysis(provider=DemoProvider())
        st.session_state.current_report = report

    fig = render_graph_figure(report.nodes, report.edges)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Node Legend & Provenance")
    st.markdown(
        """
        - 🔵 **Goal / Constraint:** Explicit user specifications and invariants.
        - 🟠 **Assumption:** Unverified claims relied upon by plan decisions.
        - 🟣 **Evidence:** Real-world documentation, release notes, or inputs.
        - 🔴 **Action:** Concrete operations (e.g. adding dependencies or network endpoints).
        - 🟢 **Artifact:** Configuration files, code, or documentation generated by the plan.
        """
    )

# --- TAB 4: EXPERIMENTS ---
elif nav_selection == "Experiments":
    st.header("Controlled Experiments & Empirical Verification")

    report = st.session_state.current_report
    if not report:
        report = workflow.run_analysis(provider=DemoProvider())
        st.session_state.current_report = report

    st.subheader("1. ContextFlip Controlled Perturbations")
    for mut in report.context_mutations:
        with st.container():
            st.markdown(f"**Mutation ID:** `{mut.mutation_id}` — {mut.description}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Baseline Decision:**\n> {sanitize_for_plain_display(mut.baseline_decision)}")
            with col2:
                st.markdown(f"**Mutated Decision:**\n> {sanitize_for_plain_display(mut.mutated_decision)}")
            flip_text = "YES (Plan Inverted)" if mut.decision_flipped else "NO (Decision Stable)"
            st.caption(f"Decision Flipped: {flip_text} | Execution Time: {mut.execution_time_ms} ms | Provenance: {mut.provenance.value}")

    st.markdown("---")
    st.subheader("2. AssumptionDebt Empirical Checks")
    for test in report.assumption_tests:
        with st.container():
            status_icon = "❌" if test.status.value == "failed" else "✅" if test.status.value == "passed" else "⚠️"
            st.markdown(f"{status_icon} **{test.name}** (`{test.assumption_id}`)")
            st.write(f"**Status:** `{test.status.value}` — {sanitize_for_plain_display(test.details)}")
            st.json(test.outputs)

# --- TAB 5: RUN HISTORY ---
elif nav_selection == "Run History":
    st.header("Local Run History")
    st.caption("Auditable local SQLite experiment storage. Parameterized queries; zero unencrypted external logging.")

    runs = workflow.repository.list_recent_runs()
    if runs:
        for r in runs:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
            c1.write(f"**{r['scenario_title']}**")
            c2.write(f"Provider: `{r['provider_name']}`")
            c3.write(f"Findings: `{r['findings_count']}`")
            c4.write(f"{r['timestamp']}")

        st.markdown("---")
        if st.button("🗑️ Delete Local History", type="secondary"):
            if workflow.repository.clear_all_history():
                st.success("Local history successfully cleared.")
                st.rerun()
    else:
        st.info("No prior runs recorded in local storage.")

# --- TAB 6: SETTINGS ---
elif nav_selection == "Settings":
    st.header("Security & Runtime Settings")
    st.markdown(
        """
        ### Non-Negotiable Invariants
        - **Local-first default:** No data leaves the machine unless explicit per-run opt-in is confirmed.
        - **Loopback binding:** Enforces connection to `127.0.0.1` and `localhost` only.
        - **No arbitrary code execution:** Test functions are strictly allowlisted. No `eval()`, `exec()`, or dynamic subprocess generation.
        - **Input/Output bounds:** Text length, graph size, and mutation depth are strictly capped.
        """
    )
    st.markdown("---")
    st.markdown("### Discovered Local Model Assets")
    st.code(f"Workspace Path: {BASE_DIR}\nModel Candidate: {DEFAULT_MODEL_FILENAME} ({'Present' if model_exists else 'Absent'})")
