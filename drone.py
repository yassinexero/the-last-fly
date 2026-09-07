"""Drone model representing a single drone entity in simulation."""

from typing import Optional
from zone import Zone
from connection import Connection


class Drone:
    """Represents an individual drone moving through the graph network."""

    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        """Initialize a Drone instance.

        Args:
            drone_id: Unique integer identifier for the drone (1-indexed).
            start_zone: Starting hub zone.
        """
        self.drone_id: int = drone_id
        self.current_zone: Optional[Zone] = start_zone
        self.target_zone: Optional[Zone] = None
        self.connection_in_transit: Optional[Connection] = None
        self.transit_turns_remaining: int = 0
        self.is_delivered: bool = False

    @property
    def name(self) -> str:
        """Get formatted drone identifier string (e.g., 'D1').

        Returns:
            str: Drone string label.
        """
        return f"D{self.drone_id}"

    @property
    def is_in_transit(self) -> bool:
        """Check if drone is currently traversing a multi-turn connection.

        Returns:
            bool: True if drone is mid-transit on a connection.
        """
        return self.transit_turns_remaining > 0

    def __repr__(self) -> str:
        """Return string representation of Drone.

        Returns:
            str: Drone description.
        """
        location = self.current_zone.name if self.current_zone else "In-Transit"
        return f"Drone({self.name}, location={location}, delivered={self.is_delivered})"
