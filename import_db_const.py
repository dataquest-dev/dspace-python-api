# access to clarin-5 database for import purposes. NEVER push this file to git (or anywhere) with your actual password!
import sys

from support.logs import log, Severity

perform_import = False
database_name1 = "clarin-dspace"
database_name2 = "clarin-utilities"
host1 = "localhost"
host2 = "localhost"
user1 = "postgres"  # admin user
# user2 = "postgres"  # admin user
# use None to avoid connecting, so when user2 = None, dump will not be performed with user2(on database_name2, host2..)
user2 = None  # admin user
password1 = "admins_password"
password2 = "admins_password"

if len(sys.argv) > 1:
    if sys.argv[1] == 'docker':
        if host1 == 'localhost':
            log("Changed value of host1 from localhost to host.docker.internal", Severity.DEBUG)
            host1 = 'host.docker.internal'
        if host2 == 'localhost':
            log("Changed of host2 from localhost to host.docker.internal", Severity.DEBUG)
            host2 = 'host.docker.internal'
