"""Heuristics for graph-search delivery problems."""

from __future__ import annotations

import math
from typing import Any

from algorithms import utils
from graph.road_graph import haversine_km
from algorithms.problems import SearchProblem, State


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
    # VERSIÓN INICIAL de autoría propia:
    # Se planteó una heurística Manhattan sobre coordenadas:
    #
    # function heuristic(node):
    #     dx = abs(node.x - goal.x)
    #     dy = abs(node.y - goal.y)
    #     return D * (dx + dy)
    # El problema de esta versión es que Manhattan no es apropiada para
    # coordenadas geográficas (latitud/longitud), donde la distancia real
    # entre dos puntos sobre la superficie terrestre requiere haversine
    # PROMPTS USADOS CON IA (Claude):
    #
    # 1. "qué dos nodos necesito para calcular la distancia en línea recta?"
    #    El nodo actual es `state` (no problem.start), y el destino es problem.goal
    #
    # 2. "cómo retorno 0 cuando el problema optimiza paradas y no kilómetros?"
    #    Verificar hasattr(problem, 'cost_mode') and problem.cost_mode == 'stops'
    if hasattr(problem, "cost_mode") and problem.cost_mode == "stops":
        return 0.0
    actual = problem.graph.coordinates(state)
    meta = problem.graph.coordinates(problem.goal)
    return haversine_km(actual, meta)
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
    ===================================================================== 
    VERSION INICIAL (Cómputo Dinámico en Caliente):
    Esta versión original calculaba la distancia Dijkstra dinámicamente para cada par 
    (nodo_actual, entrega) durante la búsqueda. Debido a que el nodo actual de exploración 
    cambia continuamente, esto forzaba la ejecución de miles de Dijkstras en caliente, 
    haciendo que el algoritmo A* fallara por timeout para más de 3 entregas.

    Código Inicial:
    ====================================================================
    def get_road_distance(a: str, b: str) -> float:
        pair = tuple(sorted((a, b)))
        if pair in problem.heuristicInfo:
            return problem.heuristicInfo[pair]

        _, cost, _ = problem.graph.shortest_path(a, b)
        problem.heuristicInfo[pair] = cost
        return cost

    min_dist_to_delivery = min(get_road_distance(actual_node, d) for d in pending)
    mst_cost = _mst_cost(list(pending), get_road_distance)
    return min_dist_to_delivery + mst_cost
    ====================================================================

    Prompt usado con IA: Gemini Flash 3.5 Medium - Antigravity CLI
    Añade el precalculo al la funcion multiDeliveryHeuristic

    NUESTRO CAMBIO (Precálculo Único):
    Dado que el grafo es no dirigido y las entregas son estáticas, corremos Dijkstra una
    sola vez desde cada una de las k entregas al iniciar el problema. Esto calcula las
    distancias de camino mínimo desde cada entrega a todo el mapa, permitiendo consultas
    de distancia O(1) directas en diccionario en lugar de recalcular Dijkstra en cada nodo.
    """
    # Precompute all-pairs shortest paths from deliveries to all nodes in the graph
    if 'precomputed_distances' not in problem.heuristicInfo:
        precomputed = {}
        for d in problem.deliveries:
            distances = {}
            frontier = [(0.0, d)]
            best = {d: 0.0}
            while frontier:
                cost, node = heapq.heappop(frontier)
                if cost > best[node]:
                    continue
                distances[node] = cost
                for edge in problem.graph.neighbors(node):
                    new_cost = cost + edge.distance_km
                    if new_cost < best.get(edge.target, float('inf')):
                        best[edge.target] = new_cost
                        heapq.heappush(frontier, (new_cost, edge.target))
            precomputed[d] = distances
        problem.heuristicInfo['precomputed_distances'] = precomputed

    precomputed = problem.heuristicInfo['precomputed_distances']

    min_dist_to_delivery = min(precomputed[d].get(actual_node, float('inf')) for d in pending)

    def get_delivery_distance(a: str, b: str) -> float:
        return precomputed[a].get(b, float('inf'))

    mst_cost = _mst_cost(list(pending), get_delivery_distance)

    return min_dist_to_delivery + mst_cost


def straightLineMultiDeliveryHeuristic(
    state: tuple[str, frozenset[str]], problem: Any
) -> float:
    """Lighter admissible MST heuristic using geodesic distances only.

    Tips:
    - Same structure as `multiDeliveryHeuristic`, but use geodesic distances only.
    - This trades some informativeness for much faster heuristic evaluation.
    """

    actual_node, pending = state
    if not pending:
        return 0.0

    def distance_fn(a: str, b: str) -> float:
        coord_a = problem.graph.coordinates(a)
        coord_b = problem.graph.coordinates(b)
        return haversine_km(coord_a, coord_b)

    min_dist_to_delivery = min(distance_fn(actual_node, d) for d in pending)

    mst_cost = _mst_cost(list(pending), distance_fn)

    return min_dist_to_delivery + mst_cost
    


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
