from nexus.engine.graph import NexusGraphEngine
from nexus.models.entities import GraphNode, GraphEdge, NodeType, EdgeRelation, ProvenanceType


def test_graph_construction_and_blast_radius():
    engine = NexusGraphEngine()
    n1 = GraphNode(id="n1", type=NodeType.DECISION, label="Decision 1", description="Initial")
    n2 = GraphNode(id="n2", type=NodeType.ACTION, label="Action 1", description="Deploy")
    n3 = GraphNode(id="n3", type=NodeType.ARTIFACT, label="Config", description="config.yaml")

    engine.add_node(n1)
    engine.add_node(n2)
    engine.add_node(n3)

    engine.add_edge(GraphEdge(source="n1", target="n2", relation=EdgeRelation.INFLUENCES))
    engine.add_edge(GraphEdge(source="n2", target="n3", relation=EdgeRelation.MODIFIES))

    radius = engine.calculate_downstream_blast_radius("n1")
    assert "n2" in radius
    assert "n3" in radius
    assert len(radius) == 2


def test_cycle_handling_safe():
    engine = NexusGraphEngine()
    n1 = GraphNode(id="a", type=NodeType.CLAIM, label="A", description="Claim A")
    n2 = GraphNode(id="b", type=NodeType.CLAIM, label="B", description="Claim B")
    engine.add_node(n1)
    engine.add_node(n2)

    # Add cycle A -> B -> A
    engine.add_edge(GraphEdge(source="a", target="b", relation=EdgeRelation.SUPPORTS))
    engine.add_edge(GraphEdge(source="b", target="a", relation=EdgeRelation.SUPPORTS))

    cycles = engine.detect_cycles()
    assert len(cycles) > 0

    # Downstream blast radius should not infinite loop
    radius = engine.calculate_downstream_blast_radius("a", max_depth=5)
    assert "b" in radius
