"""Strict typed entities for the shared decision-and-assumption graph."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProvenanceType(str, Enum):
    DETERMINISTIC_RULE = "deterministic_rule"
    OBSERVED_EXPERIMENT = "observed_experiment"
    MODEL_INFERRED = "model_inferred"
    HUMAN_REVIEWED = "human_reviewed"
    UNVERIFIED = "unverified"


class NodeType(str, Enum):
    GOAL = "goal"
    CONSTRAINT = "constraint"
    CLAIM = "claim"
    ASSUMPTION = "assumption"
    DECISION = "decision"
    ACTION = "action"
    ARTIFACT = "artifact"
    EVIDENCE = "evidence"
    TEST_RESULT = "test_result"


class EdgeRelation(str, Enum):
    SUPPORTS = "supports"
    ASSUMES = "assumes"
    DERIVED_FROM = "derived_from"
    INFLUENCES = "influences"
    MODIFIES = "modifies"
    VIOLATES = "violates"
    VALIDATED_BY = "validated_by"
    CONTRADICTS = "contradicts"
    POTENTIALLY_AFFECTS = "potentially_affects"


class GraphNode(BaseModel):
    id: str = Field(..., max_length=128)
    type: NodeType
    label: str = Field(..., max_length=256)
    description: str = Field(..., max_length=2048)
    provenance: ProvenanceType = ProvenanceType.DETERMINISTIC_RULE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_contradicted: bool = False


class GraphEdge(BaseModel):
    source: str = Field(..., max_length=128)
    target: str = Field(..., max_length=128)
    relation: EdgeRelation
    provenance: ProvenanceType = ProvenanceType.DETERMINISTIC_RULE
    description: Optional[str] = Field(default=None, max_length=512)


class AssumptionTestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_RUN = "not_run"
    INCONCLUSIVE = "inconclusive"
    INVALID_INPUT = "invalid_input"


class AssumptionTestRecord(BaseModel):
    test_id: str
    assumption_id: str
    name: str
    status: AssumptionTestStatus
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    provenance: ProvenanceType = ProvenanceType.OBSERVED_EXPERIMENT
    execution_time_ms: float = 0.0
    details: str = ""
