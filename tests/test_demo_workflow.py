from nexus.engine.workflow import NexusWorkflowEngine
from nexus.providers.demo import DemoProvider


def test_demo_workflow_end_to_end():
    engine = NexusWorkflowEngine()
    report = engine.run_analysis(provider=DemoProvider())

    assert report is not None
    assert report.scenario_id == "scenario_offline_cloud_dep"
    assert len(report.findings) >= 4
    assert len(report.nodes) > 5
    assert len(report.edges) > 5
    assert report.is_remote is False
    assert report.metrics["findings_count"] >= 4
