#!/bin/bash

# Variables
DB_USER="user-dev"
DB_HOST="localhost"
DB_PORT="54321"
DB_NAME="appdb-dev"
BACKUP_FILE="db.backup"

# pg_dump -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -F c -f $BACKUP_FILE
pg_dump -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME --data-only --no-owner --file=data.sql

echo "Database backup completed successfully."