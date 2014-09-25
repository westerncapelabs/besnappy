""" Utilities for sending to Snappy HTTP API.
"""
import json
from requests import Session


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
            session = Session()
        self.session = session

    def _api_request(self, method, endpoint, py_data=None):
        url = "%s/%s" % (self.api_url, endpoint)
        headers = {'content-type': 'application/json; charset=utf-8'}
        auth = (self.api_key, "x")
        if method is "POST":
            data = json.dumps(py_data)
            r = self.session.post(
                url, auth=auth, data=data, headers=headers, verify=False)
        elif method is "GET":
            if py_data is not None:
                r = self.session.get(
                    url, auth=auth, params=data, headers=headers, verify=False)
            else:
                r = self.session.get(
                    url, auth=auth, headers=headers, verify=False)
        r.raise_for_status()
        # return whole response because some calls are just single text
        # response not json
        return r

    def get_accounts(self):
        """
        List accounts available.

        :returns:
            List of account dicts.
        """
        response = self._api_request('GET', 'accounts')
        return response.json()

    def get_mailboxes(self, account_id):
        """
        List mailboxes in account.

        :param int account_id:
            Account identifier.

        :returns:
            List of mailbox dicts.
        """
        response = self._api_request(
            'GET', 'account/%s/mailboxes' % (account_id,))
        return response.json()

    def get_staff(self, account_id):
        """
        List staff in account.

        :param int account_id:
            Account identifier.

        :returns:
            List of staff dicts.
        """
        response = self._api_request(
            'GET', 'account/%s/staff' % (account_id,))
        return response.json()

    def create_note(self, mailbox_id, subject, message, ticket_id=None,
                    to_addr=None, from_addr=None, staff_id=None, scope=None):
        """
        Create a new note on a new or existing ticket.

        Either ``from_addr`` or both ``to_addr`` and ``staff_id`` must be
        specified.

        :param int mailbox_id:
            Mailbox to send to.
        :param str subject:
            Subject of ticket.
        :param str message:
            Message to send.
        :param ticket_id:
            Optional ticket identifier. If not provided, a new ticket will be
            created.
        :param dict to_addr:
            name and address (optional) (TODO: document format)
        :param dict from_addr:
            name and address (optional) (TODO: document format)
        :param int staff_id:
            Staff identifier
        :param str scope:
            Set to `"private"` for a private note. (TODO: document othe values)

        :returns:
            Ticket identifier.
        """
        data = {
            "mailbox_id": mailbox_id,
            "subject": subject,
            "message": message,
        }
        if ticket_id is not None:
            data["id"] = ticket_id
        if to_addr is not None:
            data["to"] = to_addr
        if from_addr is not None:
            data["from"] = from_addr
        if staff_id is not None:
            data["staff_id"] = staff_id
        if scope is not None:
            data["scope"] = scope
        response = self._api_request('POST', 'note', data)
        return response.text

    def get_ticket_notes(self, ticket_id):
        """
        Get notes attached to the specified ticket.

        :param ticket_id:
            Ticket to get notes from.

        :returns:
            List of ticket note dicts.
        """
        response = self._api_request('GET', 'ticket/%s/notes/' % (ticket_id,))
        return response.json()
