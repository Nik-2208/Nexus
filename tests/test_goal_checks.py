from nexus.scenarios.offline_cloud_dependency import build_offline_cloud_dependency_scenario
from nexus.analyzers.goal_rot import analyze_goal_rot
from nexus.models.findings import FindingSeverity


def test_goal_rot_detects_cloud_violation():
    engine, _, _ = build_offline_cloud_dependency_scenario()
    findings = analyze_goal_rot(engine)

    assert len(findings) >= 1
    # Check that critical offline violation was detected
    violation_found = any(f.severity == FindingSeverity.CRITICAL and "violate" in f.description.lower() for f in findings)
    assert violation_found, "GoalRot must detect explicit violation of offline requirement"
