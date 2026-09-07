"""Pathfinding engine implementing BFS-based multi-path routing."""

import heapq
from typing import Dict, List, Optional, Set, Tuple
from zone import Zone, ZoneType
from connection import Connection
from drone import Drone
from graph import Graph


class Path:
    """Represents a path from start_hub to end_hub in the graph."""

    def __init__(self, nodes: List[Zone], connections: List[Connection]) -> None:
        """Initialize a Path instance.

        Args:
            nodes: Ordered list of zones from start to end.
            connections: Ordered list of connections linking the nodes.
        """
        self.nodes: List[Zone] = nodes
        self.connections: List[Connection] = connections

    @property
    def total_cost(self) -> int:
        """Calculate total turn cost of traversing the path.

        Returns:
            int: Sum of movement costs for destination zones along path.
        """
        if len(self.nodes) <= 1:
            return 0
        cost = 0
        # Exclude start node (drones start inside start node)
        for node in self.nodes[1:]:
            cost += node.zone_type.movement_cost
        return cost

    @property
    def priority_score(self) -> float:
        """Calculate path priority score (lower is better).

        Priority zones lower the score to favor priority paths.

        Returns:
            float: Weighted path score.
        """
        score = 0.0
        for node in self.nodes[1:]:
            if node.zone_type == ZoneType.PRIORITY:
                score += 0.9  # Preferred over standard cost of 1.0
            elif node.zone_type == ZoneType.RESTRICTED:
                score += 2.0
            else:
                score += 1.0
        return score

    def __repr__(self) -> str:
        """Return string representation of Path.

        Returns:
            str: Path description.
        """
        names = " -> ".join(n.name for n in self.nodes)
        return f"Path(cost={self.total_cost}, route=[{names}])"


class Pathfinder:
    """Engine for finding and allocating paths using BFS algorithms."""

    def __init__(self, graph: Graph) -> None:
        """Initialize Pathfinder with target graph.

        Args:
            graph: Graph instance containing network topology.
        """
        self.graph: Graph = graph

    def find_shortest_path_bfs(
        self,
        ignored_edges: Optional[Set[str]] = None,
        ignored_nodes: Optional[Set[str]] = None,
    ) -> Optional[Path]:
        """Find single shortest path using BFS with cost weighting.

        Args:
            ignored_edges: Connection names to exclude from search.
            ignored_nodes: Zone names to exclude from search.

        Returns:
            Optional[Path]: Discovered Path object or None if no path exists.
        """
        if self.graph.start_zone is None or self.graph.end_zone is None:
            return None

        ignored_e = ignored_edges if ignored_edges else set()
        ignored_n = ignored_nodes if ignored_nodes else set()

        start = self.graph.start_zone
        end = self.graph.end_zone

        # Priority Queue for BFS: (score, turn_cost, current_name, nodes, conns)
        queue: List[Tuple[float, int, str, List[Zone], List[Connection]]] = []
        heapq.heappush(queue, (0.0, 0, start.name, [start], []))

        visited: Dict[str, float] = {start.name: 0.0}

        while queue:
            score, turn_cost, current_name, nodes, conns = heapq.heappop(queue)
            current_zone = self.graph.zones[current_name]

            if current_name == end.name:
                return Path(nodes, conns)

            if score > visited.get(current_name, float("inf")):
                continue

            for neighbor, connection in self.graph.get_neighbors(current_zone):
                if neighbor.name in ignored_n or connection.name in ignored_e:
                    continue
                if not neighbor.is_passable():
                    continue

                step_cost = neighbor.zone_type.movement_cost
                step_score = 0.9 if neighbor.zone_type == ZoneType.PRIORITY else float(step_cost)

                new_score = score + step_score
                new_turn_cost = turn_cost + step_cost

                if new_score < visited.get(neighbor.name, float("inf")):
                    visited[neighbor.name] = new_score
                    heapq.heappush(
                        queue,
                        (
                            new_score,
                            new_turn_cost,
                            neighbor.name,
                            nodes + [neighbor],
                            conns + [connection],
                        ),
                    )

        return None

    def find_multiple_paths(self, max_paths: int = 5) -> List[Path]:
        """Discover multiple distinct or edge-disjoint paths using BFS iterations.

        Args:
            max_paths: Maximum number of paths to find.

        Returns:
            List[Path]: List of available paths sorted by cost and priority.
        """
        paths: List[Path] = []
        ignored_edges: Set[str] = set()

        # Find primary shortest path
        primary = self.find_shortest_path_bfs()
        if primary:
            paths.append(primary)

        # Iteratively search for alternate paths by temporarily removing bottleneck edges
        for _ in range(max_paths - 1):
            if not paths:
                break
            # Ignore edges of the last found path except connections at start/end if shared
            last_path = paths[-1]
            for conn in last_path.connections:
                ignored_edges.add(conn.name)

            alt_path = self.find_shortest_path_bfs(ignored_edges=ignored_edges)
            if alt_path:
                paths.append(alt_path)
            else:
                break

        # Sort paths by priority score
        paths.sort(key=lambda p: p.priority_score)
        return paths

    def allocate_drones_to_paths(
        self, drones: List[Drone], paths: List[Path]
    ) -> Dict[int, Path]:
        """Equitably assign drones to paths to minimize total simulation turns.

        Args:
            drones: List of Drone objects to route.
            paths: Available paths.

        Returns:
            Dict[int, Path]: Mapping from drone_id to assigned Path.
        """
        allocation: Dict[int, Path] = {}
        if not paths or not drones:
            return allocation

        # Track effective total turns required for each path as drones are added
        path_loads: List[int] = [p.total_cost for p in paths]

        for drone in drones:
            # Pick path with lowest (path_load + turn delay)
            best_idx = 0
            best_val = float("inf")

            for idx, path in enumerate(paths):
                current_val = path_loads[idx]
                if current_val < best_val:
                    best_val = current_val
                    best_idx = idx

            allocation[drone.drone_id] = paths[best_idx]
            # Increment path load assuming sequential dispatch
            path_loads[best_idx] += 1

        return allocation
