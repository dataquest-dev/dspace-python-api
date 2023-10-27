#!/bin/bash
/usr/local/bin/docker-entrypoint.sh postgres &
sleep 5

createuser --username=postgres dspace

echo "Importing clarin-dspace"
createdb --username=postgres --owner=dspace --encoding=UNICODE clarin-dspace
psql -U postgres clarin-dspace < ../dump/clarin-dspace-8.8.23.sql

echo "Importing clarin-utilities"
createdb --username=postgres --encoding=UNICODE clarin-utilities
psql -U postgres clarin-utilities < ../dump/clarin-utilities-8.8.23.sql

psql -U postgres