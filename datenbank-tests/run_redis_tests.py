import workloads.redis

NUM_OF_OPS: int = 1000
redis_tester: workloads.redis.RedisTester = workloads.redis.RedisTester()

redis_tester.test_all(NUM_OF_OPS)
