"""
RAG-System Datenbank Performance Tests - Test Module
=====================================================

Dieses Paket enthält alle datenbankspezifischen Performance-Tests.

Module:
    - base_test: Abstrakte Basisklasse mit gemeinsamer Test-Logik
    
    SQL-Datenbanken:
    - postgres_tests: PostgreSQL Relationale Tests
    - mariadb_tests: MariaDB SQL Tests
    - mysql_tests: MySQL SQL Tests
    - mssql_tests: Microsoft SQL Server Tests
    
    NoSQL/Document-Datenbanken:
    - redis_tests: Redis Key-Value Store Tests
    - mongo_tests: MongoDB Document Store Tests
    - couchdb_tests: CouchDB Document Store Tests
    
    Vektor-Datenbanken:
    - vector_tests: Vektorsuche Tests (pgvector & MongoDB Atlas)

Jedes Modul implementiert sowohl synchrone als auch asynchrone Tests,
um verschiedene Concurrency-Szenarien abzudecken.
"""

from db_tests.base_test import BasePerformanceTest

# SQL-Datenbanken
from db_tests.postgres_tests import PostgresPerformanceTest
from db_tests.mariadb_tests import MariaDBPerformanceTest
from db_tests.mysql_tests import MySQLPerformanceTest
from db_tests.mssql_tests import MSSQLPerformanceTest

# NoSQL/Document-Datenbanken
from db_tests.redis_tests import RedisPerformanceTest
from db_tests.mongo_tests import MongoPerformanceTest
from db_tests.couchdb_tests import CouchDBPerformanceTest

# Vektor-Datenbanken
from db_tests.vector_tests import VectorPerformanceTest

__all__ = [
    # Base
    "BasePerformanceTest",
    # SQL
    "PostgresPerformanceTest",
    "MariaDBPerformanceTest",
    "MySQLPerformanceTest",
    "MSSQLPerformanceTest",
    # NoSQL/Document
    "RedisPerformanceTest",
    "MongoPerformanceTest",
    "CouchDBPerformanceTest",
    # Vector
    "VectorPerformanceTest",
]
