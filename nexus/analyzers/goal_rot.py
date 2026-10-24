"""Module C: GoalRot analyzer evaluating divergence against explicit constraints."""

from typing import List
from nexus.models.entities import NodeType, EdgeRelation, ProvenanceType
from nexus.models.findings import Finding, ModuleType, FindingSeverity
from nexus.engine.graph import NexusGraphEngine


def analyze_goal_rot(engine: NexusGraphEngine) -> List[Finding]:
    """
    Evaluates actions and decisions against explicit requirements/goals.
    Flags cloud dependency as a deterministic goal violation of offline-only constraints.
    """
    findings: List[Finding] = []

    # Traverse all edges looking for explicit VIOLATES relations
    for edge in engine.get_all_edges():
        if edge.relation == EdgeRelation.VIOLATES:
            source_node = engine.get_node(edge.source)
            target_goal = engine.get_node(edge.target)
            if source_node and target_goal:
                findings.append(
                    Finding(
                        id=f"goal_rot_{source_node.id}_{target_goal.id}",
                        module=ModuleType.GOAL_ROT,
                        title=f"GoalRot: Critical Invariant Violation in {source_node.label}",
                        description=(
                            f"Proposed step '{source_node.label}' ({source_node.description}) directly "
                            f"violates explicit requirement '{target_goal.label}' ({target_goal.description}). "
                            "Plan has diverged from user-specified boundaries."
                        ),
                        severity=FindingSeverity.CRITICAL,
                        severity_rationale="A non-negotiable user objective or offline constraint was breached by downstream actions.",
                        provenance=ProvenanceType.DETERMINISTIC_RULE,
                        evidence_ids=[source_node.id, target_goal.id],
                        deterministic_check_executed=True,
                        affected_entity_ids=[source_node.id, target_goal.id],
                        remediation_suggestion="Reject cloud fallback; constrain agent to local model architectures or fail closed.",
                    )
                )

    # Secondary inspection: nodes mentioning remote endpoints without local loopback
    for node in engine.get_all_nodes():
        if node.type in (NodeType.ACTION, NodeType.DECISION, NodeType.ARTIFACT):
            desc_lower = node.description.lower()
            if "cloud" in desc_lower or "api." in desc_lower:
                # Check if already caught
                already_caught = any(node.id in f.evidence_ids for f in findings)
                if not already_caught:
                    findings.append(
                        Finding(
                            id=f"goal_rot_suspicious_{node.id}",
                            module=ModuleType.GOAL_ROT,
                            title=f"GoalRot (Suspicious): External Service Reference in {node.label}",
                            description=f"Entity '{node.label}' references external service infrastructure: '{node.description}'.",
                            severity=FindingSeverity.HIGH,
                            severity_rationale="Unconfirmed external service references may breach local isolation policy.",
                            provenance=ProvenanceType.DETERMINISTIC_RULE,
                            evidence_ids=[node.id],
                            deterministic_check_executed=True,
                            affected_entity_ids=[node.id],
                            remediation_suggestion="Verify host endpoint conforms to loopback before deployment.",
                        )
                    )

    return findings
