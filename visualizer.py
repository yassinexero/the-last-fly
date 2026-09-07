"""Terminal visualizer for colorized simulation feedback."""

from typing import Dict, List, Optional
from graph import Graph


class TerminalVisualizer:
    """Provides colorized terminal output for drone simulation steps."""

    # Rich ANSI 256-color mappings for all common color names
    COLOR_CODES: Dict[str, str] = {
        "red": "\033[38;5;196m",
        "green": "\033[38;5;46m",
        "yellow": "\033[38;5;226m",
        "blue": "\033[38;5;39m",
        "magenta": "\033[38;5;201m",
        "cyan": "\033[38;5;51m",
        "white": "\033[38;5;231m",
        "gray": "\033[38;5;245m",
        "grey": "\033[38;5;245m",
        "orange": "\033[38;5;208m",
        "gold": "\033[38;5;220m",
        "lime": "\033[38;5;118m",
        "purple": "\033[38;5;135m",
        "brown": "\033[38;5;130m",
        "pink": "\033[38;5;213m",
        "violet": "\033[38;5;177m",
        "teal": "\033[38;5;37m",
        "navy": "\033[38;5;25m",
        "olive": "\033[38;5;142m",
        "silver": "\033[38;5;250m",
        "maroon": "\033[38;5;124m",
        "coral": "\033[38;5;209m",
        "indigo": "\033[38;5;63m",
        "turquoise": "\033[38;5;45m",
    }

    RESET: str = "\033[0m"
    BOLD: str = "\033[1m"

    @classmethod
    def get_color_code(cls, color: str) -> str:
        """Get ANSI 256-color escape code for any color name.

        Args:
            color: Color name string.

        Returns:
            str: ANSI color escape sequence.
        """
        key = color.lower().strip()
        if key in cls.COLOR_CODES:
            return cls.COLOR_CODES[key]
        # Deterministic fallback mapping to 256-color palette
        val = sum(ord(c) for c in key) % 216
        return f"\033[38;5;{16 + val}m"

    @classmethod
    def colorize(
        cls, text: str, color: Optional[str], bold: bool = True
    ) -> str:
        """Wrap text in ANSI color escape sequence if color is defined.

        Args:
            text: Input string to colorize.
            color: Color name key (e.g. 'orange', 'gold', 'lime').
            bold: If True, apply bold style.

        Returns:
            str: Colorized string or original text if color is None.
        """
        if not color:
            return text
        code = cls.get_color_code(color)
        bold_code = cls.BOLD if bold else ""
        return f"{bold_code}{code}{text}{cls.RESET}"

    @classmethod
    def render_turn(cls, turn_num: int, turn_line: str, graph: Graph) -> str:
        """Render a single turn line with zone color highlights.

        Args:
            turn_num: Current turn index (1-based).
            turn_line: Standard movement line (e.g. 'D1-roof1 D2-corridorA').
            graph: Graph instance containing zone color attributes.

        Returns:
            str: Rendered colorized string for terminal display.
        """
        movements = turn_line.split()
        colorized_moves: List[str] = []

        for move in movements:
            if "-" not in move:
                colorized_moves.append(move)
                continue
            drone_part, target_part = move.split("-", 1)

            target_color = None
            if target_part in graph.zones:
                target_color = graph.zones[target_part].color
            elif "-" in target_part:
                # In transit on connection (e.g. hub-roof1)
                sub_parts = target_part.split("-", 1)
                if sub_parts[1] in graph.zones:
                    target_color = graph.zones[sub_parts[1]].color

            # Bold drone identifier in bright white
            drone_styled = f"{cls.BOLD}\033[38;5;231m{drone_part}{cls.RESET}"

            if target_color:
                colored_target = cls.colorize(
                    target_part, target_color, bold=True
                )
            else:
                colored_target = f"{cls.BOLD}{target_part}{cls.RESET}"

            colorized_moves.append(f"{drone_styled}-{colored_target}")

        header = cls.colorize(f"[Turn {turn_num:02d}]", "cyan", bold=True)
        return f"{header} {' '.join(colorized_moves)}"

    @classmethod
    def print_summary(cls, total_turns: int, nb_drones: int) -> None:
        """Print colored summary statistics upon simulation completion.

        Args:
            total_turns: Total simulation turns completed.
            nb_drones: Total drones delivered.
        """
        title = cls.colorize(
            "=== SIMULATION COMPLETED ===", "green", bold=True
        )
        turns_str = cls.colorize(str(total_turns), "yellow", bold=True)
        drones_str = cls.colorize(str(nb_drones), "magenta", bold=True)

        print(f"\n{title}")
        print(f"Total Drones Delivered: {drones_str}")
        print(f"Total Simulation Turns: {turns_str}\n")
