"""
Docker Manager - Steuerung der Docker Compose Infrastruktur
============================================================

Dieses Modul steuert den Lifecycle der Docker-Container für die Tests.

Funktionalität:
    - Container starten (docker compose up)
    - Container stoppen und aufräumen (docker compose down -v)
    - Health-Checks für alle Datenbanken
    - Timeout-Handling bei Startup-Problemen

Modul-Referenz:
    - Anforderungen 1.2: Automatisierung & Lifecycle
    - Anforderungen 5.2: Docker-Management

Autor: RAG Performance Test Suite
"""

import subprocess
import time
import logging
from pathlib import Path
from typing import Optional
import yaml

# Logger für dieses Modul
logger = logging.getLogger(__name__)


class DockerManager:
    """
    Verwaltet Docker Compose Container für die Performance-Tests.
    
    Diese Klasse ist verantwortlich für:
    - Das Starten aller Datenbank-Container vor den Tests
    - Das Warten auf die Verfügbarkeit der Datenbanken
    - Das Aufräumen nach den Tests (auch bei Fehlern)
    
    Beispiel:
        manager = DockerManager(config)
        try:
            manager.start_containers()
            # ... Tests ausführen ...
        finally:
            manager.stop_containers()
    """
    
    def __init__(self, config: dict, base_path: Optional[Path] = None):
        """
        Initialisiert den Docker Manager.
        
        Args:
            config: Die geladene Konfiguration aus test_config.yaml
            base_path: Basisverzeichnis für relative Pfade (Standard: tests/)
        """
        self.config = config
        self.base_path = base_path or Path(__file__).parent.parent
        
        # Docker Compose Konfiguration
        docker_config = config.get("docker", {})
        self.compose_file = self.base_path / docker_config.get(
            "compose_file", "docker/docker-compose.yml"
        )
        self.startup_wait = docker_config.get("startup_wait_seconds", 15)
        self.timeout = docker_config.get("timeout_seconds", 120)
        
        # Status-Tracking
        self._containers_running = False
    
    def start_containers(self, services: Optional[list[str]] = None) -> bool:
        """
        Startet die Docker Container.
        
        Args:
            services: Optional - Liste spezifischer Services zum Starten.
                      Wenn None, werden alle Services gestartet.
        
        Returns:
            True wenn erfolgreich, False bei Fehlern.
        
        Raises:
            RuntimeError: Wenn Docker Compose fehlschlägt.
        """
        logger.info("=" * 60)
        logger.info("Starte Docker Container...")
        logger.info("=" * 60)
        
        # Prüfe ob Docker Compose Datei existiert
        if not self.compose_file.exists():
            raise FileNotFoundError(
                f"Docker Compose Datei nicht gefunden: {self.compose_file}"
            )
        
        # Docker Compose Befehl zusammenbauen
        cmd = [
            "docker", "compose",
            "-f", str(self.compose_file),
            "up", "-d",
            "--wait",  # Wartet auf Health-Checks
        ]
        
        # Spezifische Services hinzufügen
        if services:
            cmd.extend(services)
        
        try:
            logger.info(f"Führe aus: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.error(f"Docker Compose Fehler: {result.stderr}")
                raise RuntimeError(f"Docker Compose fehlgeschlagen: {result.stderr}")
            
            logger.info("Container gestartet, warte auf Initialisierung...")
            
            # Zusätzliche Wartezeit für DB-Initialisierung
            time.sleep(self.startup_wait)
            
            self._containers_running = True
            logger.info("✓ Alle Container sind bereit!")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout beim Starten der Container ({self.timeout}s)")
            self.stop_containers()
            raise RuntimeError("Container-Start Timeout")
        
        except Exception as e:
            logger.error(f"Fehler beim Starten der Container: {e}")
            self.stop_containers()
            raise
    
    def stop_containers(self, remove_volumes: bool = True) -> bool:
        """
        Stoppt und entfernt die Docker Container.
        
        Args:
            remove_volumes: Wenn True, werden auch Volumes gelöscht (Standard).
                           Dies verhindert Seiteneffekte zwischen Testläufen.
        
        Returns:
            True wenn erfolgreich, False bei Fehlern.
        """
        logger.info("=" * 60)
        logger.info("Stoppe Docker Container...")
        logger.info("=" * 60)
        
        cmd = [
            "docker", "compose",
            "-f", str(self.compose_file),
            "down",
        ]
        
        if remove_volumes:
            cmd.append("-v")  # Volumes löschen
            cmd.append("--remove-orphans")  # Verwaiste Container entfernen
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.base_path
            )
            
            if result.returncode != 0:
                logger.warning(f"Warnung beim Stoppen: {result.stderr}")
            else:
                logger.info("✓ Alle Container gestoppt und aufgeräumt!")
            
            self._containers_running = False
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Container: {e}")
            return False
    
    def get_container_status(self) -> dict:
        """
        Gibt den Status aller Container zurück.
        
        Returns:
            Dictionary mit Container-Namen und deren Status.
        """
        cmd = [
            "docker", "compose",
            "-f", str(self.compose_file),
            "ps", "--format", "json"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                import json
                # Docker Compose gibt JSON-Lines aus
                containers = {}
                for line in result.stdout.strip().split("\n"):
                    if line:
                        data = json.loads(line)
                        containers[data.get("Name", "unknown")] = {
                            "status": data.get("State", "unknown"),
                            "health": data.get("Health", "N/A"),
                            "ports": data.get("Ports", "")
                        }
                return containers
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Container-Status: {e}")
        
        return {}
    
    def is_running(self) -> bool:
        """Prüft ob die Container laufen."""
        return self._containers_running
    
    def __enter__(self):
        """Context Manager: Startet Container."""
        self.start_containers()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager: Stoppt Container (auch bei Exceptions)."""
        self.stop_containers()
        return False  # Exceptions nicht unterdrücken
