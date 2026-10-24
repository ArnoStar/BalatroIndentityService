#!/bin/sh
# Migrates the database, then runs the command (uvicorn).
set -e
if [ "${MIGRATE_ON_START:-1}" = "1" ]; then
  alembic upgrade head
fi
exec "$@"
