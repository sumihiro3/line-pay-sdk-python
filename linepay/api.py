# -*- coding: utf-8 -*-

import base64
import copy
from enum import Enum
import hashlib
import hmac
import json
import requests
import uuid

from .util import validate_function_args_return_value, LOGGER
from .exceptions import LinePayApiError


class LinePayApi(object):
    """LinePayApi provides interface for LINE Pay API."""

    LINE_PAY_API_VERSION = "v3"
    DEFAULT_API_ENDPOINT = "https://api-pay.line.me"
    SANDBOX_API_ENDPOINT = "https://sandbox-api-pay.line.me"
    CHECK_REGKEY_SAFE_RETURN_CODE_LIST = ["0000", "1190", "1193"]
    CHECK_PAYMENT_STATUS_SAFE_RETURN_CODE_LIST = [
        "0000", "0110", "0121", "0122", "0123"]

    @classmethod
    @validate_function_args_return_value
    def is_supported_currency(cls, currency: str) -> bool:
        """Check supported currency or not
        :param str currency: currency type
        :rtype bool: supported currency or not
        """
        result = False
        obj = CurrencyType.__members__.get(currency, None)
        if obj is not None:
            result = True
        return result

    @classmethod
    @validate_function_args_return_value
    def round_amount_by_currency(cls, currency: str, amount: float):
        if cls.is_supported_currency(currency) is False:
            raise ValueError("currency[{}] is not supported".format(currency))
        # If you use JPY. Need to round amount.
        if (CurrencyType.JPY.value == currency):
            amount = int(amount)
        return amount

    @validate_function_args_return_value
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

    @validate_function_args_return_value
    def sign(
        self,
        headers: dict,
        path: str,
        body: str
    ) -> dict:
        """generate signature method
        :param dict headers: Request HTTP Headers
        :param str path: API request path
        :param str body: API request body for POST Request or Query String
            (Without "?") for GET Request
        :rtpye dict: signed headers
        """
        LOGGER.debug("path: %s", path)
        LOGGER.debug("body: %s", body)
        signed_headers: dict = copy.deepcopy(headers)
        # Create nonce
        nonce: str = self._create_nonce()
        signed_headers["X-LINE-Authorization-Nonce"] = nonce
        # Create HMAC Signature
        hmac_key: bytes = self.channel_secret.encode()
        hmac_text_str: str = self.channel_secret + path + body + nonce
        hmac_text_bytes: bytes = hmac_text_str.encode()
        sign = hmac.new(
            hmac_key, hmac_text_bytes, hashlib.sha256)
        signed_headers["X-LINE-Authorization"] = base64.b64encode(
            sign.digest()).decode()
        LOGGER.debug(signed_headers)
        return signed_headers

    @validate_function_args_return_value
    def _create_nonce(self) -> str:
        """generate nonce for HMAC Authorization
        :rtpye str: generate nonce by uuid4
        """
        return str(uuid.uuid4())

    @validate_function_args_return_value
    def request(self, options: dict) -> dict:
        """Method to Request Payment
        :param dict options: LINE Pay Request API Options
            see https://pay.line.me/jp/developers/apis/onlineApis?locale=ja_JP
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

        LOGGER.debug("Going to execute Request API [URL: %s]", url)
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

    @validate_function_args_return_value
    def confirm(self, transaction_id: int, amount: float, currency: str) \
            -> dict:
        """Method to Confirm Payment
        :param int transaction_id: Transaction id returned from Request API
        :param float amount: Payment amount
        :param str currency: Payment currency (ISO 4217) Supported currencies
            are USD, JPY, TWD and THB
        :rtpye dict: Confirm API response
        """
        if (self.__class__.is_supported_currency(currency) is False):
            raise ValueError(
                "Currency:[{}] is not supported by LINE Pay".format(currency))
        path = "/{api_version}/payments/{transaction_id}/confirm".format(
            api_version=self.LINE_PAY_API_VERSION,
            transaction_id=str(transaction_id)
        )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        amount = self.__class__.round_amount_by_currency(currency, amount)
        options = {
            "amount": amount,
            "currency": currency
        }
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Confirm API [URL: %s]", url)
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Confirm API Completed!")
            return result
        else:
            LOGGER.debug("Confirm API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def capture(self, transaction_id: int, amount: float, currency: str) \
            -> dict:
        """Method to Capture Payment
        :param int transaction_id: Transaction id returned from Request API
        :param float amount: Payment amount
        :param str currency: Payment currency (ISO 4217) Supported currencies
            are USD, JPY, TWD and THB
        :rtpye dict: Capture API response
        """
        if (self.__class__.is_supported_currency(currency) is False):
            raise ValueError(
                "Currency:[{}] is not supported by LINE Pay".format(currency))
        path = "/{api_version}/payments/authorizations/" \
            "{transaction_id}/capture".format(
                api_version=self.LINE_PAY_API_VERSION,
                transaction_id=str(transaction_id)
            )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        amount = self.__class__.round_amount_by_currency(currency, amount)
        options = {
            "amount": amount,
            "currency": currency
        }
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Capture API [URL: %s]", url)
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Capture API Completed!")
            return result
        else:
            LOGGER.debug("Capture API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def void(self, transaction_id: int) -> dict:
        """Method to Void Payment
        :param int transaction_id: Transaction id returned from Request API
        :rtpye dict: Void API response
        """
        path = "/{api_version}/payments/authorizations/" \
            "{transaction_id}/void".format(
                api_version=self.LINE_PAY_API_VERSION,
                transaction_id=str(transaction_id)
            )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        options = {}
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Void API [URL: %s]", url)
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Void API Completed!")
            return result
        else:
            LOGGER.debug("Void API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def refund(self, transaction_id: int, refund_amount: int = 0) -> dict:
        """Method to Refund Payment
        :param int transaction_id: Transaction id returned from Request API
        :param float refund_amount: Refund amount. Full refund if not returned
        :rtpye dict: Refund API response
        """
        path = "/{api_version}/payments/{transaction_id}/refund".format(
            api_version=self.LINE_PAY_API_VERSION,
            transaction_id=str(transaction_id)
        )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        if (refund_amount > 0):
            options = {
                "refundAmount": refund_amount
            }
        else:
            options = {}
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Refund API [URL: %s]", url)
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Refund API Completed!")
            return result
        else:
            LOGGER.debug("Refund API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def pay_preapproved(
            self,
            reg_key: str,
            product_name: str,
            amount: float,
            currency: str,
            order_id: str,
            capture: bool = True) -> dict:
        """Method to Pay Preapproved
        :param str reg_key: RegKey returned from Confirm API
        :param str product_name: Product name
        :param float amount: Payment amount
        :param str currency: Payment currency (ISO 4217) Supported currencies
            are USD, JPY, TWD and THB
        :param str order_id: Order id
        :param bool capture: Capture payment nor not
        :rtpye dict: Pay Preapproved API response
        """
        if (self.__class__.is_supported_currency(currency) is False):
            raise ValueError(
                "Currency:[{}] is not supported by LINE Pay".format(currency))
        path = "/{api_version}/payments/preapprovedPay/" \
            "{reg_key}/payment".format(
                api_version=self.LINE_PAY_API_VERSION,
                reg_key=reg_key
            )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        amount = self.__class__.round_amount_by_currency(currency, amount)
        options = {
            "productName": product_name,
            "amount": amount,
            "currency": currency,
            "orderId": order_id,
            "capture": capture
        }
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Pay Preapproved API [URL: %s]", url)
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Pay Preapproved API Completed!")
            return result
        else:
            LOGGER.debug("Pay Preapproved API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def check_regkey(self, reg_key: str, credit_card_auth: bool = False) \
            -> dict:
        """Method to Check RegKey
        :param str reg_key: Reg Key returned from Confirm API
        :param bool credit_card_auth: Whether credit cards issued with RegKey
            have authorized minimum amount
        :rtpye dict: Check RegKey API response
        """
        path = "/{api_version}/payments/preapprovedPay/{reg_key}/check".format(
            api_version=self.LINE_PAY_API_VERSION,
            reg_key=reg_key
        )
        # build QueryString
        query = ""
        if (credit_card_auth is True):
            query = "creditCardAuth=true"
        if query == "":
            url = "{api_endpoint}{path}".format(
                api_endpoint=self.api_endpoint,
                path=path
            )
        else:
            url = "{api_endpoint}{path}?{query}".format(
                api_endpoint=self.api_endpoint,
                path=path,
                query=query
            )
        headers = self.sign(self.headers, path, query)

        LOGGER.debug("Going to execute Check RegKey API [URL: %s]", url)
        response = requests.get(url, headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code in self.CHECK_REGKEY_SAFE_RETURN_CODE_LIST:
            LOGGER.debug("Check RegKey API Completed!")
            return result
        else:
            LOGGER.debug("Check RegKey API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def expire_regkey(self, reg_key: str) -> dict:
        """Method to Expire RegKey
        :param str reg_key: Reg Key returned from Confirm API
        :rtpye dict: Expire RegKey API response
        """
        path = "/{api_version}/payments/preapprovedPay/" \
            "{reg_key}/expire".format(
                api_version=self.LINE_PAY_API_VERSION,
                reg_key=reg_key
            )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        options = {}
        body_str = json.dumps(options)
        headers = self.sign(self.headers, path, body_str)

        LOGGER.debug("Going to execute Expire RegKey API [URL: %s]", url)
        response = requests.post(url, json.dumps(options), headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Expire RegKey API Completed!")
            return result
        else:
            LOGGER.debug("Expire RegKey API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def check_payment_status(self, transaction_id: int) -> dict:
        """Method to Check Payment Status
        :param int transaction_id: TransactionId returned from Request API
        :rtpye dict: Check Payment Status API response
        """
        path = "/{api_version}/payments/requests/" \
            "{transaction_id}/check".format(
                api_version=self.LINE_PAY_API_VERSION,
                transaction_id=str(transaction_id)
            )
        url = "{api_endpoint}{path}".format(
            api_endpoint=self.api_endpoint,
            path=path
        )
        headers = self.sign(self.headers, path, "")

        LOGGER.debug(
            "Going to execute Check Payment Status API [URL: %s]", url)
        response = requests.get(url, headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code in self.CHECK_PAYMENT_STATUS_SAFE_RETURN_CODE_LIST:
            LOGGER.debug("Check Payment Status API Completed!")
            return result
        else:
            LOGGER.debug("Check Payment Status API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )

    @validate_function_args_return_value
    def payment_details(
        self, transaction_id: int = None,
            order_id: str = None) -> dict:
        """Method to Payment Details
        :param int transaction_id: Payment or refund transaction ID generated
            by LINE Pay
        :param str order_id: Order ID of the merchant
        :rtpye dict: Payment Details API response
        """
        path = "/{api_version}/payments".format(
            api_version=self.LINE_PAY_API_VERSION
        )
        # build QueryString
        query = ""
        if transaction_id is not None:
            query += "transactionId={}&".format(str(transaction_id))
        if order_id is not None:
            query += "orderId={}".format(order_id)
        if query.endswith("?") or query.endswith("&"):
            query = query[:-1]
        # build URL
        if query == "":
            url = "{api_endpoint}{path}".format(
                api_endpoint=self.api_endpoint,
                path=path
            )
        else:
            url = "{api_endpoint}{path}?{query}".format(
                api_endpoint=self.api_endpoint,
                path=path,
                query=query
            )
        headers = self.sign(self.headers, path, query)
        LOGGER.debug("Going to execute Payment Details API [URL: %s]", url)
        response = requests.get(url, headers=headers)
        result = response.json()
        LOGGER.debug(result)
        return_code = result.get("returnCode", None)
        if return_code == "0000":
            LOGGER.debug("Payment Details API Completed!")
            return result
        else:
            LOGGER.debug("Payment Details API Failed...")
            raise LinePayApiError(
                return_code=return_code,
                status_code=response.status_code,
                headers=dict(response.headers.items()),
                api_response=result
            )


class CurrencyType(Enum):
    # LINE Pay API supports USD, JPY, TWD, THB
    USD = "USD"
    JPY = "JPY"
    TWD = "TWD"
    THB = "THB"
