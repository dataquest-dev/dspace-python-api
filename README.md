[![Test dspace on dev-5](https://github.com/dataquest-dev/dspace-blackbox-testing/actions/workflows/test.yml/badge.svg)](https://github.com/dataquest-dev/dspace-blackbox-testing/actions/workflows/test.yml)


# Dspace python REST API wrapper

A library by dspace is used to simplify access through python to running
dspace instance.
It contains several parts.

- [Data import](#data-import)
- [Testing running instance](#tests)

## Common requirements for all parts
- For every part (except those run in docker), requirements must be installed before running it for the first time, 
using following command
`pip install -r requirements.txt`

- Next insert correct information into `const.py`
  - `user = "<ADMIN_NAME>"`
  - `password = "<ADMIN_PASSWORD>"`
  - `use_ssl = False  # or True - http or https`
  - `host = "<YOUR_SERVER>"  # e.g., localhost or my.dspace.com`
  - `fe_port = "<YOUR_FE_PORT>"  # or None`
  - `be_port = "<YOUR_BE_PORT>"  # or None`
  - `be_location = "<SERVER_SUBPATH>"  # e.g. /server/`
  

# Data import
How to migrate CLARIN-DSpace5.* to CLARIN-DSpace7.*

Please note [Migration notes](##migration-notes:) section.

## Import data using docker
This is the simplest set of instructions. It requires
- docker
- [Fresh installation of dspace 7](#installation)
- [Clear database (with only admin account)](#clear-database)
- [Access to original database (postgres server) from which to import database](#no-access-to-original-database,-only-sql-dump)

If you lack any of these, please click and follow instructions. Then return here.

1. Clone this project https://github.com/dataquest-dev/dspace-python-api (branch `main`)
2. Update `const.py` as specified above with connection details to running dspace instance
to which you want to import
3. Update `import_db_const.py` with connection details to database server(s). This is 
specific for clarin-5. First one is database usually marked as `clarin-dspace` and second
is usually `clarin-utilities`. Set `perform-import` to True (if it isn't already).
4. Copy assetstore from dspace5 to installed dspace 7. If installation folder is `/dspace/`
then copy assetstore folder to `/dspace/assetstore`.
5. Run docker from downloaded repository root in step 1 as 

   `docker build -t dspace-import . && docker run --name dspace-import-instance dspace-import `

## Installation
Installing clarin 7

# I dont think this belongs here, install according to [official](https://wiki.lyrasis.org/display/DSDOC7x/Installing+DSpace) or from [clarin wiki](https://github.com/ufal/clarin-dspace/wiki/Migration-to-DSpace7.2.1.)

1. Clone repository //https://github.com/dataquest-dev/DSpace (branch dtq-dev)
   
   repository contains [readme](https://github.com/dataquest-dev/DSpace/blob/dtq-dev/README.md) 
   with instructions, but you can follow these:
2. Create database either by [official tutorial steps](https://wiki.lyrasis.org/display/DSDOC7x/Installing+DSpace#InstallingDSpace-PostgreSQL11.x,12.xor13.x(withpgcryptoinstalled))
or try these. Note, you have to have Postgres installed.
   1. Go to `<PSQL_PATH>/bin`
   2. Issue commands:
      - `createdb --username=postgres --owner=dspace --encoding=UNICODE dspace` // create database
      - `psql --username=postgres dspace -c "CREATE EXTENSION pgcrypto;"` // Add pgcrypto extension
        - If it throws warning that `-c` parameter was ignored, just write a `CREATE EXTENSION pgcrypto;` command in the database cmd. 
        CREATE EXTENSION pgcrypto;
        ![image](https://user-images.githubusercontent.com/90026355/228528044-f6ad178c-f525-4b15-b6cc-03d8d94c8ccc.png)
   3. Now the clarin database for Dspace7 shoudl be created, run the database by command
 `pg_ctl start -D "<PSQL_PATH>\data\"`
3. If all went right, now there is dspace installed. It needs web server to be deployed, which you need to start.
If you have no idea what that means, please check 
 

## Clear database

to be added

## No access to original database, only sql dump
to be added

# OLD MANUAL ===start=== 

### Prerequisites:
- Installed CLARIN-DSpace7.*. with running and empty database, solr, tomcat

### Steps (including installation of dspace -7):
1. Clone python-api: https://github.com/dataquest-dev/dspace-python-api (branch `main`) and dpace://https://github.com/dataquest-dev/DSpace (branch `dtq-dev`)

***
2. Get database dump (old CLARIN-DSpace) and unzip it into the `<PSQL_PATH>/bin` (or wherever you want)

***
3. Create CLARIN-DSpace5.* databases (dspace, utilities) from dump.
> // clarin-dspace database
> - `createdb --username=postgres --owner=dspace --encoding=UNICODE clarin-dspace` // create a clarin database with owner

> // It runs on second try:
> - `psql -U postgres clarin-dspace < <CLARIN_DUMP_FILE_PATH>`

> // clarin-utilities database
> - `createdb --username=postgres --owner=dspace --encoding=UNICODE clarin-utilities` // create a utilities database with owner

> // It runs on second try:
> - `psql -U postgres clarin-utilities < <UTILITIES_DUMP_FILE_PATH>`

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
7. Prepare `dspace-python-api` project for migration
**IMPORTANT:** If `data` folder doesn't exist in the project, create it

Update `const.py` as specified near top of this file

***
8. Create JSON files from the database tables. **NOTE: You must do it for both databases `clarin-dspace` and `clarin-utilities`** (JSON files are stored in the `data` folder)
- Go to `dspace-python-api` in the cmd
- Run `pip install -r requirements.txt`
- Run `python data_migration.py <DATABSE NAME> <HOST> postgres <PASSWORD FOR POSTGRES>` e.g., `python data_migration.py clarin-dspace localhost postgres pass` (arguments for database connection - database, host, user, password) for the BOTH databases // NOTE there must exist data folder in the project structure

***
9. Copy `assetstore` from dspace5 to dspace7 (for bitstream import). `assetstore` is in the folder where you have installed DSpace `dspace/assetstore`.

***
10. Import data from the json files (python-api/data/*) into dspace database (CLARIN-DSpace7.*)
- **NOTE:** database must be up to date (`dspace database migrate force` must be called in the `dspace/bin`)
- **NOTE:** dspace server must be running
- From the `dspace-python-api` run command `python dspace_import.py`

***


# OLD MANUAL ===end===

## Migration notes:
- The values of table attributes that describe the last modification time of dspace object (for example attribute `last_modified` in table `Item`) have a value that represents the time when that object was migrated and not the value from migrated database dump.

# Tests

In order to run tests, use command
`python -m unittest`

Recommended variation is
`python -m unittest -v 2> output.txt`
which leaves result in output.txt

It is possible to run in Pycharm with configuration like so:


## How to write new tests
Check test.example package. Everything necessary should be there.

Test data are in `test/data` folder.
If your test data contains special characters like čřšáý and so on, it is recommended
to make `.stripped` variation of the file. 
E.g. `my_format.json` and `my_format.stripped.json` for loading data
and `my_format.test.xml` and `my_format.test.stripped.xml` for testing.

If not on dev-5 (e.g. when run on localhost), `.stripped` version of files will be loaded.
The reason for this is, that when dspace runs on windows, it has trouble with special characters.


## Settings
See const.py for constants used at testing.

To set up logs, navigate to support.logs.py and modify method set_up_logging.



![image](https://user-images.githubusercontent.com/88670521/186934112-d0f828fd-a809-4ed8-bbfd-4457b734d8fd.png)
