"""Signature scenario: Offline Coding Agent - Hidden Cloud Dependency."""

from typing import Tuple, List
from nexus.models.entities import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeRelation,
    ProvenanceType,
)
from nexus.engine.graph import NexusGraphEngine


def build_offline_cloud_dependency_scenario() -> Tuple[NexusGraphEngine, str, str]:
    """
    Builds the deterministic reference scenario:
    - Original Objective: Design local-first offline application without cloud dependency.
    - Agent assumes unverified library feature 'local_quantizer_v2'.
    - Agent receives contradictory docs indicating feature unavailable.
    - Revised architecture adopts remote Cloud Inference API.
    - Updates config and doc artifacts.
    - Violates initial offline requirement.
    """
    engine = NexusGraphEngine()
    scenario_id = "scenario_offline_cloud_dep"
    title = "Offline Coding Agent — Hidden Cloud Dependency"

    # Nodes
    nodes = [
        GraphNode(
            id="goal_offline_only",
            type=NodeType.GOAL,
            label="Offline Operation Invariant",
            description="The application must operate fully offline and must not depend on a cloud inference service.",
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            metadata={"predicate": "offline_only", "source_quote": "must operate without internet access or cloud inference"},
        ),
        GraphNode(
            id="assumption_lib_feature",
            type=NodeType.ASSUMPTION,
            label="Local Quantizer Library Available",
            description="Assumes that 'local_quantizer_v2' is packaged and available in the offline runtime environment.",
            provenance=ProvenanceType.UNVERIFIED,
            metadata={
                "test_name": "test_library_feature_available",
                "test_inputs": {"feature": "local_quantizer_v2", "environment": "local"},
            },
        ),
        GraphNode(
            id="decision_arch_initial",
            type=NodeType.DECISION,
            label="Initial Local-Only Architecture",
            description="Plan step 1: Execute all inference using local quantization runtime.",
            provenance=ProvenanceType.MODEL_INFERRED,
        ),
        GraphNode(
            id="evidence_contradictory_doc",
            type=NodeType.EVIDENCE,
            label="Library Documentation Update",
            description="Release notes state 'local_quantizer_v2' was deprecated and removed; requires cloud fall-back.",
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            is_contradicted=False,
        ),
        GraphNode(
            id="decision_arch_revised",
            type=NodeType.DECISION,
            label="Revised Architecture (Cloud Fallback)",
            description="Agent switches to hosted Cloud Inference API to compensate for missing local quantizer.",
            provenance=ProvenanceType.MODEL_INFERRED,
            metadata={"introduced_host": "api.cloudinference.com"},
        ),
        GraphNode(
            id="action_add_cloud_dep",
            type=NodeType.ACTION,
            label="Add Cloud API Client Dependency",
            description="Agent adds 'remote-cloud-client>=2.0' to dependencies and network calls in codebase.",
            provenance=ProvenanceType.MODEL_INFERRED,
            metadata={"violates_goal": "goal_offline_only"},
        ),
        GraphNode(
            id="artifact_config_yaml",
            type=NodeType.ARTIFACT,
            label="runtime_config.yaml",
            description="Generated config file specifying endpoint: 'https://api.cloudinference.com/v1'.",
            provenance=ProvenanceType.MODEL_INFERRED,
        ),
        GraphNode(
            id="artifact_readme_md",
            type=NodeType.ARTIFACT,
            label="README.md Setup Guide",
            description="Generated user documentation instructing user to supply CLOUD_API_KEY for inference.",
            provenance=ProvenanceType.MODEL_INFERRED,
        ),
    ]

    for node in nodes:
        engine.add_node(node)

    # Edges
    edges = [
        GraphEdge(
            source="decision_arch_initial",
            target="goal_offline_only",
            relation=EdgeRelation.SUPPORTS,
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            description="Initial local plan satisfies offline requirement.",
        ),
        GraphEdge(
            source="decision_arch_initial",
            target="assumption_lib_feature",
            relation=EdgeRelation.ASSUMES,
            provenance=ProvenanceType.MODEL_INFERRED,
            description="Initial plan relies directly on unverified library feature.",
        ),
        GraphEdge(
            source="evidence_contradictory_doc",
            target="assumption_lib_feature",
            relation=EdgeRelation.CONTRADICTS,
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            description="Documentation disproves the assumption that local_quantizer_v2 is available.",
        ),
        GraphEdge(
            source="decision_arch_revised",
            target="evidence_contradictory_doc",
            relation=EdgeRelation.DERIVED_FROM,
            provenance=ProvenanceType.MODEL_INFERRED,
            description="Revised plan was prompted by the contradictory documentation.",
        ),
        GraphEdge(
            source="decision_arch_revised",
            target="action_add_cloud_dep",
            relation=EdgeRelation.INFLUENCES,
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            description="Decision leads directly to adding the cloud dependency.",
        ),
        GraphEdge(
            source="action_add_cloud_dep",
            target="goal_offline_only",
            relation=EdgeRelation.VIOLATES,
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            description="Introducing cloud inference directly violates the offline-only requirement.",
        ),
        GraphEdge(
            source="decision_arch_revised",
            target="artifact_config_yaml",
            relation=EdgeRelation.MODIFIES,
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            description="Generates cloud endpoint configuration.",
        ),
        GraphEdge(
            source="decision_arch_revised",
            target="artifact_readme_md",
            relation=EdgeRelation.MODIFIES,
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            description="Generates README instructing users to setup cloud API keys.",
        ),
    ]

    for edge in edges:
        engine.add_edge(edge)

    return engine, scenario_id, title
