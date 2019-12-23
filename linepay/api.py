# -*- coding: utf-8 -*-

import copy
import hashlib
import hmac
import json
import uuid

from .util import validate_function
from .exceptions import InvalidSignatureError


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

        self.api_endpoint: str = self.__class__.DEFAULT_API_ENDPOINT
        if (self.is_sandbox is True):
            self.api_endpoint = self.__class__.SANDBOX_API_ENDPOINT

        self.headers: dict = {
            "X-LINE-ChannelId": channel_id,
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
        nonce: str = str(uuid.uuid4())
        signed_headers["X-LINE-Authorization-Nonce"] = nonce
        hmac_key: bytes = self.channel_secret.encode("utf-8")
        hmac_text_str: str = self.channel_secret + path + body + nonce
        hmac_text_bytes: bytes = hmac_text_str.encode("utf-8")
        signature: str = hmac.new(
            hmac_key, hmac_text_bytes, hashlib.sha256).hexdigest()
        signed_headers["X-LINE-Authorization"] = signature
        return signed_headers
