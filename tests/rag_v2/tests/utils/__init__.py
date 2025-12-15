"""
RAG-System Datenbank Performance Tests - Utility Module
========================================================

Dieses Paket enthält Hilfsfunktionen und -klassen für die Tests.

Module:
    - docker_manager: Docker Compose Steuerung (Start/Stop Container)
    - data_generator: Generierung realistischer Testdaten
    - metrics: Berechnung von Performance-Metriken (P95, P99, etc.)
    - report_generator: Erstellung des Markdown-Reports
"""

from .docker_manager import DockerManager
from .data_generator import DataGenerator
from .metrics import MetricsCalculator
from .report_generator import ReportGenerator

__all__ = [
    "DockerManager",
    "DataGenerator",
    "MetricsCalculator",
    "ReportGenerator",
]
