import workloads.tests

print("DO SETUP")
workloads.tests.setup()
print("FINISHED SETUPS")



def process_results(title: str, num_of_ops: int, r: tuple[float, float, float]) -> None:
    postgres_dur: float = r[0]
    mongo_dur: float = r[1]
    redis_dur: float = r[2]

    postgres_avg: float = r[0] / NUM_OF_OPS
    mongo_avg: float = r[1] / NUM_OF_OPS
    redis_avg: float = r[2] / NUM_OF_OPS

    print(f"RESULTS - {title}")
    print(f"Number of operations: {num_of_ops}")
    print("")
    print("Postgres DB:")
    print(f" Total: {postgres_dur:>10}")
    print(f" Avg  : {postgres_avg:>10}")
    print("")
    print("Mongo DB:")
    print(f" Total: {mongo_dur:>10}")
    print(f" Avg  : {mongo_avg:>10}")
    print("")
    print("Redis DB:")
    print(f" Total: {redis_dur:>10}")
    print(f" Avg  : {redis_avg:>10}")


NUM_OF_OPS: int = 5000
r_read = workloads.tests.test_read(NUM_OF_OPS)
process_results("Read", NUM_OF_OPS, r_read)

r_write = workloads.tests.test_write(NUM_OF_OPS)
process_results("Write", NUM_OF_OPS, r_write)


r_update = workloads.tests.test_update(NUM_OF_OPS)
process_results("Update", NUM_OF_OPS, r_update)
