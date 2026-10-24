"""Structured findings and experiment run models."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from nexus.models.entities import ProvenanceType, GraphNode, GraphEdge, AssumptionTestRecord


class ModuleType(str, Enum):
    BELIEF_BLAST_RADIUS = "BeliefBlast Radius"
    CONTEXT_FLIP = "ContextFlip"
    GOAL_ROT = "GoalRot"
    ASSUMPTION_DEBT = "AssumptionDebt"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    id: str = Field(..., max_length=128)
    module: ModuleType
    title: str = Field(..., max_length=256)
    description: str = Field(..., max_length=4096)
    severity: FindingSeverity
    severity_rationale: str = Field(..., max_length=1024)
    provenance: ProvenanceType
    evidence_ids: List[str] = Field(default_factory=list)
    deterministic_check_executed: bool = False
    human_reviewed: bool = False
    affected_entity_ids: List[str] = Field(default_factory=list)
    remediation_suggestion: Optional[str] = None


class ContextMutationRecord(BaseModel):
    mutation_id: str
    description: str
    target_node_id: str
    original_value: str
    mutated_value: str
    decision_flipped: bool
    baseline_decision: str
    mutated_decision: str
    provenance: ProvenanceType
    execution_time_ms: float = 0.0


class AnalysisReport(BaseModel):
    scenario_id: str
    scenario_title: str
    timestamp: str
    provider_name: str
    is_remote: bool
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    findings: List[Finding]
    assumption_tests: List[AssumptionTestRecord]
    context_mutations: List[ContextMutationRecord]
    metrics: Dict[str, Any]
    limitations: List[str]
