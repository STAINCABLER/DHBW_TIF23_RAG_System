import time

def process_result(title: str, number_of_operations: int, latency: float) -> None:
    rounded_duration: float = round(latency, 3)

    average_duration: float = round(latency / number_of_operations * 1000)

    requests_per_second: int = int(1 // (latency / number_of_operations))
    print(title)
    print(f" Total: {rounded_duration:>8}s")
    print(f" Avg  : {average_duration:>8}ms")
    print(f" Req/s: {requests_per_second:>8}/s")
    print("")


class BaseTester():
    def __init__(self):
        self.db_name: str = "Base"

    def setup(self) -> None:
        pass

    def test_all(self, number_of_operations: int = 100) -> None:
        self.setup()

        read_duration: float = self.test_read(number_of_operations)
        process_result(self.db_name, number_of_operations, read_duration)

        write_duration: float = self.test_write(number_of_operations)
        process_result(self.db_name, number_of_operations, write_duration)

        update_duration: float = self.test_update(number_of_operations)
        process_result(self.db_name, number_of_operations, update_duration)

        bulk_read_duration: float = self.test_bulk_read(number_of_operations)
        process_result(self.db_name, number_of_operations, bulk_read_duration)

        bulk_write_duration: float = self.test_bulk_write(number_of_operations)
        process_result(self.db_name, number_of_operations, bulk_write_duration)

    def test_read(self, number_of_operations: int = 100) -> float:
        return 1.0

    def test_write(self, number_of_operations: int = 100) -> float:
        return 1.0

    def test_update(self, number_of_operations: int = 100) -> float:
        return 1.0

    def test_bulk_read(self, number_of_operations: int = 100) -> float:
        return 1.0

    def test_bulk_write(self, number_of_operations: int = 100) -> float:
        return 1.0

class Timer():
    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration: float = 0.0

    def start(self) -> None:
        self.start_time = time.perf_counter()

    def stop(self) -> None:
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time


