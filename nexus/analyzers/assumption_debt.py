"""Module D: AssumptionDebt analyzer discovering assumptions and executing deterministic checks."""

from typing import List, Tuple
from nexus.models.entities import NodeType, AssumptionTestRecord, AssumptionTestStatus, ProvenanceType
from nexus.models.findings import Finding, ModuleType, FindingSeverity
from nexus.engine.graph import NexusGraphEngine
from nexus.tests_registry.deterministic_tests import execute_registered_test


def analyze_assumption_debt(engine: NexusGraphEngine) -> Tuple[List[Finding], List[AssumptionTestRecord]]:
    """
    Identifies unverified assumptions in the plan, explains why they matter,
    and runs allowlisted deterministic checks to evaluate them.
    """
    findings: List[Finding] = []
    test_records: List[AssumptionTestRecord] = []

    for node in engine.get_all_nodes():
        if node.type == NodeType.ASSUMPTION:
            # Check if there's a registered test definition in metadata
            test_name = node.metadata.get("test_name")
            test_inputs = node.metadata.get("test_inputs", {})

            if test_name:
                rec = execute_registered_test(test_name, node.id, test_inputs)
                test_records.append(rec)

                if rec.status == AssumptionTestStatus.FAILED:
                    findings.append(
                        Finding(
                            id=f"debt_failing_{node.id}",
                            module=ModuleType.ASSUMPTION_DEBT,
                            title=f"AssumptionDebt: Disproven Assumption '{node.label}'",
                            description=(
                                f"Assumption '{node.label}' ({node.description}) failed verification test "
                                f"'{test_name}'. Diagnostic: {rec.details}"
                            ),
                            severity=FindingSeverity.HIGH,
                            severity_rationale="Agent plan relied on an assumption that has been conclusively disproven.",
                            provenance=ProvenanceType.OBSERVED_EXPERIMENT,
                            evidence_ids=[node.id],
                            deterministic_check_executed=True,
                            affected_entity_ids=[node.id],
                            remediation_suggestion="Refactor plan to eliminate dependency on this unavailable feature.",
                        )
                    )
                else:
                    findings.append(
                        Finding(
                            id=f"debt_verified_{node.id}",
                            module=ModuleType.ASSUMPTION_DEBT,
                            title=f"AssumptionDebt: Tested Assumption '{node.label}'",
                            description=f"Assumption was evaluated with status: {rec.status.value}. {rec.details}",
                            severity=FindingSeverity.LOW if rec.status == AssumptionTestStatus.PASSED else FindingSeverity.MEDIUM,
                            severity_rationale="Empirical check executed.",
                            provenance=ProvenanceType.OBSERVED_EXPERIMENT,
                            evidence_ids=[node.id],
                            deterministic_check_executed=True,
                        )
                    )
            else:
                # Unverified assumption without automated test
                findings.append(
                    Finding(
                        id=f"debt_unverified_{node.id}",
                        module=ModuleType.ASSUMPTION_DEBT,
                        title=f"AssumptionDebt: Unverified Assumption '{node.label}'",
                        description=f"Unverified assumption '{node.description}' lacks an automated test. Downstream reliability is uncertain.",
                        severity=FindingSeverity.MEDIUM,
                        severity_rationale="Unverified assumptions create unmeasured risk.",
                        provenance=ProvenanceType.UNVERIFIED,
                        evidence_ids=[node.id],
                        deterministic_check_executed=False,
                    )
                )

    return findings, test_records
