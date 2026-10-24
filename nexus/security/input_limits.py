"""Security utilities for input boundaries and limit enforcement."""

from nexus.config import MAX_COMBINED_INPUT_LENGTH, MAX_GRAPH_NODES, MAX_GRAPH_EDGES, MAX_MUTATIONS_PER_RUN


class InputLimitExceededError(ValueError):
    """Raised when user-provided or aggregated input exceeds defined safety limits."""
    pass


def validate_input_length(text: str, max_length: int = MAX_COMBINED_INPUT_LENGTH) -> str:
    """
    Validates that text length is within allowed bounded limits.
    Fails closed if violated.
    """
    if text is None:
        return ""
    if len(text) > max_length:
        raise InputLimitExceededError(
            f"Input size ({len(text)} chars) exceeds maximum safety limit of {max_length} characters."
        )
    return text


def check_graph_limits(node_count: int, edge_count: int) -> None:
    """Ensures graph complexity is bounded against resource exhaustion."""
    if node_count > MAX_GRAPH_NODES:
        raise InputLimitExceededError(
            f"Graph node count ({node_count}) exceeds limit of {MAX_GRAPH_NODES} nodes."
        )
    if edge_count > MAX_GRAPH_EDGES:
        raise InputLimitExceededError(
            f"Graph edge count ({edge_count}) exceeds limit of {MAX_GRAPH_EDGES} edges."
        )


def check_mutation_limit(mutation_count: int) -> None:
    """Ensures context mutations do not exceed bounding limits."""
    if mutation_count > MAX_MUTATIONS_PER_RUN:
        raise InputLimitExceededError(
            f"Mutation count ({mutation_count}) exceeds maximum allowed mutations ({MAX_MUTATIONS_PER_RUN})."
        )
