#!/bin/bash
echo "Starting postgres"
/usr/local/bin/docker-entrypoint.sh postgres &> ./__postgres.log &
PID=$!
sleep 3

createuser --username=postgres dspace

echo "Importing dspace6"
createdb --username=postgres --owner=dspace --encoding=UNICODE dspace6
psql -U postgres dspace6 < ../dump/dspace6_27.7.23.sql &> /dev/null
psql -U postgres dspace6 < ../dump/dspace6_27.7.23.sql &> ./__dspace6.log

echo "Importing dspace7"
createdb --username=postgres --encoding=UNICODE dspace7
psql -U postgres dspace7 < ../dump/dspace7_20.6.24.sql &> /dev/null
psql -U postgres dspace7 < ../dump/dspace7_20.6.24.sql &> ./__dspace7.log

echo "Done, starting psql"

# psql -U postgres
echo "Waiting for PID:$PID /usr/local/bin/docker-entrypoint.sh"
wait $PID