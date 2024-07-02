# Import check

1. Get database dumps and unzip them into `input/dump`, rename to `dspace6.sql` and `dspace7.sql` accordingly.
 
1. Create `dspace6` and `dspace7` databases from dump:
```
> scripts/start.dspace.db.bat
Starting postgres
Importing dspace6
Importing dspace7
Done, starting psql
Waiting for PID:7 /usr/local/bin/docker-entrypoint.sh
```

1. Add settings to `diff_settings`, see [settings](diff_settings/tul.py). 

1. Compare dspace databases:
```
python diff.py --use=tul
```