"""Unified workflow coordinator for NEXUS failure analysis."""

from datetime import datetime
import time
from typing import Optional, List, Dict, Any

from nexus.engine.graph import NexusGraphEngine
from nexus.models.findings import AnalysisReport, Finding
from nexus.providers.base import BaseInferenceProvider
from nexus.providers.demo import DemoProvider
from nexus.scenarios.offline_cloud_dependency import build_offline_cloud_dependency_scenario
from nexus.analyzers.belief_blast_radius import analyze_belief_blast_radius
from nexus.analyzers.context_flip import analyze_context_flip
from nexus.analyzers.goal_rot import analyze_goal_rot
from nexus.analyzers.assumption_debt import analyze_assumption_debt
from nexus.storage.repository import LocalExperimentRepository
from nexus.security.input_limits import validate_input_length


class NexusWorkflowEngine:
    """
    Executes the unified end-to-end failure analysis:
    1. Graph construction & validation
    2. GoalRot evaluation
    3. ContextFlip controlled mutation experiments
    4. AssumptionDebt deterministic tests
    5. BeliefBlast Radius downstream propagation
    6. Metrics compilation and storage
    """

    def __init__(self, repository: Optional[LocalExperimentRepository] = None):
        self.repository = repository or LocalExperimentRepository()

    def run_analysis(
        self,
        provider: Optional[BaseInferenceProvider] = None,
        custom_input_text: Optional[str] = None,
    ) -> AnalysisReport:
        active_provider = provider or DemoProvider()
        t_start = time.perf_counter()

        # Input boundary validation
        if custom_input_text:
            validate_input_length(custom_input_text)

        # Build signature reference scenario
        engine, scenario_id, scenario_title = build_offline_cloud_dependency_scenario()

        # Module C: GoalRot Analysis
        goal_findings = analyze_goal_rot(engine)

        # Module B: ContextFlip Analysis
        context_findings, mutations = analyze_context_flip(engine)

        # Module D: AssumptionDebt Analysis
        assumption_findings, test_records = analyze_assumption_debt(engine)

        # Module A: BeliefBlast Radius Analysis
        blast_findings = analyze_belief_blast_radius(engine, focus_node_id="decision_arch_revised")

        # Combine all findings
        all_findings: List[Finding] = []
        all_findings.extend(goal_findings)
        all_findings.extend(context_findings)
        all_findings.extend(assumption_findings)
        all_findings.extend(blast_findings)

        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # Metrics calculation
        critical_count = sum(1 for f in all_findings if f.severity.value == "critical")
        high_count = sum(1 for f in all_findings if f.severity.value == "high")
        unverified_assumptions = sum(1 for n in engine.get_all_nodes() if n.type.value == "assumption")

        metrics = {
            "wall_clock_ms": elapsed_ms,
            "total_nodes": engine.node_count,
            "total_edges": engine.edge_count,
            "findings_count": len(all_findings),
            "critical_violations": critical_count,
            "high_severity_risks": high_count,
            "assumptions_identified": unverified_assumptions,
            "mutations_tested": len(mutations),
            "observed_decision_flips": sum(1 for m in mutations if m.decision_flipped),
            "deterministic_checks_passed": sum(1 for t in test_records if t.status.value == "passed"),
            "deterministic_checks_failed": sum(1 for t in test_records if t.status.value == "failed"),
        }

        limitations = [
            "Research diagnostic tool: identifies empirical risks and plan divergence; not a formal mathematical verification engine.",
            "Local SQLite history is unencrypted at rest; accessible to accounts with host filesystem permissions.",
            "In Demo Mode, outputs derive strictly from deterministic application rules and allowlisted fixtures.",
        ]

        report = AnalysisReport(
            scenario_id=scenario_id,
            scenario_title=scenario_title,
            timestamp=datetime.now().isoformat(),
            provider_name=active_provider.name,
            is_remote=active_provider.is_remote,
            nodes=engine.get_all_nodes(),
            edges=engine.get_all_edges(),
            findings=all_findings,
            assumption_tests=test_records,
            context_mutations=mutations,
            metrics=metrics,
            limitations=limitations,
        )

        # Persist report to local database
        self.repository.save_report(report)

        return report
