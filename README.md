[![Test dspace on dev-5](https://github.com/dataquest-dev/dspace-blackbox-testing/actions/workflows/test.yml/badge.svg)](https://github.com/dataquest-dev/dspace-blackbox-testing/actions/workflows/test.yml)

# Dspace-python-api
used for blackbox testing, data-ingestion procedures

# How to migrate CLARIN-DSpace5.* to CLARIN-DSpace7.*

### Important:
Make sure that your email server is NOT running because some of the endpoints that are used
are sending emails to the input email addresses. 
For example, when using the endpoint for creating new registration data, 
there exists automatic function that sends email, what we don't want
because we use this endpoint for importing existing data.

### Prerequisites:
- Installed CLARIN-DSpace7.*. with running database, solr, tomcat

### Steps:
1. Clone python-api: https://github.com/dataquest-dev/dspace-python-api (branch `main`) and https://github.com/dataquest-dev/DSpace (branch `dtq-dev`)

***
2. Get database dump (old CLARIN-DSpace) and unzip it into the `<PSQL_PATH>/bin` (or wherever you want)

***
3. Create CLARIN-DSpace5.* databases (dspace, utilities) from dump.
> // clarin-dspace database
> - `createdb --username=postgres --owner=dspace --encoding=UNICODE clarin-dspace` // create a clarin database with owner

> // Running on second try:
> - `psql -U postgres clarin-dspace < <CLARIN_DUMP_FILE_PATH>`

> // clarin-utilities database
> - `createdb --username=postgres --owner=dspace --encoding=UNICODE clarin-utilities` // create the utilities database with owner

> // Running on second try:
> - `psql -U postgres clarin-utilities < <UTILITIES_DUMP_FILE_PATH>`

or use `scripts/start.local.dspace.db.bat`.
NOTE: `start.local.dspace.db.bat` and `init.dspacedb5.sh` must have `LF` line separator.

***
4. Recreate your local CLARIN-DSpace7.* database **NOTE: all data will be deleted**
- Install again the database following the official tutorial steps: https://wiki.lyrasis.org/display/DSDOC7x/Installing+DSpace#InstallingDSpace-PostgreSQL11.x,12.xor13.x(withpgcryptoinstalled)
- Or try to run these commands in the <PSQL_PATH>/bin:
> - `createdb --username=postgres --owner=dspace --encoding=UNICODE dspace` // create database
> - `psql --username=postgres dspace -c "CREATE EXTENSION pgcrypto;"` // Add pgcrypto extension
> > If it throws warning that `-c` parameter was ignored, just write a `CREATE EXTENSION pgcrypto;` command in the database cmd.
> > CREATE EXTENSION pgcrypto;
![image](https://user-images.githubusercontent.com/90026355/228528044-f6ad178c-f525-4b15-b6cc-03d8d94c8ccc.png)
 

> // Now the clarin database for DSpace7 should be created
> - Run the database by the command: `pg_ctl start -D "<PSQL_PATH>\data\"`

***
5. (Your DSpace project must be installed) Go to the `dspace/bin` and run the command `dspace database migrate force` // force because of local types
**NOTE:** `dspace database migrate force` creates default database data that may be not in database dump, so after migration, some tables may have more data than the database dump. Data from database dump that already exists in database is not migrated.

***
6. Create an admin by running the command `dspace create-administrator` in the `dspace/bin`

***
7. Create JSON files from the database tables. 
**NOTE: You must do it for both databases `clarin-dspace` and `clarin-utilities`** (JSON files are stored in the `data` folder)
- Go to `dspace-python-api` in the cmd
- Run `pip install -r requirements.txt` (maybe, `apt install libpq-dev` is needed)
- Run  e.g., `python db_to_json.py --database=clarin-dspace`

***
8. Prepare `dspace-python-api` project for migration

- create `input/` directory and copy all the files that are used for migration
```
> ls -R ./input
input:
data dump  icon

input/data:
bitstream.json                   fileextension.json                    piwik_report.json
bitstreamformatregistry.json     ...

input/dump:
clarin-dspace-8.8.23.sql  clarin-utilities-8.8.23.sql

input/icon:
aca.png  by.png  gplv2.png  mit.png    ...
```
- update `project_settings.py`

***
9. Make sure, your backend configuration (`dspace.cfg`) includes all handle prefixes from generated handle json in property `handle.additional.prefixes`, 
e.g.,`handle.additional.prefixes = 11858, 11234, 11372, 11346, 20.500.12801, 20.500.12800`

***
10. Copy `assetstore` from dspace5 to dspace7 (for bitstream import). `assetstore` is in the folder where you have installed DSpace `dspace/assetstore`.

***
11. Import data from the json files (python-api/data/*) into dspace database (CLARIN-DSpace7.*)
- **NOTE:** database must be up to date (`dspace database migrate force` must be called in the `dspace/bin`)
- **NOTE:** dspace server must be running
- run command `cd ./src && python repo_import.py`

***
## !!!Migration notes:!!!
- The values of table attributes that describe the last modification time of dspace object (for example attribute `last_modified` in table `Item`) have a value that represents the time when that object was migrated and not the value from migrated database dump.
- If you don't have valid and complete data, not all data will be imported.
