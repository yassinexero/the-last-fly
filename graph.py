"""Graph model managing the network topology, zones, and connections."""

from typing import Dict, List, Optional, Tuple
from zone import Zone
from connection import Connection


class Graph:
    """Represents the complete network graph of zones and connections."""

    def __init__(self, nb_drones: int = 0) -> None:
        """Initialize a Graph instance.

        Args:
            nb_drones: Total number of drones to route.
        """
        self.nb_drones: int = nb_drones
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.adj: Dict[Zone, List[Tuple[Zone, Connection]]] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone node to the graph.

        Args:
            zone: Zone object to add.

        Raises:
            ValueError: If a zone with the same name already exists.
        """
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name detected: {zone.name}")
        self.zones[zone.name] = zone
        self.adj[zone] = []

        if zone.is_start:
            if self.start_zone is not None:
                raise ValueError("Multiple start_hub zones defined in map")
            self.start_zone = zone
        if zone.is_end:
            if self.end_zone is not None:
                raise ValueError("Multiple end_hub zones defined in map")
            self.end_zone = zone

    def add_connection(self, connection: Connection) -> None:
        """Add a connection edge between two zones.

        Args:
            connection: Connection object to add.

        Raises:
            ValueError: If connection connects unknown zones or is duplicate.
        """
        z1 = connection.zone1
        z2 = connection.zone2
        if z1.name not in self.zones or z2.name not in self.zones:
            raise ValueError(f"Connection references unknown zone: {connection.name}")

        for existing in self.connections:
            if existing.connects(z1, z2):
                raise ValueError(f"Duplicate connection detected: {connection.name}")

        self.connections.append(connection)
        self.adj[z1].append((z2, connection))
        self.adj[z2].append((z1, connection))

    def get_neighbors(self, zone: Zone) -> List[Tuple[Zone, Connection]]:
        """Get all adjacent zones and connecting edges for a given zone.

        Args:
            zone: Source zone.

        Returns:
            List[Tuple[Zone, Connection]]: List of (neighbor_zone, connection) tuples.
        """
        return self.adj.get(zone, [])

    def get_connection(self, zone_a: Zone, zone_b: Zone) -> Optional[Connection]:
        """Find the connection linking two zones if one exists.

        Args:
            zone_a: First zone.
            zone_b: Second zone.

        Returns:
            Optional[Connection]: Connection object or None if not connected.
        """
        for connection in self.adj.get(zone_a, []):
            if connection[0] == zone_b:
                return connection[1]
        return None

    def validate(self) -> None:
        """Validate structural integrity of the graph.

        Raises:
            ValueError: If start/end zones missing or invalid number of drones.
        """
        if self.nb_drones <= 0:
            raise ValueError(f"Invalid number of drones: {self.nb_drones}")
        if self.start_zone is None:
            raise ValueError("Missing start_hub in graph definition")
        if self.end_zone is None:
            raise ValueError("Missing end_hub in graph definition")
        if self.start_zone == self.end_zone:
            raise ValueError("start_hub and end_hub cannot be the same zone")

    def __repr__(self) -> str:
        """Return string representation of Graph.

        Returns:
            str: Graph summary.
        """
        start = self.start_zone.name if self.start_zone else "None"
        end = self.end_zone.name if self.end_zone else "None"
        return (
            f"Graph(drones={self.nb_drones}, zones={len(self.zones)}, "
            f"connections={len(self.connections)}, start={start}, end={end})"
        )
