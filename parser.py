import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Process:
    """Represents a single process and tracks its execution metrics."""
    name: str
    arrival_time: int
    service_time: int  # Also serves as initial priority for Aging
    finish_time: int = 0

    @property
    def priority_level(self) -> int:
        return self.service_time

    @property
    def turnaround_time(self) -> int:
        return self.finish_time - self.arrival_time

    @property
    def normalized_turnaround(self) -> float:
        return self.turnaround_time / self.service_time if self.service_time else 0.0

    def response_ratio(self, current_time: int) -> float:
        wait_time = current_time - self.arrival_time
        return (wait_time + self.service_time) / self.service_time


def parse_algorithms(algorithm_chunk: str) -> List[Tuple[str, int]]:
    """Parses comma-separated algorithm specs like '1,2-1,2-4,3,4,5,6,7,8-1'."""
    algorithms: List[Tuple[str, int]] = []
    for item in algorithm_chunk.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split("-")
        algorithm_id = parts[0].strip()
        if len(algorithm_id) != 1 or not algorithm_id.isdigit():
            raise ValueError(f"Invalid algorithm specification: '{item}'")

        if len(parts) > 1 and parts[1].strip():
            try:
                quantum = int(parts[1].strip())
            except ValueError as exc:
                raise ValueError(f"Invalid quantum value in '{item}'") from exc
        else:
            quantum = -1

        algorithms.append((algorithm_id, quantum))

    if not algorithms:
        raise ValueError("No valid algorithms specified.")
    return algorithms


def parse_input(raw_text: Optional[str] = None) -> Tuple[str, List[Tuple[str, int]], int, List[Process]]:
    """Reads problem configuration and processes from raw_text or standard input."""
    source = raw_text if raw_text is not None else sys.stdin.read()
    tokens = source.split()
    if not tokens:
        raise ValueError("Input is empty. Please provide scheduling configuration and processes.")

    if len(tokens) < 4:
        raise ValueError(
            "Incomplete header. Expected at least 4 lines/tokens: "
            "<operation> <algorithms> <last_instant> <process_count>."
        )

    operation = tokens[0].strip()
    if operation not in ("trace", "stats"):
        raise ValueError(f"Invalid operation '{operation}'. Expected 'trace' or 'stats'.")

    algorithm_chunk = tokens[1].strip()
    try:
        last_instant = int(tokens[2])
        process_count = int(tokens[3])
    except ValueError as exc:
        raise ValueError("Both 'last_instant' and 'process_count' must be integers.") from exc

    if last_instant <= 0 or process_count <= 0:
        raise ValueError("'last_instant' and 'process_count' must be positive integers.")

    if len(tokens) < 4 + process_count:
        raise ValueError(
            f"Expected {process_count} process definitions, but found {len(tokens) - 4}."
        )

    algorithms = parse_algorithms(algorithm_chunk)

    processes: List[Process] = []
    for i in range(process_count):
        process_chunk = tokens[4 + i]
        parts = process_chunk.split(",")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid process format '{process_chunk}'. Expected 'Name,Arrival,Service'."
            )
        name, arrival_str, service_str = parts
        try:
            arrival_time = int(arrival_str.strip())
            service_time = int(service_str.strip())
        except ValueError as exc:
            raise ValueError(
                f"Arrival and service times must be integers in '{process_chunk}'."
            ) from exc

        processes.append(
            Process(
                name=name.strip(),
                arrival_time=arrival_time,
                service_time=service_time,
            )
        )

    return operation, algorithms, last_instant, processes