"""Zone model representing a node in the network graph."""

from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """Supported zone types in the routing network."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def movement_cost(self) -> int:
        """Get turn cost associated with destination zone type.

        Returns:
            int: Movement cost in simulation turns.
        """
        if self == ZoneType.RESTRICTED:
            return 2
        return 1


class Zone:
    """Represents a zone (node) in the routing graph."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[str] = None,
        max_drones: int = 1,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        """Initialize a Zone instance.

        Args:
            name: Unique name identifier of the zone.
            x: X-coordinate integer position.
            y: Y-coordinate integer position.
            zone_type: Type of zone governing movement rules.
            color: Optional display color string.
            max_drones: Max drone capacity (ignored if start or end).
            is_start: True if this is the start hub.
            is_end: True if this is the end hub.
        """
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.is_start: bool = is_start
        self.is_end: bool = is_end

    @property
    def capacity(self) -> float:
        """Get effective capacity limit of the zone.

        Returns:
            float: Capacity limit (infinity for start/end, max_drones).
        """
        if self.is_start or self.is_end:
            return float("inf")
        return float(self.max_drones)

    def is_passable(self) -> bool:
        """Check if drones are allowed to enter this zone.

        Returns:
            bool: True if zone is not blocked.
        """
        return self.zone_type != ZoneType.BLOCKED

    def __repr__(self) -> str:
        """Return string representation of the Zone.

        Returns:
            str: Zone description.
        """
        zt = self.zone_type.value
        return f"Zone({self.name}, type={zt}, cap={self.max_drones})"
