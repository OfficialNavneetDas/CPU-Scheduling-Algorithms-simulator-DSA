import copy
import heapq
from collections import deque
from typing import List

from parser import Process, parse_input

TRACE = "trace"
SHOW_STATISTICS = "stats"


class Scheduler:
    """Simulates CPU scheduling algorithms and formats timeline/stats output."""

    ALGORITHMS = {
        "1": "FCFS",
        "2": "RR",
        "3": "SPN",
        "4": "SRT",
        "5": "HRRN",
        "6": "FB-1",
        "7": "FB-2i",
        "8": "Aging",
    }

    def __init__(self, processes: List[Process], last_instant: int):
        self.processes: List[Process] = copy.deepcopy(processes)
        self.last_instant: int = last_instant
        self.process_count: int = len(self.processes)
        self.process_to_index = {p.name: idx for idx, p in enumerate(self.processes)}
        self.timeline: List[List[str]] = [
            [" " for _ in range(self.process_count)] for _ in range(self.last_instant)
        ]

    def _fill_in_wait_time(self) -> None:
        for idx, proc in enumerate(self.processes):
            for t in range(proc.arrival_time, min(proc.finish_time, self.last_instant)):
                if self.timeline[t][idx] != "*":
                    self.timeline[t][idx] = "."

    def first_come_first_serve(self) -> None:
        if not self.processes:
            return
        time = self.processes[0].arrival_time
        for idx, proc in enumerate(self.processes):
            proc.finish_time = time + proc.service_time
            for t in range(proc.arrival_time, time):
                if t < self.last_instant:
                    self.timeline[t][idx] = "."
            for t in range(time, proc.finish_time):
                if t < self.last_instant:
                    self.timeline[t][idx] = "*"
            time += proc.service_time

    def round_robin(self, quantum: int) -> None:
        queue = deque()
        j = 0
        if self.process_count > 0 and self.processes[0].arrival_time == 0:
            queue.append([0, self.processes[0].service_time])
            j += 1

        current_quantum = quantum
        for time in range(self.last_instant):
            if queue:
                proc_idx, rem_time = queue[0]
                rem_time -= 1
                queue[0][1] = rem_time
                current_quantum -= 1
                self.timeline[time][proc_idx] = "*"

                while j < self.process_count and self.processes[j].arrival_time == time + 1:
                    queue.append([j, self.processes[j].service_time])
                    j += 1

                if rem_time == 0:
                    self.processes[proc_idx].finish_time = time + 1
                    queue.popleft()
                    current_quantum = quantum
                elif current_quantum == 0:
                    queue.popleft()
                    queue.append([proc_idx, rem_time])
                    current_quantum = quantum

            while j < self.process_count and self.processes[j].arrival_time == time + 1:
                queue.append([j, self.processes[j].service_time])
                j += 1

        self._fill_in_wait_time()

    def shortest_process_next(self) -> None:
        pq = []
        j = 0
        time = 0
        while time < self.last_instant:
            while j < self.process_count and self.processes[j].arrival_time <= time:
                heapq.heappush(pq, (self.processes[j].service_time, j))
                j += 1

            if pq:
                _, proc_idx = heapq.heappop(pq)
                proc = self.processes[proc_idx]
                for t in range(proc.arrival_time, time):
                    self.timeline[t][proc_idx] = "."
                for t in range(time, min(time + proc.service_time, self.last_instant)):
                    self.timeline[t][proc_idx] = "*"

                proc.finish_time = time + proc.service_time
                time += proc.service_time
            else:
                time += 1

    def shortest_remaining_time(self) -> None:
        pq = []
        j = 0
        for time in range(self.last_instant):
            while j < self.process_count and self.processes[j].arrival_time == time:
                heapq.heappush(pq, (self.processes[j].service_time, j))
                j += 1

            if pq:
                rem_time, proc_idx = heapq.heappop(pq)
                self.timeline[time][proc_idx] = "*"
                if rem_time == 1:
                    self.processes[proc_idx].finish_time = time + 1
                else:
                    heapq.heappush(pq, (rem_time - 1, proc_idx))

        self._fill_in_wait_time()

    def highest_response_ratio_next(self) -> None:
        ready = []
        j = 0
        time = 0

        while time < self.last_instant:
            while j < self.process_count and self.processes[j].arrival_time <= time:
                ready.append([self.processes[j].name, 1.0, 0])
                j += 1

            for item in ready:
                proc = self.processes[self.process_to_index[item[0]]]
                item[1] = proc.response_ratio(time)

            ready.sort(key=lambda x: x[1], reverse=True)

            if ready:
                proc_idx = self.process_to_index[ready[0][0]]
                proc = self.processes[proc_idx]
                while time < self.last_instant and ready[0][2] != proc.service_time:
                    self.timeline[time][proc_idx] = "*"
                    time += 1
                    ready[0][2] += 1

                ready.pop(0)
                proc.finish_time = time
            else:
                time += 1

        self._fill_in_wait_time()

    def feedback_q1(self) -> None:
        pq = []
        rem_service = {}
        j = 0

        if self.process_count > 0 and self.processes[0].arrival_time == 0:
            heapq.heappush(pq, (0, 0))
            rem_service[0] = self.processes[0].service_time
            j += 1

        for time in range(self.last_instant):
            if pq:
                prio, proc_idx = heapq.heappop(pq)

                while j < self.process_count and self.processes[j].arrival_time == time + 1:
                    heapq.heappush(pq, (0, j))
                    rem_service[j] = self.processes[j].service_time
                    j += 1

                rem_service[proc_idx] -= 1
                self.timeline[time][proc_idx] = "*"

                if rem_service[proc_idx] == 0:
                    self.processes[proc_idx].finish_time = time + 1
                else:
                    next_prio = prio + 1 if pq else prio
                    heapq.heappush(pq, (next_prio, proc_idx))

            while j < self.process_count and self.processes[j].arrival_time == time + 1:
                heapq.heappush(pq, (0, j))
                rem_service[j] = self.processes[j].service_time
                j += 1

        self._fill_in_wait_time()

    def feedback_q2i(self) -> None:
        pq = []
        rem_service = {}
        j = 0

        if self.process_count > 0 and self.processes[0].arrival_time == 0:
            heapq.heappush(pq, (0, 0))
            rem_service[0] = self.processes[0].service_time
            j += 1

        time = 0
        while time < self.last_instant:
            if pq:
                prio, proc_idx = heapq.heappop(pq)

                while j < self.process_count and self.processes[j].arrival_time <= time + 1:
                    heapq.heappush(pq, (0, j))
                    rem_service[j] = self.processes[j].service_time
                    j += 1

                current_quantum = 2 ** prio
                temp = time
                while (
                    current_quantum > 0
                    and rem_service[proc_idx] > 0
                    and temp < self.last_instant
                ):
                    current_quantum -= 1
                    rem_service[proc_idx] -= 1
                    self.timeline[temp][proc_idx] = "*"
                    temp += 1

                if rem_service[proc_idx] == 0:
                    self.processes[proc_idx].finish_time = temp
                else:
                    next_prio = prio + 1 if pq else prio
                    heapq.heappush(pq, (next_prio, proc_idx))

                time = temp
            else:
                while j < self.process_count and self.processes[j].arrival_time <= time + 1:
                    heapq.heappush(pq, (0, j))
                    rem_service[j] = self.processes[j].service_time
                    j += 1
                time += 1

        self._fill_in_wait_time()

    def aging(self, quantum: int) -> None:
        ready = []
        j = 0
        current_proc = -1
        time = 0

        while time < self.last_instant:
            while j < self.process_count and self.processes[j].arrival_time <= time:
                ready.append([self.processes[j].priority_level, j, 0])
                j += 1

            for item in ready:
                if item[1] == current_proc:
                    item[2] = 0
                    item[0] = self.processes[current_proc].priority_level
                else:
                    item[0] += 1
                    item[2] += 1

            ready.sort(key=lambda x: (x[0], x[2]), reverse=True)

            current_proc = ready[0][1]
            current_quantum = quantum
            while current_quantum > 0 and time < self.last_instant:
                self.timeline[time][current_proc] = "*"
                time += 1
                current_quantum -= 1

        self._fill_in_wait_time()

    def run(self, algorithm_id: str, quantum: int = 0) -> str:
        dispatch = {
            "1": lambda: self.first_come_first_serve(),
            "2": lambda: self.round_robin(quantum),
            "3": lambda: self.shortest_process_next(),
            "4": lambda: self.shortest_remaining_time(),
            "5": lambda: self.highest_response_ratio_next(),
            "6": lambda: self.feedback_q1(),
            "7": lambda: self.feedback_q2i(),
            "8": lambda: self.aging(quantum),
        }
        if algorithm_id not in dispatch:
            raise ValueError(f"Unknown algorithm ID: {algorithm_id}")

        dispatch[algorithm_id]()
        base_name = self.ALGORITHMS[algorithm_id]
        return f"{base_name}-{quantum}" if algorithm_id == "2" else base_name

    def format_timeline(self, label: str) -> str:
        header = f"{label:<6}" + " ".join(str(i % 10) for i in range(self.last_instant + 1)) + " "
        divider = "-" * 48
        rows = [header, divider]
        for idx, proc in enumerate(self.processes):
            cells = "|".join(self.timeline[t][idx] for t in range(self.last_instant))
            rows.append(f"{proc.name}     |{cells}| ")
        rows.append(divider)
        return "\n".join(rows)

    def format_stats(self, label: str) -> str:
        proc_row = "Process    " + "".join(f"|  {p.name}  " for p in self.processes) + "|"
        arr_row = "Arrival    " + "".join(f"|{p.arrival_time:3d}  " for p in self.processes) + "|"
        srv_row = "Service    |" + "".join(f"{p.service_time:3d}  |" for p in self.processes) + " Mean|"
        fin_row = "Finish     " + "".join(f"|{p.finish_time:3d}  " for p in self.processes) + "|-----|"

        tat_values = [p.turnaround_time for p in self.processes]
        mean_tat = sum(tat_values) / self.process_count
        tat_row = (
            "Turnaround |"
            + "".join(f"{t:3d}  |" for t in tat_values)
            + (f"{mean_tat:2.2f}|" if mean_tat >= 10 else f" {mean_tat:2.2f}|")
        )

        nt_values = [p.normalized_turnaround for p in self.processes]
        mean_nt = sum(nt_values) / self.process_count
        nt_cells = "".join(f"{nt:2.2f}|" if nt >= 10 else f" {nt:2.2f}|" for nt in nt_values)
        nt_mean_cell = f"{mean_nt:2.2f}|" if mean_nt >= 10 else f" {mean_nt:2.2f}|"
        nt_row = f"NormTurn   |{nt_cells}{nt_mean_cell}"

        return "\n".join([label, proc_row, arr_row, srv_row, fin_row, tat_row, nt_row])


def main():
    operation, algorithms, last_instant, processes = parse_input()

    for alg_id, quantum in algorithms:
        scheduler = Scheduler(processes, last_instant)
        label = scheduler.run(alg_id, quantum)
        if operation == TRACE:
            print(scheduler.format_timeline(label))
        elif operation == SHOW_STATISTICS:
            print(scheduler.format_stats(label))
        print()


if __name__ == "__main__":
    main()