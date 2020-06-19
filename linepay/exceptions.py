# -*- coding: utf-8 -*-


class BaseError(Exception):
    """Base Exception class."""

    def __init__(self, message='-'):
        """__init__ method.

        :param str message: Human readable message
        """
        self.message = message

    def __repr__(self):
        """repr."""
        return str(self)

    def __str__(self):
        """str.

        :rtype: str
        """
        return '<{0} [{1}]>'.format(
            self.__class__.__name__, self.message)


class InvalidSignatureError(BaseError):
    """When Webhook signature does NOT match, this error will be raised."""

    def __init__(self, message='-'):
        """__init__ method.

        :param str message: Human readable message
        """
        super(InvalidSignatureError, self).__init__(message)


class LinePayApiError(BaseError):
    """When LINE Pay API response error, this error will be raised."""

    def __init__(self, return_code, status_code, headers, api_response):
        """__init__ method.

        :param str return_code:  API Return code
        :param int status_code: HTTP status code
        :param headers: Response headers
        :type headers: dict[str, str]
        :param dict api_response: API response json
        """
        super(LinePayApiError, self).__init__(
            api_response.get("returnMessage"))

        self.return_code = return_code
        self.status_code = status_code
        self.headers = headers
        self.api_response = api_response

    def __str__(self):
        """str.

        :rtype: str
        """
        return '{0}: return_code={1}, http_status_code={2}, api_response={3}, http_headers={4}'.format(
            self.__class__.__name__, self.return_code, self.status_code, self.api_response, self.headers)
