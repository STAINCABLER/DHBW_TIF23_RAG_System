"""
RAG-System Datenbank Performance Tests - Test Module
=====================================================

Dieses Paket enthält alle datenbankspezifischen Performance-Tests.

Module:
    - base_test: Abstrakte Basisklasse mit gemeinsamer Test-Logik
    - redis_tests: Redis Key-Value Store Tests
    - mongo_tests: MongoDB Document Store Tests
    - postgres_tests: PostgreSQL Relationale Tests
    - vector_tests: Vektorsuche Tests (pgvector & MongoDB)

Jedes Modul implementiert sowohl synchrone als auch asynchrone Tests,
um verschiedene Concurrency-Szenarien abzudecken.
"""

from db_tests.base_test import BasePerformanceTest
from db_tests.redis_tests import RedisPerformanceTest
from db_tests.mongo_tests import MongoPerformanceTest
from db_tests.postgres_tests import PostgresPerformanceTest
from db_tests.vector_tests import VectorPerformanceTest

__all__ = [
    "BasePerformanceTest",
    "RedisPerformanceTest",
    "MongoPerformanceTest",
    "PostgresPerformanceTest",
    "VectorPerformanceTest",
]
