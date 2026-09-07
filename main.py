"""Main CLI entry point for the Fly-in drone routing system."""

import argparse
import sys
from typing import List, Optional
from map_parser import MapParser
from exceptions import MapParsingError
from engine import SimulationEngine, SimulationResult
from visualizer import TerminalVisualizer


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments for the application.

    Args:
        args: List of command line arguments (defaults to sys.argv[1:]).

    Returns:
        argparse.Namespace: Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Fly-in: Autonomous Drone Routing & Simulation System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "map_file",
        nargs="?",
        default="maps/example_subject.txt",
        help="Path to the map input text file.",
    )
    parser.add_argument(
        "-v",
        "--visual",
        action="store_true",
        help="Enable colorized visual feedback for terminal output.",
    )
    parser.add_argument(
        "-c",
        "--capacity-info",
        action="store_true",
        help="Display zone and connection capacity information during simulation.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Output raw turn lines only (for evaluation scripts).",
    )
    return parser.parse_args(args)


def run_simulation(
    map_filepath: str, visual_mode: bool = False, capacity_info: bool = False
) -> int:
    """Load map file, run drone simulation, and display results.

    Args:
        map_filepath: Path to input map file.
        visual_mode: If True, display colorized turn output.
        capacity_info: If True, display capacity usage breakdown per turn.

    Returns:
        int: Exit status code (0 for success, 1 for errors).
    """
    try:
        graph = MapParser.parse_file(map_filepath)
        engine = SimulationEngine(graph)
        result: SimulationResult = engine.run()

        if visual_mode:
            print("\n=== STARTING SIMULATION ===")
            for idx, turn_line in enumerate(result.turn_lines, start=1):
                rendered = TerminalVisualizer.render_turn(idx, turn_line, graph)
                print(rendered)
                if capacity_info and idx <= len(result.capacity_lines):
                    cap_info = result.capacity_lines[idx - 1]
                    if cap_info:
                        print(f"   [Capacity] {cap_info}")
            TerminalVisualizer.print_summary(result.total_turns, graph.nb_drones)
        else:
            print(result.format_output(show_capacity=capacity_info))

        return 0

    except MapParsingError as err:
        print(f"Parsing Error: {err}", file=sys.stderr)
        return 1
    except RuntimeError as err:
        print(f"Simulation Error: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"Unexpected Error: {err}", file=sys.stderr)
        return 1


def main() -> int:
    """CLI execution entry point.

    Returns:
        int: System exit code.
    """
    options = parse_arguments()
    return run_simulation(
        options.map_file,
        visual_mode=options.visual,
        capacity_info=options.capacity_info,
    )


if __name__ == "__main__":
    sys.exit(main())
