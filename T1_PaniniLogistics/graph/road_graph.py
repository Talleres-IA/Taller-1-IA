"""Road graph model used by the Panini logistics search problems."""

from __future__ import annotations

import heapq
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class RoadNode:
    id: str
    lat: float
    lon: float
    name: str = ""
    department: str = ""
    kind: str = "osm_node"
    degree: int = 0


@dataclass(frozen=True)
class RoadEdge:
    source: str
    target: str
    distance_km: float
    mode: str = "road"
    name: str = ""
    highway: str = "primary"

    @property
    def action(self) -> str:
        return self.target


class ColombiaRoadGraph:
    """Undirected weighted graph over curated Colombian road corridors."""

    def __init__(
        self,
        nodes: dict[str, RoadNode],
        adjacency: dict[str, list[RoadEdge]],
    ) -> None:
        self.nodes = nodes
        self.adjacency = adjacency

    @classmethod
    def from_json(cls, path: str | Path) -> "ColombiaRoadGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        nodes = {
            item["id"]: RoadNode(
                id=item["id"],
                lat=float(item["lat"]),
                lon=float(item["lon"]),
                name=item.get("name", item["id"]),
                department=item.get("department", ""),
                kind=item.get("kind", "osm_node"),
                degree=int(item.get("degree", 0) or 0),
            )
            for item in data["nodes"]
        }

        adjacency: dict[str, list[RoadEdge]] = defaultdict(list)
        seen: set[tuple[str, str]] = set()
        for item in data["edges"]:
            source = item["source"]
            target = item["target"]
            if source not in nodes or target not in nodes:
                raise ValueError(f"Unknown edge endpoint: {source!r} -> {target!r}")
            distance = float(item["distance_km"])
            if distance <= 0:
                raise ValueError(f"Edge {source!r}->{target!r} has non-positive cost")
            mode = item.get("mode", "road")
            name = item.get("name", f"{source}-{target}")
            highway = item.get("highway", "primary")
            key = tuple(sorted((source, target)))
            if key in seen:
                continue
            seen.add(key)
            adjacency[source].append(
                RoadEdge(source, target, distance, mode, name, highway)
            )
            adjacency[target].append(
                RoadEdge(target, source, distance, mode, name, highway)
            )

        graph = cls(nodes=nodes, adjacency=dict(adjacency))
        graph.validate(raise_on_error=True)
        return graph

    def validate(self, raise_on_error: bool = False) -> list[str]:
        errors: list[str] = []
        for node_id in self.nodes:
            if node_id not in self.adjacency:
                errors.append(f"Node {node_id} has no incident edges")
        for source, edges in self.adjacency.items():
            if source not in self.nodes:
                errors.append(f"Adjacency references unknown node {source}")
            for edge in edges:
                if edge.target not in self.nodes:
                    errors.append(
                        f"Edge {source}->{edge.target} references unknown node"
                    )
                if edge.distance_km <= 0 or not math.isfinite(edge.distance_km):
                    errors.append(f"Edge {source}->{edge.target} has invalid cost")
                reverse = self.get_edge(edge.target, source)
                if reverse is None:
                    errors.append(f"Missing reverse edge for {source}->{edge.target}")
                elif abs(reverse.distance_km - edge.distance_km) > 1e-6:
                    errors.append(f"Asymmetric cost for {source}<->{edge.target}")
        components = self.connected_components()
        if len(components) != 1:
            errors.append(f"Graph has {len(components)} connected components")
        if raise_on_error and errors:
            raise ValueError("; ".join(errors))
        return errors

    def connected_components(self) -> list[set[str]]:
        unseen = set(self.nodes)
        components: list[set[str]] = []
        while unseen:
            start = unseen.pop()
            component = {start}
            queue: deque[str] = deque([start])
            while queue:
                current = queue.popleft()
                for edge in self.adjacency.get(current, []):
                    if edge.target in unseen:
                        unseen.remove(edge.target)
                        component.add(edge.target)
                        queue.append(edge.target)
            components.append(component)
        return components

    def neighbors(self, node_id: str) -> list[RoadEdge]:
        return self.adjacency[node_id]

    def get_edge(self, source: str, target: str) -> RoadEdge | None:
        for edge in self.adjacency.get(source, []):
            if edge.target == target:
                return edge
        return None

    def edge_cost(self, source: str, target: str) -> float:
        edge = self.get_edge(source, target)
        if edge is None:
            raise ValueError(f"No edge from {source!r} to {target!r}")
        return edge.distance_km

    def coordinates(self, node_id: str) -> tuple[float, float]:
        node = self.nodes[node_id]
        return node.lat, node.lon

    def node_label(self, node_id: str) -> str:
        node = self.nodes[node_id]
        if node.name and node.name != node.id:
            return f"{node.id} - {node.name}"
        return f"{node.id} ({node.lat:.5f}, {node.lon:.5f})"

    def resolve_node(self, text: str) -> str:
        if text in self.nodes:
            return text
        raise KeyError(
            f"Unknown node id {text!r}. Use the notebook map to inspect IDs."
        )

    def shortest_path(
        self,
        start: str,
        goal: str,
        weight: str = "distance_km",
    ) -> tuple[list[str], float, int]:
        """Dijkstra helper used for validation and route comparisons."""

        frontier: list[tuple[float, int, str]] = [(0.0, 0, start)]
        parent: dict[str, str] = {}
        best = {start: 0.0}
        expanded = 0
        counter = 1
        while frontier:
            cost, _, node = heapq.heappop(frontier)
            if cost > best[node]:
                continue
            expanded += 1
            if node == goal:
                return _reconstruct_nodes(parent, goal), cost, expanded
            for edge in self.neighbors(node):
                step = 1.0 if weight == "stops" else edge.distance_km
                new_cost = cost + step
                if new_cost < best.get(edge.target, math.inf):
                    best[edge.target] = new_cost
                    parent[edge.target] = node
                    heapq.heappush(frontier, (new_cost, counter, edge.target))
                    counter += 1
        return [], math.inf, expanded

    def route_cost(self, route: Iterable[str]) -> float:
        route_list = list(route)
        total = 0.0
        for source, target in zip(route_list, route_list[1:], strict=False):
            total += self.edge_cost(source, target)
        return total

    def route_coordinates(self, route: Iterable[str]) -> list[tuple[float, float]]:
        return [self.coordinates(node_id) for node_id in route]

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self.adjacency.values()) // 2

def load_default_graph() -> ColombiaRoadGraph:
    path = Path(__file__).resolve().parents[1] / "data" / "colombia_roads.json"
    return ColombiaRoadGraph.from_json(path)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(value))


def _reconstruct_nodes(parent: dict[str, str], goal: str) -> list[str]:
    route = [goal]
    while route[-1] in parent:
        route.append(parent[route[-1]])
    route.reverse()
    return route
