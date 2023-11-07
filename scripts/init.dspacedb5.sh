#!/bin/bash
echo "Starting postgres"
/usr/local/bin/docker-entrypoint.sh postgres &> ./postgres.log &
PID=$!
sleep 3

createuser --username=postgres dspace

echo "Importing clarin-dspace"
createdb --username=postgres --owner=dspace --encoding=UNICODE clarin-dspace
psql -U postgres clarin-dspace < ../dump/clarin-dspace-8.8.23.sql &> /dev/null

echo "Importing clarin-utilities"
createdb --username=postgres --encoding=UNICODE clarin-utilities
psql -U postgres clarin-utilities < ../dump/clarin-utilities-8.8.23.sql &> /dev/null

echo "Done, starting psql"

# psql -U postgres
echo "Waiting for PID:$PID /usr/local/bin/docker-entrypoint.sh"
wait $PID