import workloads.postgres

NUM_OF_OPS: int = 1000
postgres_tester: workloads.postgres.PostgresTester = workloads.postgres.PostgresTester()

postgres_tester.test_all(NUM_OF_OPS)
