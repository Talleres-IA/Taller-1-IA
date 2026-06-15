"""Generic search algorithms for the Panini logistics workshop."""

from __future__ import annotations

from typing import Any

from algorithms import utils
from algorithms.heuristics import nullHeuristic
from algorithms.problems import SearchProblem, State


def _remember_frontier(problem: SearchProblem, frontier: Any) -> None:
    """Record the largest frontier size reached during a search.

    Call this helper after each push/pop cycle in DFS, BFS, UCS and A*.
    It updates `problem._max_frontier_size`, which `main.py` prints in the
    execution summary for your experimental analysis.

    You do not need to count expanded nodes here: `getSuccessors` in
    `algorithms/problems.py` already increments `problem._expanded`.
    """

    if hasattr(frontier, "_items"):
        size = len(frontier._items)
    elif hasattr(frontier, "heap"):
        size = len(frontier.heap)
    else:
        size = 0
    current = getattr(problem, "_max_frontier_size", 0)
    problem._max_frontier_size = max(current, size)


def depthFirstSearch(problem: SearchProblem) -> list[str]:
    """Search the deepest nodes in the search tree first.

    Tips:
    - Return the action list accumulated along the path, not the node sequence.
    - Call `_remember_frontier` whenever the frontier changes.
    - Expanded nodes are counted automatically inside `getSuccessors`.
    """

   ### YOUR CODE HERE ###
    frontier = utils.Stack()
    frontier.push((problem.getStartState(), []))
    visited = set()
 
    while not frontier.isEmpty():
        _remember_frontier(problem, frontier)
        state, actions = frontier.pop()
 
        if state in visited:
            continue
        visited.add(state)
 
        if problem.isGoalState(state):
            return actions
 
        for successor, action, _ in problem.getSuccessors(state):
            if successor not in visited:
                frontier.push((successor, actions + [action]))
        _remember_frontier(problem, frontier)
 
    return []


def breadthFirstSearch(problem: SearchProblem) -> list[str]:
    """Search the shallowest nodes in the search tree first.

    Tips:
    - Mark a state as visited when you enqueue it, not when you dequeue it.
    - Test for the goal immediately after dequeuing a state.
    """

    ### YOUR CODE HERE ###
    frontier = utils.Queue()
    start = problem.getStartState()
    frontier.push((start, []))
    visited = {start}  
 
    while not frontier.isEmpty():
        _remember_frontier(problem, frontier)
        state, actions = frontier.pop()
 
        if problem.isGoalState(state):
            return actions
 
        for successor, action, _ in problem.getSuccessors(state):
            if successor not in visited:
                visited.add(successor)
                frontier.push((successor, actions + [action]))
        _remember_frontier(problem, frontier)
 
    return []


def uniformCostSearch(problem: SearchProblem) -> list[str]:
    """Search the node with the lowest path cost first.

    Tips:
    - Use path cost `g(n)` as the priority queue key.
    - Ignore stale frontier entries whose stored `g` is worse than the best known.
    """

    ### YOUR CODE HERE ###
    frontier = utils.PriorityQueue()
    start = problem.getStartState()
    frontier.push((start, [], 0.0), 0.0)
    best_cost: dict = {start: 0.0}
 
    while not frontier.isEmpty():
        _remember_frontier(problem, frontier)
        state, actions, cost = frontier.pop()
 
        if cost > best_cost.get(state, float("inf")):
            continue
 
        if problem.isGoalState(state):
            return actions
 
        for successor, action, step_cost in problem.getSuccessors(state):
            new_cost = cost + step_cost
            if new_cost < best_cost.get(successor, float("inf")):
                best_cost[successor] = new_cost
                frontier.push((successor, actions + [action], new_cost), new_cost)
        _remember_frontier(problem, frontier)
 
    return [] 


def aStarSearch(problem: SearchProblem, heuristic=nullHeuristic) -> list[str]:
    """Search the node with the lowest `g(n) + h(n)` first.

    Tips:
    - Push `g(n) + h(n)` to the frontier, but compare re-expansions against `g(n)`.
    - The UCS pattern still applies once a state is popped from the queue.
    """

    ### YOUR CODE HERE ###
    frontier = utils.PriorityQueue()
    start = problem.getStartState()
    frontier.push((start, [], 0.0), 0.0)
    best_cost: dict = {start: 0.0}

    while not frontier.isEmpty():
        _remember_frontier(problem, frontier)
        state, actions, cost = frontier.pop()

        if cost > best_cost.get(state, float("inf")):
            continue

        if problem.isGoalState(state):
            return actions

        for successor, action, step_cost in problem.getSuccessors(state):
            new_cost = cost + step_cost
            if new_cost < best_cost.get(successor, float("inf")):
                best_cost[successor] = new_cost
                frontier.push((successor, actions + [action], new_cost), new_cost + heuristic(successor, problem))
        _remember_frontier(problem, frontier)

    return []


def depthLimitedSearch(problem: SearchProblem, limit: int) -> list[str] | None:
    """Return a solution with at most `limit` actions, or None if none is found.

    Tips:
    - Depth counts actions taken from the start, not recursive calls made.
    - Keep a set of nodes on the current path to avoid revisiting them in one branch.
    """
    start = problem.getStartState()

    def recursive_dls(state: State, actions: list[str], depth: int, path: set[State]):
        
        current = getattr(problem, "_max_frontier_size", 0)
        problem._max_frontier_size = max(current, len(path))


        if problem.isGoalState(state):
            return actions

        if depth == limit:
            return None

        for successor, action, _step_cost in problem.getSuccessors(state):
            if successor not in path:
                path.add(successor)

                result = recursive_dls(
                    successor,
                    actions + [action],
                    depth + 1,
                    path
                )

                if result is not None:
                    return result

                path.remove(successor)

        return None
    
    return recursive_dls(start, [], 0, {start})
    


def iterativeDeepeningSearch(
    problem: SearchProblem, max_depth: int | None = None
) -> list[str]:
    """Run depth-limited DFS with increasing depth limits.

    Tips:
    - Increase the limit one step at a time and delegate each attempt to DLS.
    - Save the successful depth in `problem._ids_depth_found` before returning.
    """

    if max_depth is None:
        max_depth = 100000 # se pone siemrpe un número muy grande

    for depth in range(max_depth + 1):
        # print("Probando profundidad:", depth) Me estaba falladno entonces puse esto
        result = depthLimitedSearch(problem, depth)

        if result is not None:
            problem._ids_depth_found = depth
            return result

    return []

    """if max_depth is None:
        max_depth = 40

    for depth in range(max_depth + 1):
        print("Probando profundidad:", depth)
    result = depthLimitedSearch(problem, depth)

    if result is not None:
        problem._ids_depth_found = depth
        return result
    #Usé esto para proba si servía
    """


# Abbreviations used by the CLI and the statement.
dfs = depthFirstSearch
bfs = breadthFirstSearch
ucs = uniformCostSearch
astar = aStarSearch
ids = iterativeDeepeningSearch

# se ven los cambios ??
# ahora ??