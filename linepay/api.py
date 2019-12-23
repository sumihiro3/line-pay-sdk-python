# -*- coding: utf-8 -*-

import base64
import copy
import hashlib
import hmac
import json
import requests
import uuid

from .util import validate_function, LOGGER
from .exceptions import InvalidSignatureError, LinePayApiError


class LinePayApi(object):
    """LinePayApi provides interface for LINE Pay API."""

    LINE_PAY_API_VERSION = "v3"
    DEFAULT_API_ENDPOINT = "https://api-pay.line.me"
    SANDBOX_API_ENDPOINT = "https://sandbox-api-pay.line.me"

    @validate_function
    def __init__(
        self,
        channel_id: str,
        channel_secret: str,
        is_sandbox: bool = False
    ):
        """__init__ method.
        :param str channel_id: Your channel id
        :param str channel_secret: Your channel secret
        :param bool is_sandbox: Sandbox or not
        """
        self.channel_id: str = channel_id
        self.channel_secret: str = channel_secret
        self.is_sandbox: bool = is_sandbox

        self.api_endpoint: str = self.DEFAULT_API_ENDPOINT
        if (self.is_sandbox is True):
            self.api_endpoint = self.SANDBOX_API_ENDPOINT

        self.headers: dict = {
            "X-LINE-ChannelId": self.channel_id,
            "Content-Type": "application/json"
        }

    @validate_function
    def sign(
        self,
        headers: dict,
        path: str,
        body: str
    ) -> dict:
        """generate signature method
        :param dict headers: Request HTTP Headers
        :param str path: API request path
        :param str body: API request body
        :rtpye dict: signed headers
        """
        signed_headers: dict = copy.deepcopy(headers)
        # Create nonce
        nonce: str = str(uuid.uuid4())
        signed_headers["X-LINE-Authorization-Nonce"] = nonce
        # Create HMAC Signature
        hmac_key: bytes = self.channel_secret.encode()
        hmac_text_str: str = self.channel_secret + path + body + nonce
        hmac_text_bytes: bytes = hmac_text_str.encode()
        sign = hmac.new(
            hmac_key, hmac_text_bytes, hashlib.sha256)
        signed_headers["X-LINE-Authorization"] = base64.b64encode(sign.digest()).decode()
        LOGGER.debug(signed_headers)
        return signed_headers

    @validate_function
    def request(self, options: dict) -> dict:
        """Method to Request Payment
        :param dict options: LINE Pay Request API Options see https://pay.line.me/jp/developers/apis/onlineApis?locale=ja_JP
        :rtpye dict: Request API response
        """
        path = "/{api_version}/payments/request".format(
            api_version=self.LINE_PAY_API_VERSION
        )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Request API")
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Request API Completed!")
            return result
        else:
            LOGGER.debug("Request API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

