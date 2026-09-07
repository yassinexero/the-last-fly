"""Connection model representing a bidirectional edge between two zones."""

from zone import Zone


class Connection:
    """Represents a connection (edge) between two zones in the graph."""

    def __init__(self, zone1: Zone, zone2: Zone, max_link_capacity: int = 1) -> None:
        """Initialize a Connection instance.

        Args:
            zone1: First endpoint Zone.
            zone2: Second endpoint Zone.
            max_link_capacity: Maximum simultaneous drones traversing edge.
        """
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.max_link_capacity: int = max_link_capacity

    @property
    def name(self) -> str:
        """Get canonical formatted connection name identifier.

        Returns:
            str: Canonical connection string formatted as 'zone1-zone2'.
        """
        names = sorted([self.zone1.name, self.zone2.name])
        return f"{names[0]}-{names[1]}"

    def get_other_zone(self, zone: Zone) -> Zone:
        """Get the opposite endpoint zone given one endpoint zone.

        Args:
            zone: One of the connection's endpoint zones.

        Returns:
            Zone: The opposite endpoint zone.

        Raises:
            ValueError: If the provided zone is not part of this connection.
        """
        if zone == self.zone1:
            return self.zone2
        elif zone == self.zone2:
            return self.zone1
        raise ValueError(f"Zone {zone.name} is not part of connection {self.name}")

    def connects(self, zone_a: Zone, zone_b: Zone) -> bool:
        """Check if connection connects the two specified zones.

        Args:
            zone_a: First zone to check.
            zone_b: Second zone to check.

        Returns:
            bool: True if connection links zone_a and zone_b.
        """
        return (self.zone1 == zone_a and self.zone2 == zone_b) or (
            self.zone1 == zone_b and self.zone2 == zone_a
        )

    def __repr__(self) -> str:
        """Return string representation of Connection.

        Returns:
            str: Connection description.
        """
        return f"Connection({self.name}, capacity={self.max_link_capacity})"
