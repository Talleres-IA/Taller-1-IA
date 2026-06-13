"""Search problem definitions for the Panini logistics domain."""

from __future__ import annotations

import math
from typing import Any, Hashable

from algorithms import utils
from graph.road_graph import ColombiaRoadGraph

State = Hashable


class SearchProblem:
    """Abstract interface consumed by the generic search algorithms."""

    def getStartState(self) -> State:
        utils.raiseNotDefined()

    def isGoalState(self, _state: State) -> bool:
        utils.raiseNotDefined()

    def getSuccessors(self, _state: State) -> list[tuple[State, str, float]]:
        """Return triples `(successor, action, stepCost)`."""

        utils.raiseNotDefined()

    def getCostOfActions(self, _actions: list[str] | None) -> float:
        utils.raiseNotDefined()


class SingleDeliveryProblem(SearchProblem):
    """Find a route from a Panini warehouse to one fan location."""

    def __init__(
        self,
        graph: ColombiaRoadGraph,
        start: str,
        goal: str,
        cost_mode: str = "distance",
    ) -> None:
        self.graph = graph
        self.start = graph.resolve_node(start)
        self.goal = graph.resolve_node(goal)
        self.cost_mode = cost_mode
        self._expanded = 0
        self._expanded_nodes: set[str] = set()
        self.heuristicInfo: dict[str, Any] = {}

    def getStartState(self) -> str:
        return self.start

    def isGoalState(self, state: str) -> bool:
        return state == self.goal

    def getSuccessors(self, state: str) -> list[tuple[str, str, float]]:
        self._expanded += 1
        self._expanded_nodes.add(state)
        successors = []
        for edge in self.graph.neighbors(state):
            cost = 1.0 if self.cost_mode == "stops" else edge.distance_km
            successors.append((edge.target, edge.action, cost))
        return successors

    def getCostOfActions(self, actions: list[str] | None) -> float:
        if actions is None:
            return math.inf
        current = self.start
        total = 0.0
        for action in actions:
            edge = self.graph.get_edge(current, action)
            if edge is None:
                return math.inf
            total += 1.0 if self.cost_mode == "stops" else edge.distance_km
            current = action
        return total


class FewestStopsDeliveryProblem(SingleDeliveryProblem):
    """Variant where each edge has unit cost, regardless of road length."""

    def __init__(self, graph: ColombiaRoadGraph, start: str, goal: str) -> None:
        super().__init__(graph, start, goal, cost_mode="stops")


class MultiDeliveryProblem(SearchProblem):
    """Visit several delivery destinations in any order.

    State: `(current_node, remaining_deliveries)`, where `remaining_deliveries`
    is a frozenset of city node IDs still to be reached.
    """

    def __init__(
        self,
        graph: ColombiaRoadGraph,
        start: str,
        deliveries: list[str] | tuple[str, ...],
    ) -> None:
        self.graph = graph
        self.start = graph.resolve_node(start)
        resolved = frozenset(graph.resolve_node(node) for node in deliveries)
        self.deliveries = resolved - {self.start}
        self._expanded = 0
        self._expanded_nodes: set[str] = set()
        self.heuristicInfo: dict[str, Any] = {}

    def getStartState(self) -> tuple[str, frozenset[str]]:
        return (self.start, self.deliveries)

    def isGoalState(self, state: tuple[str, frozenset[str]]) -> bool:
        return len(state[1]) == 0

    def getSuccessors(
        self, state: tuple[str, frozenset[str]]
    ) -> list[tuple[tuple[str, frozenset[str]], str, float]]:
        current, remaining = state
        self._expanded += 1
        self._expanded_nodes.add(current)
        successors = []
        for edge in self.graph.neighbors(current):
            next_remaining = remaining - {edge.target}
            successors.append(
                ((edge.target, next_remaining), edge.action, edge.distance_km)
            )
        return successors

    def getCostOfActions(self, actions: list[str] | None) -> float:
        if actions is None:
            return math.inf
        current = self.start
        total = 0.0
        for action in actions:
            edge = self.graph.get_edge(current, action)
            if edge is None:
                return math.inf
            total += edge.distance_km
            current = action
        return total


def actions_to_route(start: str, actions: list[str]) -> list[str]:
    return [start, *actions]
