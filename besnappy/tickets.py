""" Utilities for sending to Snappy HTTP API.
"""
import json
import requests

class SnappyApiSender(object):
    """
    A helper for managing support tickets via Snappy's HTTP API.
    Full documentation: https://github.com/BeSnappy/api-docs

    :param str api_key:
        The secret authentication token found in You -> Your Setting
        -> Security
    :param str api_url:
        The full URL of the HTTP API. Defaults to
        ``https://app.besnappy.com/api/v1``.
    :type session:
        :class:`requests.Session`
    :param session:
        Requests session to use for HTTP requests. Defaults to
        a new session.
    """

    def __init__(self, api_key, api_url=None, session=None):
        self.api_key = api_key
        if api_url is None:
            api_url = "https://app.besnappy.com/api/v1"
        self.api_url = api_url
        if session is None:
             session = requests.Session()
        self.session = session

    def _api_request(self, method, endpoint, py_data=None):
        url = "%s/%s" % (self.api_url, endpoint)
        headers = {'content-type': 'application/json; charset=utf-8'}
        auth = (self.api_key, "x")
        if method is "POST":
            data = json.dumps(py_data)
            r = requests.post(url, auth=auth, data=data, headers=headers, verify=False)
        elif method is "GET":
            if py_data is not None:
                r = self.session.get(url, auth=auth, params=data, headers=headers, verify=False)
            else:
                r = self.session.get(url, auth=auth, headers=headers, verify=False)
        r.raise_for_status()
        # return whole response because some calls are just single text response not json
        return r

    def note(self, mailbox_id, subject, message, to_addr=None, from_addr=None, **kwargs):
        """ Send a note to a mailbox. Needs a to or from.

        :param int mailbox_id:
            Mailbox to send to.
        :param str subject:
            Subject of ticket.
        :param str message:
            Message to send.
        :param dict to_addr:
            name and address (optional)
        :param dict from_addr:
            name and address (optional)
        """
        data = {
            "mailbox_id": mailbox_id,
            "subject": subject,
            "message": message,
        }
        if to_addr is not None:
            data["to"] = to_addr
        if from_addr is not None:
            data["from"] = from_addr
        response = self._api_request('POST', 'note', data)
        return response.text
