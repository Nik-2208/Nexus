"""Allowlisted deterministic tests registry for safe assumption verification."""

from typing import Dict, Any, Callable
from nexus.models.entities import AssumptionTestStatus, AssumptionTestRecord, ProvenanceType


def test_library_feature_available(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates whether a named feature or offline dependency is present in local runtime.
    Synthetic safe evaluation for offline agent scenario.
    """
    feature_name = inputs.get("feature", "")
    target_env = inputs.get("environment", "local")

    # In our deterministic scenario, local_onnx_quantizer is NOT available offline
    if feature_name == "local_quantizer_v2":
        return {
            "status": AssumptionTestStatus.FAILED,
            "details": "Feature 'local_quantizer_v2' is absent in the specified offline local environment.",
            "outputs": {"found": False, "required_version": ">=2.0", "installed_version": "None"}
        }
    elif feature_name == "basic_local_inference":
        return {
            "status": AssumptionTestStatus.PASSED,
            "details": "Local inference engine baseline available.",
            "outputs": {"found": True, "installed_version": "1.0.0"}
        }
    return {
        "status": AssumptionTestStatus.INCONCLUSIVE,
        "details": f"Unknown or untestable feature flag: '{feature_name}'.",
        "outputs": {"found": None}
    }


def test_offline_constraint_compatible(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tests whether a network host or architecture mode complies with strict offline isolation.
    """
    host = inputs.get("target_host", "")
    is_offline_required = inputs.get("offline_required", True)

    if not is_offline_required:
        return {
            "status": AssumptionTestStatus.PASSED,
            "details": "Offline constraint not enforced for this component.",
            "outputs": {"compatible": True}
        }

    # If host targets remote cloud (e.g. api.cloudinference.com)
    if "cloud" in host.lower() or "api." in host.lower() or host not in ("127.0.0.1", "localhost", "none", ""):
        return {
            "status": AssumptionTestStatus.FAILED,
            "details": f"Target host '{host}' requires internet egress, violating offline requirement.",
            "outputs": {"compatible": False, "violating_host": host}
        }

    return {
        "status": AssumptionTestStatus.PASSED,
        "details": "Target conforms to loopback or local-only boundaries.",
        "outputs": {"compatible": True}
    }


# ALLOWLISTED DISPATCHER (Strictly bounded: No arbitrary execution, no eval)
TEST_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "test_library_feature_available": test_library_feature_available,
    "test_offline_constraint_compatible": test_offline_constraint_compatible,
}


def execute_registered_test(test_name: str, assumption_id: str, inputs: Dict[str, Any]) -> AssumptionTestRecord:
    """
    Executes an allowlisted deterministic test function.
    Rejects unregistered test names safely.
    """
    if test_name not in TEST_REGISTRY:
        return AssumptionTestRecord(
            test_id=f"test_{assumption_id}",
            assumption_id=assumption_id,
            name=test_name,
            status=AssumptionTestStatus.INVALID_INPUT,
            inputs=inputs,
            outputs={},
            provenance=ProvenanceType.DETERMINISTIC_RULE,
            details=f"Test '{test_name}' is not in the allowlisted test registry.",
        )

    handler = TEST_REGISTRY[test_name]
    res = handler(inputs)

    return AssumptionTestRecord(
        test_id=f"test_{assumption_id}",
        assumption_id=assumption_id,
        name=test_name,
        status=res.get("status", AssumptionTestStatus.INCONCLUSIVE),
        inputs=inputs,
        outputs=res.get("outputs", {}),
        provenance=ProvenanceType.OBSERVED_EXPERIMENT,
        details=res.get("details", ""),
    )
