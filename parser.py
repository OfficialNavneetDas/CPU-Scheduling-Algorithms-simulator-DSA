import sys
from dataclasses import dataclass
from typing import List, Tuple


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
        algorithm_id = parts[0][0]
        quantum = int(parts[1]) if len(parts) > 1 and len(parts[1]) >= 1 else -1
        algorithms.append((algorithm_id, quantum))
    return algorithms


def parse_input() -> Tuple[str, List[Tuple[str, int]], int, List[Process]]:
    """Reads problem configuration and processes from standard input."""
    tokens = sys.stdin.read().split()
    if not tokens:
        raise ValueError("No input provided on stdin.")

    operation = tokens[0]
    algorithm_chunk = tokens[1]
    last_instant = int(tokens[2])
    process_count = int(tokens[3])

    algorithms = parse_algorithms(algorithm_chunk)

    processes: List[Process] = []
    for i in range(process_count):
        process_chunk = tokens[4 + i]
        name, arrival_str, service_str = process_chunk.split(",")
        processes.append(
            Process(
                name=name.strip(),
                arrival_time=int(arrival_str),
                service_time=int(service_str),
            )
        )

    return operation, algorithms, last_instant, processes