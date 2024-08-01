#!/bin/bash

# Variables
DB_USER="mp_admin"
DB_HOST="menu-planning-freetier-db.cjusqw0ysi8o.sa-east-1.rds.amazonaws.com"
DB_PORT="5432"
DB_NAME="mp_freetier"
BACKUP_FILE="db.backup"

# Restore the schema and data with triggers disabled
# pg_restore -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME --no-owner --role=mp_admin --clean --if-exists --disable-triggers --schema-only $BACKUP_FILE
# pg_restore -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME --no-owner --role=mp_admin --disable-triggers --data-only $BACKUP_FILE
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -f data.sql

echo "Database restore completed successfully with triggers disabled."