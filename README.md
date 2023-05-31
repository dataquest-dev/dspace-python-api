[![Test dspace on dev-5](https://github.com/dataquest-dev/dspace-blackbox-testing/actions/workflows/test.yml/badge.svg)](https://github.com/dataquest-dev/dspace-blackbox-testing/actions/workflows/test.yml)


# Dspace python REST API wrapper

A library by dspace is used to simplify access through python to running
[dspace](https://github.com/dataquest-dev/DSpace) instance.
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
- [Copied appropriate assetstore](#copying-assetstore)

If you lack any of these, please click and follow instructions. Then return here.

1. Clone this project https://github.com/dataquest-dev/dspace-python-api (branch `main`)
2. Update `const.py` as specified above with connection details to running dspace instance
to which you want to import
3. Update `import_db_const.py` with connection details to database server(s). This is 
specific for clarin-5. First one is database usually marked as `clarin-dspace` and second
is usually `clarin-utilities`. Set `perform-import` to True (if it isn't already).
4. Copy assetstore from dspace5 to installed dspace 7. If installation folder is `/dspace/`
then copy assetstore folder to `/dspace/assetstore`.
   - if copying assetstore to docker use `docker cp assetstore dspace:/dspace/`
     - first argument to `docker cp` which is `assetstore` is local folder of assetstore, which you obviously need prepared
     - second argument `dspace:/dspace/` denotes container `dspace` and within it path `/dspace/` since that is where assetsotre resides
5. Run docker from downloaded repository root in step 1 as 

   `docker build -t dspace_import . && docker run --name dspacedataimport dspace_import`

## Installation
Installing clarin 7

install according to [official](https://wiki.lyrasis.org/display/DSDOC7x/Installing+DSpace) or from [clarin wiki](https://github.com/ufal/clarin-dspace/wiki/Migration-to-DSpace7.2.1.)

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


## Clear database

**NOTE: all data will be deleted**

- Install again the database following the official tutorial steps: https://wiki.lyrasis.org/display/DSDOC7x/Installing+DSpace#InstallingDSpace-PostgreSQL11.x,12.xor13.x(withpgcryptoinstalled)
- Or try to run these commands in the <PSQL_PATH>/bin:
  - `dropdb --username=postgres mydb` // drop old database
  - `createdb --username=postgres --owner=dspace --encoding=UNICODE dspace` // create database
  - `psql --username=postgres -c "CREATE EXTENSION pgcrypto;" dspace ` // Add pgcrypto extension
    > If there is warinng that `-c` parameter was ignored, just write a `CREATE EXTENSION pgcrypto;` command in the database cmd.
    > CREATE EXTENSION pgcrypto;
![image](https://user-images.githubusercontent.com/90026355/228528044-f6ad178c-f525-4b15-b6cc-03d8d94c8ccc.png)
  - Now the clarin database for DSpace7 should be created
  - Run the database by the command: `pg_ctl start -D "<PSQL_PATH>\data\"`

- Create an admin by running the command `dspace create-administrator` in the `dspace/bin`

## No access to original database, only sql dump
not currently supported

## Copying assetstore
Folder `assetstore` contains files, that are shown in dspace. They are not imported
through sql or othervise, they must be manually copied to your running dspace instance.
It is therefore important to first obtain "old" assetstore from the dspace, from which
you are importing.

If you are running dspace in docker, use

`docker cp path/to/assetstore dspace:/dspace/assetstore`

assuming installation location is `/dspace` inside container named `dspace`

If you are not running dspace in docker, very similarly copy folder `assetstore` to 
location `/dspace/assetstore`.

## Migration notes:
- The values of table attributes that describe the last modification time of dspace object (for example attribute `last_modified` in table `Item`) have a value that represents the time when that object was migrated and not the value from migrated database dump.
- If you are interested in logs from import, that were running in docker container,
they can be obtained by issuing 
  - `docker cp dspacedataimport:/pyimport/logs.txt localfile.txt` for logs
  - `docker cp dspacedataimport:/pyimport/debug.log.txt localfile.txt` for debug logs
- Docker version does not work, if run on the same machine AND the dspace backend is
part of docker-compose project. Please run importer from another machine. (this might
be fixed in the future)


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
If your test data contains special characters like `čřšáý` and so on, it is recommended
to make `.stripped` variation of the file. 
E.g. `my_format.json` and `my_format.stripped.json` for loading data
and `my_format.test.xml` and `my_format.test.stripped.xml` for testing.

If not on dev-5 (e.g. when run on localhost), `.stripped` version of files will be loaded.
The reason for this is, that when dspace runs on windows, it has trouble with special characters.


## Settings
See const.py for constants used at testing.

To set up logs, navigate to support.logs.py and modify method set_up_logging.



![image](https://user-images.githubusercontent.com/88670521/186934112-d0f828fd-a809-4ed8-bbfd-4457b734d8fd.png)
