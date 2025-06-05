#!/bin/bash
# PokéCertify DB Initialization Script

set -e

DB_PATH=${1:-pokecertify.db}
SCHEMA_PATH="$(dirname "$0")/../src/backend/db/schema.sql"

echo "Initializing PokéCertify database at $DB_PATH"
sqlite3 "$DB_PATH" < "$SCHEMA_PATH"
echo "Database initialized successfully."