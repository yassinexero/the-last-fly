"""Simulation engine executing turn-by-turn drone movements."""

from typing import Dict, List, Optional, Set
from zone import ZoneType
from drone import Drone
from graph import Graph
from pathfinder import Pathfinder


class SimulationResult:
    """Stores the outcome of a completed simulation run."""

    def __init__(
        self,
        turn_lines: List[str],
        total_turns: int,
        capacity_lines: Optional[List[str]] = None,
    ) -> None:
        """Initialize SimulationResult.

        Args:
            turn_lines: Output lines formatted per simulation turn.
            total_turns: Total turn count required to deliver all drones.
            capacity_lines: Optional capacity usage breakdown lines per turn.
        """
        self.turn_lines: List[str] = turn_lines
        self.total_turns: int = total_turns
        self.capacity_lines: List[str] = capacity_lines or []

    def format_output(self, show_capacity: bool = False) -> str:
        """Format simulation output as standard multi-line string.

        Args:
            show_capacity: If True, include capacity info lines.

        Returns:
            str: Multi-line simulation log matching specification.
        """
        if not show_capacity or not self.capacity_lines:
            return "\n".join(self.turn_lines)

        output: List[str] = []
        for line, cap in zip(self.turn_lines, self.capacity_lines):
            output.append(line)
            if cap:
                output.append(f"  {cap}")
        return "\n".join(output)


class SimulationEngine:
    """Engine executing turn-by-turn drone movement simulation."""

    def __init__(self, graph: Graph) -> None:
        """Initialize SimulationEngine with graph network.

        Args:
            graph: Validated Graph instance.
        """
        assert graph.start_zone is not None
        self.graph: Graph = graph
        self.drones: List[Drone] = [
            Drone(i + 1, graph.start_zone)
            for i in range(graph.nb_drones)
        ]
        self.pathfinder: Pathfinder = Pathfinder(graph)

    def run(self) -> SimulationResult:
        """Run simulation until all drones reach the end zone.

        Returns:
            SimulationResult: Container holding turn output lines and total turns.

        Raises:
            RuntimeError: If no valid paths exist to route drones.
        """
        assert self.graph.start_zone is not None
        assert self.graph.end_zone is not None

        paths = self.pathfinder.find_multiple_paths()
        if not paths:
            raise RuntimeError("No valid path exists from start_hub to end_hub")

        drone_paths = self.pathfinder.allocate_drones_to_paths(self.drones, paths)
        drone_indices: Dict[int, int] = {d.drone_id: 0 for d in self.drones}

        # Track zone & connection occupancies
        zone_occupancy: Dict[str, Set[int]] = {z_name: set() for z_name in self.graph.zones}
        start_name = self.graph.start_zone.name
        for d in self.drones:
            zone_occupancy[start_name].add(d.drone_id)

        conn_occupancy: Dict[str, Set[int]] = {c.name: set() for c in self.graph.connections}

        turn_lines: List[str] = []
        capacity_lines: List[str] = []
        turn_count = 0

        # Safety loop cap to prevent infinite loops on deadlocks
        max_turns_limit = 10000

        while not all(d.is_delivered for d in self.drones) and turn_count < max_turns_limit:
            turn_count += 1
            turn_movements: List[str] = []

            # 1. Track which drones are exiting which zones in this turn
            exiting_from_zone: Dict[str, Set[int]] = {z_name: set() for z_name in self.graph.zones}
            entering_to_zone: Dict[str, Set[int]] = {z_name: set() for z_name in self.graph.zones}

            # Phase A: Complete turn 2 for in-transit restricted zone drones
            for d in self.drones:
                if d.is_delivered or not d.is_in_transit:
                    continue

                d.transit_turns_remaining -= 1
                if d.transit_turns_remaining == 0:
                    # Drone arrives at target restricted zone
                    target = d.target_zone
                    conn = d.connection_in_transit
                    assert target is not None
                    assert conn is not None

                    conn_occupancy[conn.name].remove(d.drone_id)
                    zone_occupancy[target.name].add(d.drone_id)
                    entering_to_zone[target.name].add(d.drone_id)

                    d.current_zone = target
                    d.connection_in_transit = None
                    d.target_zone = None

                    if target == self.graph.end_zone:
                        d.is_delivered = True

                    drone_indices[d.drone_id] += 1
                    turn_movements.append(f"{d.name}-{target.name}")

            # Phase B: Advance stationary drones
            for d in self.drones:
                if d.is_delivered or d.is_in_transit:
                    continue

                path = drone_paths[d.drone_id]
                curr_idx = drone_indices[d.drone_id]

                if curr_idx >= len(path.nodes) - 1:
                    continue

                curr_zone = path.nodes[curr_idx]
                next_zone = path.nodes[curr_idx + 1]
                conn = path.connections[curr_idx]

                # Check connection capacity limit
                if (
                    len(conn_occupancy[conn.name]) >= conn.max_link_capacity
                    and conn.max_link_capacity < float("inf")
                ):
                    continue

                # Check next zone capacity limit
                # Drones exiting next_zone free up capacity this turn
                curr_next_occ = len(zone_occupancy[next_zone.name])
                exiting_next = len(exiting_from_zone[next_zone.name])
                entering_next = len(entering_to_zone[next_zone.name])

                effective_next_occ = curr_next_occ - exiting_next + entering_next

                if effective_next_occ >= next_zone.capacity:
                    continue

                # Move is valid!
                exiting_from_zone[curr_zone.name].add(d.drone_id)
                zone_occupancy[curr_zone.name].remove(d.drone_id)

                if next_zone.zone_type == ZoneType.RESTRICTED:
                    # Multi-turn move (cost 2 turns)
                    d.connection_in_transit = conn
                    d.target_zone = next_zone
                    d.current_zone = None
                    d.transit_turns_remaining = 1
                    conn_occupancy[conn.name].add(d.drone_id)
                    turn_movements.append(f"{d.name}-{conn.name}")
                else:
                    # Single turn move (cost 1 turn)
                    zone_occupancy[next_zone.name].add(d.drone_id)
                    entering_to_zone[next_zone.name].add(d.drone_id)
                    d.current_zone = next_zone
                    if next_zone == self.graph.end_zone:
                        d.is_delivered = True
                    drone_indices[d.drone_id] += 1
                    turn_movements.append(f"{d.name}-{next_zone.name}")

            if turn_movements:
                turn_lines.append(" ".join(turn_movements))
                cap_parts: List[str] = []
                for z_name, z_obj in self.graph.zones.items():
                    if not z_obj.is_start and not z_obj.is_end:
                        occ = len(zone_occupancy[z_name])
                        if occ > 0 or z_obj.max_drones > 1:
                            cap_parts.append(
                                f"Zone {z_name}: {occ}/{z_obj.max_drones} drones"
                            )
                for c_obj in self.graph.connections:
                    occ = len(conn_occupancy[c_obj.name])
                    if occ > 0 or c_obj.max_link_capacity > 1:
                        c_cap = c_obj.max_link_capacity
                        cap_parts.append(
                            f"Connection {c_obj.name}: {occ}/{c_cap} capacity used"
                        )
                capacity_lines.append(", ".join(cap_parts))

        return SimulationResult(turn_lines, turn_count, capacity_lines)
