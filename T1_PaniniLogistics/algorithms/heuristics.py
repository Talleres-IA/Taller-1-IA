"""Heuristics for graph-search delivery problems."""

from __future__ import annotations

import math
from typing import Any

from algorithms import utils
from graph.road_graph import haversine_km


def nullHeuristic(_state: Any, _problem: Any = None) -> float:
    """A trivial admissible heuristic."""

    return 0.0


def straightLineHeuristic(state: str, problem: Any) -> float:
    """Geodesic distance from the current node to the destination.

    Tips:
    - Use `problem.graph.coordinates` and `haversine_km`.
    - Return 0 when the problem optimizes number of stops, not kilometers.
    """

    ### YOUR CODE HERE ###
    utils.raiseNotDefined()
    # mostrar frontera, costo, nodos expandidos, acciones...
    ### END YOUR CODE ###


def multiDeliveryHeuristic(state: tuple[str, frozenset[str]], problem: Any) -> float:
    """Admissible MST heuristic for the multi-delivery TSP-like problem.

    The estimate is:
      shortest-path distance from current node to the nearest remaining delivery
      + MST cost over the remaining deliveries using shortest-path distances.

    This is a lower bound on any route that visits all pending deliveries.

    Tips:
    - Split the state into current node and pending deliveries.
    - Cache pairwise road distances in `problem.heuristicInfo` to avoid recomputing.
    - Reuse `_mst_cost` with a distance function defined over delivery node IDs.
    """

    ### YOUR CODE HERE ###
    utils.raiseNotDefined()
    # mostrar frontera, costo, nodos expandidos, acciones...
    ### END YOUR CODE ###


def straightLineMultiDeliveryHeuristic(
    state: tuple[str, frozenset[str]], problem: Any
) -> float:
    """Lighter admissible MST heuristic using geodesic distances only.

    Tips:
    - Same structure as `multiDeliveryHeuristic`, but use geodesic distances only.
    - This trades some informativeness for much faster heuristic evaluation.
    """

    ### YOUR CODE HERE ###
    utils.raiseNotDefined()
    # mostrar frontera, costo, nodos expandidos, acciones...
    ### END YOUR CODE ###


def _mst_cost(nodes: list[str], distance_fn) -> float:
    if len(nodes) <= 1:
        return 0.0
    in_tree = {nodes[0]}
    total = 0.0
    while len(in_tree) < len(nodes):
        best_cost = math.inf
        best_node = None
        for source in in_tree:
            for target in nodes:
                if target in in_tree:
                    continue
                cost = distance_fn(source, target)
                if cost < best_cost:
                    best_cost = cost
                    best_node = target
        if best_node is None:
            return math.inf
        in_tree.add(best_node)
        total += best_cost
    return total
