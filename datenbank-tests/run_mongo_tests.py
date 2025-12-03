import workloads.mongo

NUM_OF_OPS: int = 1000
mongo_tester: workloads.mongo.MongoTester = workloads.mongo.MongoTester()

mongo_tester.test_all(NUM_OF_OPS)
