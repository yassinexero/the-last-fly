*This project has been created as part of the 42 curriculum by <yel-ghaz>.*

# Fly-in: Autonomous Drone Routing & Simulation System

## Description

**Fly-in** is a high-performance, object-oriented Python drone simulation system designed to route a fleet of drones from a central starting base (`start_hub`) to a target destination (`end_hub`) through a network of connected zones in the minimum possible simulation turns.

The system handles dynamic zone occupancy limits (`max_drones`), connection capacities (`max_link_capacity`), variable movement costs (`normal`, `priority`, `restricted` 2-turn transit, `blocked` impassable zones), simultaneous drone movements, and path conflict resolution.

---

## Features

- **Pure Python Implementation**: No external graph or pathfinding libraries (`networkx`, `graphlib`) used.
- **Type-Safe & Strict Quality**: 100% compliant with `flake8` and strict `mypy` type checking (`mypy --strict`).
- **Breadth-First Search (BFS) Routing**: Multi-path BFS pathfinder to maximize drone throughput.
- **Simultaneous Turn Simulation**: Drones exiting a zone free up capacity during that same turn.
- **Terminal Visualizer**: Colorized terminal output highlighting zone color attributes.
- **Capacity Monitoring**: Live turn-by-turn capacity inspection using `--capacity-info`.

---

## Instructions

### Dependencies & Setup

Ensure Python 3.10+ is installed on your system. Install dependencies using the provided `Makefile`:

```bash
make install
```

### Running the Application

Execute the main simulation with a map file:

```bash
# Standard output format
python main.py maps/example_subject.txt

# Colorized visual mode
python main.py -v maps/example_subject.txt

# Capacity usage breakdown mode
python main.py --capacity-info maps/example_subject.txt

# Combined visual and capacity info mode
python main.py -v --capacity-info maps/example_subject.txt
```

Or run via `Makefile`:

```bash
make run
```

### Makefile Rules

- `make install`: Install project dependencies via pip.
- `make run`: Execute main script on the default map.
- `make debug`: Launch main script in Python debugger (`pdb`).
- `make clean`: Remove cached bytecode (`__pycache__`, `.mypy_cache`).
- `make lint`: Run `flake8` and strict `mypy` static type checks.
- `make lint-strict`: Run strict `flake8` and `mypy --strict`.

---

## Algorithm Explanation

### 1. Object-Oriented Domain Architecture
- `Zone` (`zone.py`): Represents graph nodes with integer coordinates `(x, y)`, zone types (`NORMAL`, `BLOCKED`, `RESTRICTED`, `PRIORITY`), display colors, and max drone capacities (`max_drones`).
- `Connection` (`connection.py`): Represents bidirectional edges linking two zones with capacity constraints (`max_link_capacity`).
- `Drone` (`drone.py`): Tracks individual drone entity state, transit timers for restricted zones, and delivery status.
- `Graph` (`graph.py`): Stores node adjacencies, start/end hubs, and structural integrity validations.

### 2. BFS Pathfinding & Multi-Path Allocation (`pathfinder.py`)
- **Weighted BFS**: Uses Breadth-First Search to find the shortest turn-cost paths from `start_hub` to `end_hub`. Restricted zones cost 2 turns, normal zones cost 1 turn, and priority zones cost 1 turn with preferred path selection.
- **Multi-Path Routing**: Discovers parallel and edge-disjoint routes across the graph topology to allow simultaneous drone traversal.
- **Path Load Allocation**: Equitably balances drones across available paths to minimize total simulation turn duration.

### 3. Discrete Turn Simulation Engine (`engine.py`)
- **Simultaneous Move Mechanics**: At each turn step, drones leaving a zone immediately free up capacity for incoming drones on that same turn.
- **Multi-Turn Restricted Transit**: Drones moving to a `restricted` zone spend 1 turn in transit on the connection edge (`D<ID>-<connection>`) and arrive at the destination zone on turn 2 (`D<ID>-<zone>`).

---

## Visual Representation

The application includes a `TerminalVisualizer` (`visualizer.py`) that translates zone `color` attributes (`red`, `green`, `blue`, `yellow`, `gray`, `cyan`, `magenta`) into ANSI terminal color codes.

Passing the `-v` or `--visual` flag renders color-coded target zones for each turn and displays a summary report:

```
[Turn 01] D1-corridorA D3-hub-roof1
[Turn 02] D3-roof1 D1-tunnelB D2-corridorA D3-roof2 D4-corridorA D5-hub-roof1
[Turn 03] D5-roof1 D1-goal D2-tunnelB D3-goal D5-roof2
...
```

---

## Example Input & Expected Output

### Sample Input (`maps/example_subject.txt`):

```txt
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

### Expected Standard Output (`python main.py maps/example_subject.txt`):

```txt
D1-corridorA D3-hub-roof1
D3-roof1 D1-tunnelB D2-corridorA D3-roof2 D4-corridorA D5-hub-roof1
D5-roof1 D1-goal D2-tunnelB D3-goal D5-roof2
D2-goal D4-tunnelB D5-goal
D4-goal
```

---

## Resources

- **Graph Algorithms & BFS**: Reference material on Breadth-First Search, Dijkstra's algorithm, and multi-path routing.
- **Python Type Hints & PEP 257**: Official Python typing documentation and docstring standards.
- **AI Tool Usage**: AI assistant was utilized for code structuring, flake8/mypy strict compliance validation, map parsing edge cases, and generating comprehensive project documentation.
