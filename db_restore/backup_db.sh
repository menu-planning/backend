#!/bin/bash

# Variables
DB_USER="mp_admin"
DB_HOST="menu-planning-freetier-dev.cjusqw0ysi8o.sa-east-1.rds.amazonaws.com"
DB_PORT="5432"
DB_NAME="mp_freetier_dev"
BACKUP_FILE="db.backup.set.24.2025"

# pg_dump -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -F c -f $BACKUP_FILE
pg_dump -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_NAME --data-only --no-owner --file=data.sql

echo "Database backup completed successfully."