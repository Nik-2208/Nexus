"""Deterministic Graph Engine managing nodes, edges, cycle detection, and blast radius traversal."""

from typing import List, Dict, Set, Optional, Tuple
import networkx as nx

from nexus.models.entities import GraphNode, GraphEdge, NodeType, EdgeRelation, ProvenanceType
from nexus.security.input_limits import check_graph_limits


class NexusGraphEngine:
    """
    Manages typed dependency graphs with cycle-safe deterministic traversal,
    impact tracing, and invariant checks.
    """

    def __init__(self):
        self._nx_graph = nx.DiGraph()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    def add_node(self, node: GraphNode) -> None:
        check_graph_limits(self.node_count + 1, self.edge_count)
        self._nodes[node.id] = node
        self._nx_graph.add_node(
            node.id,
            type=node.type.value,
            label=node.label,
            description=node.description,
            provenance=node.provenance.value,
            is_contradicted=node.is_contradicted,
        )

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self._nodes:
            raise ValueError(f"Source node '{edge.source}' does not exist in graph.")
        if edge.target not in self._nodes:
            raise ValueError(f"Target node '{edge.target}' does not exist in graph.")

        check_graph_limits(self.node_count, self.edge_count + 1)
        self._edges.append(edge)
        self._nx_graph.add_edge(
            edge.source,
            edge.target,
            relation=edge.relation.value,
            provenance=edge.provenance.value,
            description=edge.description,
        )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[GraphNode]:
        return list(self._nodes.values())

    def get_all_edges(self) -> List[GraphEdge]:
        return list(self._edges)

    def detect_cycles(self) -> List[List[str]]:
        """Identifies cycles if present without hanging."""
        try:
            return list(nx.simple_cycles(self._nx_graph))
        except Exception:
            return []

    def get_direct_dependents(self, node_id: str) -> List[str]:
        """Returns direct successor node IDs."""
        if not self._nx_graph.has_node(node_id):
            return []
        return list(self._nx_graph.successors(node_id))

    def get_direct_dependencies(self, node_id: str) -> List[str]:
        """Returns direct predecessor node IDs."""
        if not self._nx_graph.has_node(node_id):
            return []
        return list(self._nx_graph.predecessors(node_id))

    def calculate_downstream_blast_radius(self, node_id: str, max_depth: int = 10) -> Set[str]:
        """
        Calculates all reachable downstream entities starting from node_id
        within bounded depth, preventing recursion hangs on cyclic graphs.
        """
        if not self._nx_graph.has_node(node_id):
            return set()

        visited: Set[str] = set()
        queue: List[Tuple[str, int]] = [(node_id, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for succ in self._nx_graph.successors(curr):
                if succ not in visited:
                    visited.add(succ)
                    queue.append((succ, depth + 1))

        return visited

    def calculate_upstream_causes(self, node_id: str, max_depth: int = 10) -> Set[str]:
        """
        Calculates all upstream ancestors for root cause tracing.
        """
        if not self._nx_graph.has_node(node_id):
            return set()

        visited: Set[str] = set()
        queue: List[Tuple[str, int]] = [(node_id, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for pred in self._nx_graph.predecessors(curr):
                if pred not in visited:
                    visited.add(pred)
                    queue.append((pred, depth + 1))

        return visited

    def get_paths(self, source_id: str, target_id: str, cutoff: int = 5) -> List[List[str]]:
        """Returns all simple paths from source to target within bounded cutoff."""
        if not self._nx_graph.has_node(source_id) or not self._nx_graph.has_node(target_id):
            return []
        try:
            return list(nx.all_simple_paths(self._nx_graph, source=source_id, target=target_id, cutoff=cutoff))
        except Exception:
            return []
