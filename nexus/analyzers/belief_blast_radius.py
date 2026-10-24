"""Module A: BeliefBlast Radius analyzer."""

from typing import List, Set
from nexus.models.entities import NodeType, ProvenanceType
from nexus.models.findings import Finding, ModuleType, FindingSeverity
from nexus.engine.graph import NexusGraphEngine


def analyze_belief_blast_radius(engine: NexusGraphEngine, focus_node_id: str = "decision_arch_revised") -> List[Finding]:
    """
    Traces downstream impact from a contradicted claim or revised decision.
    Distinguishes 'potentially affected' artifacts from confirmed broken components.
    """
    findings: List[Finding] = []
    node = engine.get_node(focus_node_id)
    if not node:
        return findings

    downstream_ids = engine.calculate_downstream_blast_radius(focus_node_id)

    affected_artifacts: List[str] = []
    affected_actions: List[str] = []

    for d_id in downstream_ids:
        d_node = engine.get_node(d_id)
        if not d_node:
            continue
        if d_node.type == NodeType.ARTIFACT:
            affected_artifacts.append(d_node.label)
        elif d_node.type == NodeType.ACTION:
            affected_actions.append(d_node.label)

    desc = (
        f"Altering or adopting '{node.label}' propagates potentially destabilizing changes "
        f"across {len(downstream_ids)} downstream entities. Specifically affected artifacts: "
        f"{', '.join(affected_artifacts) if affected_artifacts else 'None'}; "
        f"affected actions: {', '.join(affected_actions) if affected_actions else 'None'}."
    )

    findings.append(
        Finding(
            id=f"blast_radius_{focus_node_id}",
            module=ModuleType.BELIEF_BLAST_RADIUS,
            title=f"BeliefBlast Radius: {node.label}",
            description=desc,
            severity=FindingSeverity.HIGH if affected_artifacts else FindingSeverity.MEDIUM,
            severity_rationale="Downstream artifacts and code configuration are modified based on a fragile or revised claim.",
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            evidence_ids=[focus_node_id],
            deterministic_check_executed=True,
            affected_entity_ids=list(downstream_ids),
            remediation_suggestion="Audit and isolate affected configuration files and documentation before committing changes.",
        )
    )

    return findings
