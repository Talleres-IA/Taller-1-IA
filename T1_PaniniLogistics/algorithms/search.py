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
    """def dfs(graph, start):

    visited = set()
    stack = [start]

    while stack:

        vertex = stack.pop()

        if vertex not in visited:

            print(vertex)
            visited.add(vertex)

            for neighbor in graph[vertex]:
                stack.append(neighbor)
    
    Y el BFS es:
    
    def bfs(graph, start):

    visited = set()
    queue = deque([start])

    while queue:

        vertex = queue.popleft()

        if vertex not in visited:

            print(vertex)
            visited.add(vertex)

            for neighbor in graph[vertex]:
                queue.append(neighbor)
    
    """
   # La versión inicial de BFS y DFS se tomo como guia la implementacion de esto en el curso de estructuras de datos, pero con algunos errores que se corrigieron con prompts a la IA (Claude):
   # 1. "cómo evito expandir nodos ya visitados en DFS?"
   #    corrección: agregar un conjunto de visitados y verificar antes de expandir.
   # 2. "cuándo verifico si el nodo es meta en DFS?"
   #    corrección: verificar meta inmediatamente después de sacar el nodo de la frontera.
   
    
   
    frrontera = utils.Stack()
    frrontera.push((problem.getStartState(), []))
    visitados = set()
 
    while not frrontera.isEmpty():
        _remember_frontier(problem, frrontera)
        state, actions = frrontera.pop()
 
        if state in visitados:
            continue
        visitados.add(state)
 
        if problem.isGoalState(state):
            return actions
 
        for successor, action, _ in problem.getSuccessors(state):
            if successor not in visitados:
                frrontera.push((successor, actions + [action]))
        _remember_frontier(problem, frrontera)
 
    return []


def breadthFirstSearch(problem: SearchProblem) -> list[str]:
    """Search the shallowest nodes in the search tree first.

    Tips:
    - Mark a state as visited when you enqueue it, not when you dequeue it.
    - Test for the goal immediately after dequeuing a state.
    """

    ### YOUR CODE HERE ###
    frrontera = utils.Queue()
    inicio = problem.getStartState()
    frrontera.push((inicio, []))
    visitados = {inicio}  
 
    while not frrontera.isEmpty():
        _remember_frontier(problem, frrontera)
        state, actions = frrontera.pop()
 
        if problem.isGoalState(state):
            return actions
 
        for successor, action, _ in problem.getSuccessors(state):
            if successor not in visitados:
                visitados.add(successor)
                frrontera.push((successor, actions + [action]))
        _remember_frontier(problem, frrontera)
 
    return []


def uniformCostSearch(problem: SearchProblem) -> list[str]:
    """Search the node with the lowest path cost first.

    Tips:
    - Use path cost `g(n)` as the priority queue key.
    - Ignore stale frontier entries whose stored `g` is worse than the best known.
    """

    ### YOUR CODE HERE ###
    """ Version inicial y con las cosas que estaban mal corregidas con prompts a la IA (Claude):
    El pront fue: "cómo evito expandir nodos con peor g(n) que el mejor conocido? y Adicionalmente comprender que estaba mal dentro del codigo inicial y corregirlo
        frontier = utils.PriorityQueue()
    start = problem.getStartState()

    frontier.push((start, [], 0.0), 0.0)

    best_cost: dict = {start: 0.0}
    visited = set()

    while not frontier.isEmpty():

        _remember_frontier(problem, frontier)

        state, actions, cost = frontier.pop()

        # ERROR SUTIL:
        # esto puede bloquear caminos más baratos
        # que aparezcan después
        if state in visited:
            continue

        visited.add(state)

        # ERROR:
        # revisa goal después de marcar visited
        # y antes de validar stale entries
        if problem.isGoalState(state):
            return actions

        # ERROR IMPORTANTE:
        # comparación al revés
        # ignora caminos buenos y deja malos
        if cost < best_cost.get(state, float("inf")):
            continue

        for successor, action, step_cost in problem.getSuccessors(state):

            # ERROR:
            # accidentalmente multiplicando
            # en vez de sumar
            new_cost = cost * step_cost

            # ERROR:
            # prioridad incorrecta
            # debería usar new_cost
            priority = len(actions)

            if successor not in visited:

                best_cost[successor] = new_cost

                frontier.push(
                    (successor, actions + [action], new_cost),
                    priority
                )

        _remember_frontier(problem, frontier)

        return []   """
    
    frontera = utils.PriorityQueue()
    inicio = problem.getStartState()
    frontera.push((inicio, [], 0.0), 0.0)
    m_costo: dict = {inicio: 0.0}
 
    while not frontera.isEmpty():
        _remember_frontier(problem, frontera)
        state, actions, cost = frontera.pop()
 
        if cost > m_costo.get(state, float("inf")):
            continue
 
        if problem.isGoalState(state):
            return actions
 
        for successor, action, step_cost in problem.getSuccessors(state):
            new_cost = cost + step_cost
            if new_cost < m_costo.get(successor, float("inf")):
                m_costo[successor] = new_cost
                frontera.push((successor, actions + [action], new_cost), new_cost)
        _remember_frontier(problem, frontera)
 
    return [] 


def aStarSearch(problem: SearchProblem, heuristic=nullHeuristic) -> list[str]:
    """Search the node with the lowest `g(n) + h(n)` first.

    Tips:
    - Push `g(n) + h(n)` to the frontier, but compare re-expansions against `g(n)`.
    - The UCS pattern still applies once a state is popped from the queue.
    """

    ### YOUR CODE HERE ###
    # MI VERSIÓN INICIAL
    # def aStarSearch(problem: SearchProblem, heuristic=nullHeuristic) -> list[str]:
    #     visitados = set()
    #     estadoi = problem.getStartState()
    #     colapri = utils.PriorityQueue()
    #     colapri.push((estadoi, []), 0, 0)   # ACÁ había un error ya que push recibe 2 args, no 3
    #     while not colapri.isEmpty():
    #         _remember_frontier(problem, colapri)
    #         estado, accion, costo = colapri.pop()  
    #         if estado in visitados():              # visitados no es una funcion 
    #             continue
    #         if problem.isGoalState(estado):
    #             return estado                      # debía retornar camino no el estado
    #             visitados.add(estado)             
    #         for s, g, c in problem.getSuccessors(estado):  
    #             nuevog = g + c
    #             nuevof = nuevog + heuristic(sucesor, problem)  
    #             return camino + [accion]  
    # PROMPTS USADOS CON IA (Claude):
    #
    # 1. "qué va en la prioridad del push inicial si g=0?"
    #    corrección: la prioridad es f = g + h, el item debe incluir g acumulado.
    #    push((estadoi, 0, []), hinicial)
    #
    # 2. "cuándo marco un nodo como visitado y cómo verifico si es meta?"
    #    corrección: visitados sin paréntesis; isGoalState() para verificar meta;
    #    retornar camino (no estado); visitados.add() va después del chequeo.
    #
    # 3. "cómo evito pisar g acumulado en el for y qué pusheo al final?"
    #    corrección: renombrar variables del for a (sucesor, accion, costo_paso);
    #      nuevo_g = g + costo_paso; push item con camino (no c) + [accion].

    visitados = set()
    estadoi = problem.getStartState()
    colapri = utils.PriorityQueue()
    hinicial = heuristic(estadoi, problem)
    colapri.push((estadoi, 0, []),hinicial)
    while not colapri.isEmpty():
        _remember_frontier(problem, colapri)
        estado, g, camino = colapri.pop()
        if estado in visitados:
            continue
        if problem.isGoalState(estado):
            return camino #es el camino acumulado
        visitados.add(estado)
        for s, accion, c in problem.getSuccessors(estado):
            nuevog = g + c
            nuevof = nuevog + heuristic(s, problem)
            colapri.push((s, nuevog, camino + [accion]), nuevof)
    
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

