"""Map parser for reading and validating Fly-in network files."""

import re
from typing import Dict, List, Tuple
from zone import Zone, ZoneType
from connection import Connection
from graph import Graph
from exceptions import MapParsingError


class MapParser:
    """Parses Fly-in map files into Graph data structures."""

    VALID_ZONE_TYPES = {
        "normal": ZoneType.NORMAL,
        "blocked": ZoneType.BLOCKED,
        "restricted": ZoneType.RESTRICTED,
        "priority": ZoneType.PRIORITY,
    }

    @staticmethod
    def parse_file(filepath: str) -> Graph:
        """Parse a map file at the given filepath into a Graph.

        Args:
            filepath: Absolute or relative path to map file.

        Returns:
            Graph: Populated and validated Graph instance.

        Raises:
            MapParsingError: If any parsing syntax or validation error occurs.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            raise MapParsingError(f"Map file not found: {filepath}")
        except Exception as err:
            raise MapParsingError(f"Failed to read map file: {err}")

        return MapParser.parse_lines(lines)

    @staticmethod
    def parse_lines(lines: List[str]) -> Graph:
        """Parse a list of file lines into a Graph instance.

        Args:
            lines: List of text lines from a map file.

        Returns:
            Graph: Populated and validated Graph instance.

        Raises:
            MapParsingError: If any parsing syntax or validation error occurs.
        """
        graph = Graph()
        nb_drones_found = False

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            # Ignore comments and empty lines
            if not line or line.startswith("#"):
                continue

            # 1. Parse number of drones (must be first data line)
            if line.startswith("nb_drones:"):
                if nb_drones_found:
                    raise MapParsingError("Duplicate nb_drones line encountered", idx)
                parts = line.split(":", 1)
                value_str = parts[1].strip()
                try:
                    nb = int(value_str)
                    if nb <= 0:
                        raise ValueError()
                    graph.nb_drones = nb
                    nb_drones_found = True
                except ValueError:
                    raise MapParsingError(
                        f"nb_drones must be a positive integer, got '{value_str}'", idx
                    )
                continue

            if not nb_drones_found:
                raise MapParsingError(
                    "First non-comment line must define 'nb_drones: <number>'", idx
                )

            # 2. Parse zone definitions (start_hub:, end_hub:, hub:)
            if (
                line.startswith("start_hub:")
                or line.startswith("end_hub:")
                or line.startswith("hub:")
            ):
                MapParser._parse_zone_line(line, graph, idx)
                continue

            # 3. Parse connection definitions (connection:)
            if line.startswith("connection:"):
                MapParser._parse_connection_line(line, graph, idx)
                continue

            # Invalid line format
            raise MapParsingError(f"Unrecognized syntax or command: '{line}'", idx)

        # Validate graph requirements
        try:
            graph.validate()
        except ValueError as err:
            raise MapParsingError(str(err))

        return graph

    @staticmethod
    def _extract_metadata(line_body: str, line_num: int) -> Tuple[str, Dict[str, str]]:
        """Extract metadata inside [...] from the end of a line body.

        Args:
            line_body: Line text content.
            line_num: Line number for error reporting.

        Returns:
            Tuple[str, Dict[str, str]]: (clean_line_body, metadata_dict).

        Raises:
            MapParsingError: If bracket syntax is invalid.
        """
        metadata: Dict[str, str] = {}
        line_body = line_body.strip()
        if "[" not in line_body:
            return line_body, metadata

        match = re.search(r"\[(.*?)\]$", line_body)
        if not match:
            raise MapParsingError("Malformed metadata bracket syntax", line_num)

        meta_str = match.group(1).strip()
        clean_body = line_body[: match.start()].strip()

        if meta_str:
            tokens = meta_str.split()
            for token in tokens:
                if "=" not in token:
                    raise MapParsingError(
                        f"Invalid metadata key-value token '{token}'", line_num
                    )
                key, val = token.split("=", 1)
                key = key.strip()
                val = val.strip()
                if not key or not val:
                    raise MapParsingError(
                        f"Empty metadata key or value in '{token}'", line_num
                    )
                metadata[key] = val

        return clean_body, metadata

    @staticmethod
    def _parse_zone_line(line: str, graph: Graph, line_num: int) -> None:
        """Parse a zone line (start_hub:, end_hub:, or hub:).

        Args:
            line: Full line string.
            graph: Target Graph instance.
            line_num: Line number for error reporting.

        Raises:
            MapParsingError: On invalid syntax or values.
        """
        if line.startswith("start_hub:"):
            prefix = "start_hub:"
            is_start, is_end = True, False
        elif line.startswith("end_hub:"):
            prefix = "end_hub:"
            is_start, is_end = False, True
        else:
            prefix = "hub:"
            is_start, is_end = False, False

        body = line[len(prefix) :].strip()
        body_no_meta, meta = MapParser._extract_metadata(body, line_num)

        tokens = body_no_meta.split()
        if len(tokens) != 3:
            raise MapParsingError(
                f"Zone definition requires '<name> <x> <y>', got '{body_no_meta}'", line_num
            )

        name, x_str, y_str = tokens[0], tokens[1], tokens[2]

        if "-" in name or " " in name:
            raise MapParsingError(
                f"Zone name '{name}' cannot contain dashes or spaces", line_num
            )

        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise MapParsingError(
                f"Zone coordinates must be integers, got x='{x_str}', y='{y_str}'", line_num
            )

        # Parse metadata
        zone_type = ZoneType.NORMAL
        if "zone" in meta:
            zt_str = meta["zone"].lower()
            if zt_str not in MapParser.VALID_ZONE_TYPES:
                raise MapParsingError(
                    f"Invalid zone type '{zt_str}'. Must be one of: "
                    f"{', '.join(MapParser.VALID_ZONE_TYPES.keys())}",
                    line_num,
                )
            zone_type = MapParser.VALID_ZONE_TYPES[zt_str]

        color = meta.get("color", None)

        max_drones = 1
        if "max_drones" in meta:
            try:
                max_drones = int(meta["max_drones"])
                if max_drones <= 0:
                    raise ValueError()
            except ValueError:
                raise MapParsingError(
                    f"max_drones must be a positive integer, got '{meta['max_drones']}'",
                    line_num,
                )

        try:
            zone = Zone(
                name=name,
                x=x,
                y=y,
                zone_type=zone_type,
                color=color,
                max_drones=max_drones,
                is_start=is_start,
                is_end=is_end,
            )
            graph.add_zone(zone)
        except ValueError as err:
            raise MapParsingError(str(err), line_num)

    @staticmethod
    def _parse_connection_line(line: str, graph: Graph, line_num: int) -> None:
        """Parse a connection line (connection: <zone1>-<zone2> [metadata]).

        Args:
            line: Full line string.
            graph: Target Graph instance.
            line_num: Line number for error reporting.

        Raises:
            MapParsingError: On invalid syntax or connection error.
        """
        body = line[len("connection:") :].strip()
        body_no_meta, meta = MapParser._extract_metadata(body, line_num)

        parts = body_no_meta.split("-")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise MapParsingError(
                f"Connection format must be 'connection: <zone1>-<zone2>', got '{body_no_meta}'",
                line_num,
            )

        z1_name, z2_name = parts[0].strip(), parts[1].strip()

        if z1_name not in graph.zones:
            raise MapParsingError(
                f"Connection references undefined zone '{z1_name}'", line_num
            )
        if z2_name not in graph.zones:
            raise MapParsingError(
                f"Connection references undefined zone '{z2_name}'", line_num
            )

        max_link_capacity = 1
        if "max_link_capacity" in meta:
            try:
                max_link_capacity = int(meta["max_link_capacity"])
                if max_link_capacity <= 0:
                    raise ValueError()
            except ValueError:
                cap_val = meta["max_link_capacity"]
                raise MapParsingError(
                    f"max_link_capacity must be > 0, got '{cap_val}'",
                    line_num,
                )

        try:
            conn = Connection(
                zone1=graph.zones[z1_name],
                zone2=graph.zones[z2_name],
                max_link_capacity=max_link_capacity,
            )
            graph.add_connection(conn)
        except ValueError as err:
            raise MapParsingError(str(err), line_num)
