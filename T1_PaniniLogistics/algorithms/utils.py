"""Small data structures used by the search algorithms."""

from __future__ import annotations

import heapq
import inspect
import sys
from collections import deque
from typing import Generic, TypeVar

T = TypeVar("T")


class Stack(Generic[T]):
    """A last-in, first-out container."""

    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def isEmpty(self) -> bool:
        return not self._items


class Queue(Generic[T]):
    """A first-in, first-out container."""

    def __init__(self) -> None:
        self._items: deque[T] = deque()

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.popleft()

    def isEmpty(self) -> bool:
        return not self._items


class PriorityQueue(Generic[T]):
    """Min-priority queue with stable tie-breaking."""

    def __init__(self) -> None:
        self.heap: list[tuple[float, int, T]] = []
        self.count = 0

    def push(self, item: T, priority: float) -> None:
        heapq.heappush(self.heap, (priority, self.count, item))
        self.count += 1

    def pop(self) -> T:
        _, _, item = heapq.heappop(self.heap)
        return item

    def isEmpty(self) -> bool:
        return not self.heap


def raiseNotDefined() -> None:
    file_name = inspect.stack()[1][1]
    line = inspect.stack()[1][2]
    method = inspect.stack()[1][3]
    print(f"*** Method not implemented: {method} at line {line} of {file_name}")
    sys.exit(1)
