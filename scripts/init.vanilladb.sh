#!/bin/bash
echo "Starting postgres"
/usr/local/bin/docker-entrypoint.sh postgres &> ./__postgres.log &
PID=$!
sleep 3

createuser --username=postgres dspace

echo "Importing vanilla-6"
createdb --username=postgres --owner=dspace --encoding=UNICODE vanilla-6
psql -U postgres vanilla-6 < ../dump/vanilla_6.sql &> /dev/null
psql -U postgres vanilla-6 < ../dump/vanilla_6.sql &> ./__vanilla-6.log

echo "Importing tul-7"
createdb --username=postgres --encoding=UNICODE tul-7
psql -U postgres vanilla-7 < ../dump/vanilla-7.sql &> /dev/null
psql -U postgres vanilla-7 < ../dump/vanilla-7.sql &> ./__vanilla-7.log

echo "Done, starting psql"

# psql -U postgres
echo "Waiting for PID:$PID /usr/local/bin/docker-entrypoint.sh"
wait $PID