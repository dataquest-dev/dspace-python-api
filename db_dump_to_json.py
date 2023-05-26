import os

import psycopg2
import json

from support.logs import Severity, log


def get_data_as_json(database, host, db_user, db_password):
    if db_user is None:
        log("Not dumping database, because db_user is None", Severity.DEBUG)
        return
    # create database connection
    conn = psycopg2.connect(database=database,
                            host=host,
                            user=db_user,
                            password=db_password)
    log("Connection was successful!", Severity.TRACE)

    cursor = conn.cursor()
    cursor.execute(
        "SELECT table_name FROM information_schema.tables WHERE is_insertable_into = 'YES' AND table_schema = 'public'")
    # list of tuples
    table_name = cursor.fetchall()
    log("Processing...", Severity.TRACE)
    for name_t in table_name:
        # access to 0. position, because name_t is tuple
        name = name_t[0]
        os.makedirs("data/", exist_ok=True)
        fp_name = 'data/' + name + '.json'
        fp = open(fp_name, 'w')
        cursor.execute("SELECT json_agg(row_to_json(t)) FROM {} t".format(name))
        # access to 0. position, because the fetchone returns tuple
        fp.write((json.dumps(cursor.fetchone()[0])))
        fp.close()
        log("wrote to file", fp_name)
    log("Data was successfully exported!")
    conn.close()
    log("Disconnect from database!", Severity.TRACE)
