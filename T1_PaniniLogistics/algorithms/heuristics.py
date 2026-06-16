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
    """

    ### YOUR CODE HERE ###
    # VERSIÓN INICIAL autoría propia:
    # Se tenía una idea parcial del loop para calcular la distancia mínima,
    # pero con errores de nombres de variables y sin retorno:
    #
    # actual, elresto = state
    # mindist = math.inf
    # for n in elresto:
    #     cooractual = problem.graph.coordinates[actual]
    #     coornodo = problem.graph.coordinates[nodo]  # nodo no definido, debía ser n
    #     dist = haversine_km(cooractual, coornodo)
    #     if dist < mindist:
    #         mindist = dist
    # def distance_fn(a,b):
    #     for m in elresto:              # loop innecesario
    #         act = problem.graph.coordinates[a]
    #         nod = problem.graph.coordinates[b]
    #         distanciaa = haversine_km(act, nod)  # faltaba return
    #
    # PROMPTS USADOS CON IA (Claude):
    #
    # 1. "cómo estructuro la heurística para MultiDelivery?"
    #     La heurística tiene dos términos: distancia mínima desde el nodo
    #      actual al pendiente más cercano, más el MST sobre los pendientes.
    #      A diferencia de SingleDelivery, no hay cost_mode el estado incluye
    #      el nodo actual y un frozenset de entregas pendientes.
    #
    # 2. "cómo queda distance_fn para pasarle a _mst_cost?"
    #     distance_fn recibe dos nodos a y b, obtiene sus coordenadas y
    #      retorna haversine_km entre ellos. No necesita loop.
    #
    # 3. "cuál es el caso borde?"
    #     Cuando elresto está vacío significa que ya se visitaron todas las
    #      entregas, entonces se retorna 0.0.
    actual, elresto = state
    if not elresto:
        return 0.0
    mindist = math.inf
    for n in elresto:
        cooractual = problem.graph.coordinates(actual)
        coornodo = problem.graph.coordinates(n)
        dist = haversine_km(cooractual, coornodo)
        if dist < mindist:
            mindist = dist

    def distance_fn(a, b):
        act = problem.graph.coordinates(a)
        nod = problem.graph.coordinates(b)
        return haversine_km(act, nod)

    mst = _mst_cost(list(elresto), distance_fn)
    return mindist + mst

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
    # mostrar frontera, costo, nodos expandidos, acciones...
    ### END YOUR CODE ###
    actual, elresto = state
    if not elresto:
        return 0.0
    mindist = math.inf
    for i in elresto:
        actual = problem.graph.coordinates[actual]
        siguiente = problem.graph.coordinates[i]
        distancia = haversine_km(actual,siguiente)
        if distancia < mindist:
            mindist = distancia
    def distance_fn(a,b):
        act = problem.graph.coordinates[a]
        nod = problem.graph.coordinates[b]
        return haversine_km(act, nod)
    mst = _mst_cost(list(elresto),distance_fn)
    return mindist + mst
    


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
