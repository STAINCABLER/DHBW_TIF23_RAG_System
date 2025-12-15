#!/bin/bash
# =============================================================================
# pgvector Installation Script für PostgreSQL
# =============================================================================
# Dieses Script wird beim Start des postgres_pgvector_manual Containers
# ausgeführt und installiert pgvector aus den Quellen.
#
# HINWEIS: Dies demonstriert die manuelle Installation von pgvector,
# falls das offizielle pgvector-Image nicht verwendet werden kann.
# =============================================================================

set -e

echo "=========================================="
echo "Installing pgvector extension..."
echo "=========================================="

# Benötigte Pakete für die Kompilierung
apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    git \
    postgresql-server-dev-16

# pgvector Repository klonen
cd /tmp
git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git

# Kompilieren und installieren
cd pgvector
make
make install

# Aufräumen
rm -rf /tmp/pgvector
apt-get remove -y build-essential git postgresql-server-dev-16
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "=========================================="
echo "pgvector installation complete!"
echo "=========================================="
