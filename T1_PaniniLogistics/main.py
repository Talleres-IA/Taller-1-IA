"""Command-line runner for the Panini logistics search workshop."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Callable

import algorithms.heuristics as heuristics
import algorithms.search as search
from algorithms.problems import (
    FewestStopsDeliveryProblem,
    MultiDeliveryProblem,
    SearchProblem,
    SingleDeliveryProblem,
    actions_to_route,
)
from graph.road_graph import ColombiaRoadGraph
from visualization.map_view import show_route_map

WORKSHOP_ROOT = Path(__file__).resolve().parent
INSTANCE_PATH = WORKSHOP_ROOT / "data" / "instances.json"
DEFAULT_START_NODE = "n1037511"
DEFAULT_GOAL_NODE = "n39739"
ALGORITHM_CHOICES = (
    "dfs",
    "bfs",
    "ucs",
    "astar",
    "ids",
    "depthFirstSearch",
    "breadthFirstSearch",
    "uniformCostSearch",
    "aStarSearch",
    "iterativeDeepeningSearch",
)
ASTAR_ALGORITHMS = {"astar", "aStarSearch"}
IDS_ALGORITHMS = {"ids", "iterativeDeepeningSearch"}
ALGORITHM_ALIASES = {
    "depthFirstSearch": "dfs",
    "breadthFirstSearch": "bfs",
    "uniformCostSearch": "ucs",
    "aStarSearch": "astar",
    "iterativeDeepeningSearch": "ids",
}
RECOMMENDED_ALGORITHMS = {
    "single": {"ucs", "astar"},
    "stops": {"dfs", "bfs", "ids"},
    "multi": {"astar"},
}


def read_command(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run search algorithms over the Panini Colombia logistics graph."
    )
    parser.add_argument(
        "--graph",
        default=str(WORKSHOP_ROOT / "data" / "colombia_roads.json"),
        help="Path to the road graph JSON file",
    )
    parser.add_argument(
        "--problem",
        choices=["single", "stops", "multi"],
        default="single",
        help="Search problem type",
    )
    parser.add_argument(
        "--algorithm",
        "-a",
        choices=ALGORITHM_CHOICES,
        default="ucs",
        help="Search algorithm to execute",
    )
    parser.add_argument(
        "--heuristic",
        default=None,
        help="Heuristic function name for A*",
    )
    parser.add_argument(
        "--start",
        default=DEFAULT_START_NODE,
        help="Start node ID from the road graph",
    )
    parser.add_argument(
        "--goal",
        default=DEFAULT_GOAL_NODE,
        help="Goal node ID for single-delivery problems",
    )
    parser.add_argument(
        "--deliveries",
        default="",
        help="Comma-separated node IDs for multi-delivery problems",
    )
    parser.add_argument("--instance", help="Named case from data/instances.json")
    parser.add_argument(
        "--max-depth", type=int, default=None, help="Optional IDS depth cap"
    )
    parser.add_argument(
        "--show", action="store_true", help="Open an interactive map in the browser"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = read_command(argv)
    graph = ColombiaRoadGraph.from_json(args.graph)

    config = apply_instance(args)
    warn_about_combination(config)
    problem = build_problem(graph, config)
    search_fn = get_search_function(config.algorithm)
    heuristic_fn = get_heuristic_function(config)

    start_time = time.perf_counter()
    if config.algorithm in ASTAR_ALGORITHMS:
        actions = search_fn(problem, heuristic=heuristic_fn)
    elif config.algorithm in IDS_ALGORITHMS:
        actions = search_fn(problem, max_depth=config.max_depth)
    else:
        actions = search_fn(problem)
    elapsed = time.perf_counter() - start_time

    start_node = (
        problem.getStartState()[0]
        if config.problem == "multi"
        else problem.getStartState()
    )
    route = actions_to_route(start_node, actions)
    cost = problem.getCostOfActions(actions)
    deliveries = set(config.deliveries if config.problem == "multi" else [config.goal])

    print_summary(graph, config, route, cost, problem, elapsed)

    if config.show:
        html_path = show_route_map(
            graph,
            route=route,
            deliveries=deliveries,
            expanded=getattr(problem, "_expanded_nodes", set()),
            title=f"{config.algorithm} - {config.problem}",
        )
        print(f"Interactive map opened from {html_path}")


class RunConfig(argparse.Namespace):
    problem: str
    algorithm: str
    heuristic: str | None
    start: str
    goal: str
    deliveries: list[str]
    show: bool
    max_depth: int | None


def apply_instance(args: argparse.Namespace) -> RunConfig:
    config = RunConfig(**vars(args))
    if args.instance:
        instances = json.loads(INSTANCE_PATH.read_text(encoding="utf-8"))
        if args.instance not in instances:
            raise KeyError(
                f"Unknown instance {args.instance!r}. Available: {sorted(instances)}"
            )
        selected = instances[args.instance]
        for key, value in selected.items():
            setattr(config, key, value)
    if isinstance(config.deliveries, str):
        config.deliveries = [
            item.strip() for item in config.deliveries.split(",") if item.strip()
        ]
    return config


def canonical_algorithm(name: str) -> str:
    return ALGORITHM_ALIASES.get(name, name)


def warn_about_combination(config: RunConfig) -> None:
    algorithm = canonical_algorithm(config.algorithm)
    recommended = RECOMMENDED_ALGORITHMS[config.problem]
    if algorithm in recommended:
        return

    recommended_text = ", ".join(sorted(recommended))
    print(
        "Warning: "
        f"algorithm '{config.algorithm}' is not recommended for problem "
        f"'{config.problem}'. Recommended: {recommended_text}."
    )

    if config.problem == "single" and algorithm in {"dfs", "bfs", "ids"}:
        print("  This problem minimizes kilometers; use UCS or A* for optimal costs.")
    elif config.problem == "stops" and algorithm in {"ucs", "astar"}:
        print("  This problem uses unit edge costs; BFS or IDS better match the goal.")
    elif config.problem == "multi":
        print(
            "  Multi-delivery search grows quickly; A* with a multi-delivery "
            "heuristic is the intended option."
        )


def build_problem(graph: ColombiaRoadGraph, config: RunConfig) -> SearchProblem:
    if config.problem == "single":
        return SingleDeliveryProblem(graph, config.start, config.goal)
    if config.problem == "stops":
        return FewestStopsDeliveryProblem(graph, config.start, config.goal)
    if config.problem == "multi":
        if not config.deliveries:
            raise ValueError("--deliveries is required for --problem multi")
        return MultiDeliveryProblem(graph, config.start, config.deliveries)
    raise ValueError(f"Unsupported problem: {config.problem}")


def get_search_function(name: str) -> Callable:
    if not hasattr(search, name):
        raise AttributeError(f"{name!r} is not a function in algorithms/search.py")
    return getattr(search, name)


def get_heuristic_function(config: RunConfig) -> Callable:
    if config.heuristic:
        name = config.heuristic
    elif config.problem == "multi":
        name = "multiDeliveryHeuristic"
    else:
        name = "straightLineHeuristic"
    if not hasattr(heuristics, name):
        raise AttributeError(f"{name!r} is not a function in algorithms/heuristics.py")
    return getattr(heuristics, name)


def print_summary(
    graph: ColombiaRoadGraph,
    config: RunConfig,
    route: list[str],
    cost: float,
    problem: SearchProblem,
    elapsed: float,
) -> None:
    route_preview = _route_preview(route)
    print("=" * 72)
    print("PANINI LOGISTICS SEARCH RESULT")
    print("=" * 72)
    print(f"Problem:    {config.problem}")
    print(f"Algorithm:  {config.algorithm}")
    default_heuristic = "default" if config.algorithm in ASTAR_ALGORITHMS else "n/a"
    print(f"Heuristic:  {config.heuristic or default_heuristic}")
    print(f"Cost:       {cost:.2f}")
    print(f"Actions:    {max(0, len(route) - 1)}")
    print(f"Expanded:   {getattr(problem, '_expanded', 0)}")
    print(f"Frontier:   {getattr(problem, '_max_frontier_size', 0)}")
    print(f"Time:       {elapsed:.4f} seconds")
    if hasattr(problem, "_ids_depth_found"):
        print(f"IDS depth:  {problem._ids_depth_found}")
    print("Route preview:")
    for node_id in route_preview:
        if node_id == "...":
            print("  - ...")
            continue
        print(f"  - {graph.node_label(node_id)}")


def _route_preview(route: list[str], limit: int = 24) -> list[str]:
    if len(route) <= limit:
        return route
    head = route[: limit // 2]
    tail = route[-(limit // 2) :]
    return [*head, "...", *tail]


if __name__ == "__main__":
    main()
