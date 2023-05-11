import threading
import time

import const
from support.dspace_interface.client import DSpaceClient
from support.logs import log
from support.logs import Severity

ERROR = Severity.ERROR


class DspaceRESTProxy:
    """
    Serves as proxy to Dspace REST API.
    Mostly uses attribute d which represents (slightly modified) dspace_client from
    original python rest api by dspace developers

    PLEASE call stop_reauth() when you are finished, thanks
    """

    def __init__(self):
        self.response = None
        self.d = DSpaceClient(api_endpoint=const.API_URL, username=const.user, password=const.password)
        authenticated = self.d.authenticate()
        if not authenticated:
            log(f'Error logging in to dspace REST API at ' + const.API_URL + '! Exiting!', ERROR)
            raise ConnectionError("Cannot connect to dspace on " + const.API_URL
                                  + "!! possibly wrong username or password, please check.")
        log("Successfully logged in to dspace on " + const.API_URL)

    def reauthenticate(self):
        self.d.authenticate()

    def get(self, command, params=None, data=None):
        """
        Simple GET of url.
        param command what to append to host.xx/server/api/
        """
        url = const.API_URL + command
        self.response = self.d.api_get(url, params, data)
        return self.response

    def reauthenticate_loop(self):
        while True:
            # time.sleep(5*60)
            stopevent.wait(60)  # each minute
            if stopevent.is_set():
                log("Reauthenticate loop is over", Severity.DEBUG)
                break
            self.reauthenticate()
            log("Reauthenticating", Severity.DEBUG)


rest_proxy = DspaceRESTProxy()
reauth = threading.Thread(target=rest_proxy.reauthenticate_loop, daemon=True)
stopevent = threading.Event()
reauth.start()
def stop_reauth(wait = True):
    print("Reauth over")
    stopevent.set()
    if wait:
        reauth.join()
