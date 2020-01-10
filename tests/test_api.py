import json
import unittest
from unittest.mock import MagicMock, patch
import linepay
from linepay.exceptions import LinePayApiError


class TestLinePayApi(unittest.TestCase):

    def test_is_supported_currency(self):
        self.assertTrue(linepay.LinePayApi.is_supported_currency("USD"))
        self.assertTrue(linepay.LinePayApi.is_supported_currency("JPY"))
        self.assertTrue(linepay.LinePayApi.is_supported_currency("TWD"))
        self.assertTrue(linepay.LinePayApi.is_supported_currency("THB"))
        self.assertFalse(linepay.LinePayApi.is_supported_currency("GBP"))

    def test_is_supported_currency_with_none(self):
        with self.assertRaises(ValueError):
            linepay.LinePayApi.is_supported_currency(None)

    def test_round_amount_by_currency(self):
        self.assertEqual(1, linepay.LinePayApi.round_amount_by_currency("JPY", 1.0))
        self.assertEqual(9.99, linepay.LinePayApi.round_amount_by_currency("USD", 9.99))
        self.assertEqual(9.99, linepay.LinePayApi.round_amount_by_currency("THB", 9.99))
        self.assertEqual(9.99, linepay.LinePayApi.round_amount_by_currency("TWD", 9.99))

    def test_round_amount_by_currency_with_unsupported_currency(self):
        with self.assertRaises(ValueError):
            linepay.LinePayApi.round_amount_by_currency("GBP", 9.99)

    def test_constructor(self):
        print("testing constructor.")
        with self.assertRaises(ValueError):
            channel_id = "hoge"
            channel_secret = None
            api = linepay.LinePayApi(channel_id, channel_secret, is_sandbox=True)

    def test_constructor_with_sandbox(self):
        print("testing constructor with sandbox.")
        channel_id = "hoge"
        channel_secret = "fuga"
        api = linepay.LinePayApi(channel_id, channel_secret, is_sandbox=True)
        # assert
        self.assertEqual(api.headers.get("Content-Type"), "application/json")
        self.assertEqual(api.headers.get("X-LINE-ChannelId"), channel_id)
        self.assertEqual(api.channel_id, channel_id)
        self.assertEqual(api.channel_secret, channel_secret)
        self.assertEqual(api.api_endpoint, linepay.LinePayApi.SANDBOX_API_ENDPOINT)

    def test_constructor_with_production(self):
        print("testing constructor with production.")
        channel_id = "hoge"
        channel_secret = "fuga"
        api = linepay.LinePayApi(channel_id, channel_secret, is_sandbox=False)
        # assert
        self.assertEqual(api.headers.get("Content-Type"), "application/json")
        self.assertEqual(api.headers.get("X-LINE-ChannelId"), channel_id)
        self.assertEqual(api.channel_id, channel_id)
        self.assertEqual(api.channel_secret, channel_secret)
        self.assertEqual(api.api_endpoint, linepay.LinePayApi.DEFAULT_API_ENDPOINT)
    
    def test_constructor_with_default_endpoint(self):
        print("testing constructor with production.")
        channel_id = "hoge"
        channel_secret = "fuga"
        api = linepay.LinePayApi(channel_id, channel_secret)
        # assert
        self.assertEqual(api.headers.get("Content-Type"), "application/json")
        self.assertEqual(api.headers.get("X-LINE-ChannelId"), channel_id)
        self.assertEqual(api.channel_id, channel_id)
        self.assertEqual(api.channel_secret, channel_secret)
        self.assertEqual(api.api_endpoint, linepay.LinePayApi.DEFAULT_API_ENDPOINT)

    def test_sign(self):
        print("testing sign.")
        channel_id = "hoge"
        channel_secret = "fuga"
        api = linepay.LinePayApi(channel_id, channel_secret, is_sandbox=True)
        body_str = '{"amount": 1, "currency": "JPY", "orderId": "5383b36e-fe10-4767-b11b-81eefd1752fa", "packages": [{"id": "package-999", "amount": 1, "name": "Sample package", "products": [{"id": "product-001", "name": "Sample product", "quantity": 1, "price": 1}]}], "redirectUrls": {"confirmUrl": "https://example.com/pay/confirm", "cancelUrl": "https://example.com/pay/cancel"}}'
        nonce = "021a6bb9-ed18-4562-b9bd-ad07a27532f6"
        api._create_nonce = MagicMock(return_value=nonce)
        result = api.sign(api.headers, "/v3/payments/request", body_str)
        print(result)
        self.assertEqual(result["X-LINE-ChannelId"], channel_id)
        self.assertEqual(result["Content-Type"], "application/json")
        self.assertEqual(result["X-LINE-Authorization-Nonce"], nonce)
        self.assertEqual(result["X-LINE-Authorization"], "Rz5VEwPHChlQgN+dEmYWWbtWKw0XS41MblRB/dRdygE=")

    def test_request(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            request_options = {"hoge": "fuga"}
            result = api.request(request_options)
            self.assertEqual(result, mock_api_result.return_value)
            mock_sign.assert_called_once_with(api.headers, "/v3/payments/request", json.dumps(request_options))

    def test_request_with_invalid_param(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1111"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                api.request(None)

    def test_request_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1111"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            request_options = {"hoge": "fuga"}
            with self.assertRaises(LinePayApiError):
                api.request(request_options)

    def test_confirm(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            amount = 10.0
            currency = "JPY"
            result = api.confirm(transaction_id, amount, currency)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/{}/confirm".format(
                transaction_id
            )
            request_options = {
                "amount": int(amount),
                "currency": currency
            }
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_confirm_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                transaction_id = "transaction-1234567890"
                amount = 10.0
                currency = "JPY"
                result = api.confirm(transaction_id, amount, currency)

    def test_confirm_with_none_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = None
                amount = 10.0
                currency = "JPY"
                result = api.confirm(transaction_id, amount, currency)

    def test_confirm_with_invalid_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = 10
                amount = 10.0
                currency = "JPY"
                result = api.confirm(transaction_id, amount, currency)

    def test_confirm_with_invalid_amount(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = 99
                currency = "JPY"
                result = api.confirm(transaction_id, amount, currency)

    def test_confirm_with_none_currency(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = 1.0
                currency = None
                result = api.confirm(transaction_id, amount, currency)

    def test_confirm_with_not_supported_currency(self):
        with patch('linepay.api.requests.post') as post:
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = 1.0
                currency = "GBP"
                result = api.confirm(transaction_id, amount, currency)

    def test_capture(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            amount = 10.0
            currency = "JPY"
            result = api.capture(transaction_id, amount, currency)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/authorizations/{}/capture".format(
                transaction_id
            )
            request_options = {
                "amount": int(amount),
                "currency": currency
            }
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_capture_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1104"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                transaction_id = "transaction-1234567890"
                amount = 10.0
                currency = "JPY"
                result = api.capture(transaction_id, amount, currency)

    def test_capture_with_none_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = None
                amount = 10.0
                currency = "JPY"
                result = api.capture(transaction_id, amount, currency)

    def test_capture_with_invalid_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = 10
                amount = 10.0
                currency = "JPY"
                result = api.capture(transaction_id, amount, currency)

    def test_capture_with_invalid_amount(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = 99
                currency = "JPY"
                result = api.capture(transaction_id, amount, currency)

    def test_capture_with_none_currency(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = 1.0
                currency = None
                result = api.capture(transaction_id, amount, currency)

    def test_capture_with_not_supported_currency(self):
        with patch('linepay.api.requests.post') as post:
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = 1.0
                currency = "GBP"
                result = api.capture(transaction_id, amount, currency)

    def test_void(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.void(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/authorizations/{}/void".format(
                transaction_id
            )
            request_options = {}
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_void_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1104"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                transaction_id = "transaction-1234567890"
                result = api.void(transaction_id)

    def test_void_with_none_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = None
                result = api.void(transaction_id)

    def test_void_with_invalid_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = 10
                result = api.void(transaction_id)

    def test_refund(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            amount = 10.0
            result = api.refund(transaction_id, refund_amount=amount)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/{}/refund".format(
                transaction_id
            )
            request_options = {
                "refundAmount": amount
            }
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_refund_with_no_amount(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.refund(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/{}/refund".format(
                transaction_id
            )
            request_options = {}
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_refund_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                transaction_id = "transaction-1234567890"
                result = api.refund(transaction_id)

    def test_refund_with_none_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1150"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = None
                result = api.refund(transaction_id)

    def test_refund_with_invalid_transaction_id(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1150"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = 10
                result = api.refund(transaction_id)

    def test_refund_with_invalid_amount(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = "transaction-1234567890"
                amount = "invalid"
                result = api.refund(transaction_id, refund_amount=amount)

    def test_pay_preapproved(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            product_name = "product-1234567890"
            amount = 10.0
            currency = "JPY"
            order_id = "order-1234567890"
            result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/payment".format(
                reg_key
            )
            request_options = {
                "productName": product_name,
                "amount": int(amount),
                "currency": currency,
                "orderId": order_id,
                "capture": True
            }
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_pay_preapproved_with_authorization(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            product_name = "product-1234567890"
            amount = 10.0
            currency = "JPY"
            order_id = "order-1234567890"
            result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id, capture=False)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/payment".format(
                reg_key
            )
            request_options = {
                "productName": product_name,
                "amount": int(amount),
                "currency": currency,
                "orderId": order_id,
                "capture": False
            }
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_pay_preapproved_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1104"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                reg_key = "regkey-1234567890"
                product_name = "product-1234567890"
                amount = 10.0
                currency = "JPY"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_none_reg_key(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = None
                product_name = "product-1234567890"
                amount = 10.0
                currency = "JPY"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_invalid_reg_key(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = 9999
                product_name = "product-1234567890"
                amount = 10.0
                currency = "JPY"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_none_product_name(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = "regkey-1234567890"
                product_name = None
                amount = 10.0
                currency = "JPY"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_invalid_product_name(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = "regkey-1234567890"
                product_name = 9999
                amount = 10.0
                currency = "JPY"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_invalid_amount(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = "regkey-1234567890"
                product_name = 9999
                amount = "invalid amount"
                currency = "JPY"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_none_currency(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = "regkey-1234567890"
                product_name = 9999
                amount = 10.0
                currency = None
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_pay_preapproved_with_not_supported_currency(self):
        with patch('linepay.api.requests.post') as post:
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = "regkey-1234567890"
                product_name = 9999
                amount = 10.0
                currency = "GBP"
                order_id = "order-1234567890"
                result = api.pay_preapproved(reg_key, product_name, amount, currency, order_id)

    def test_check_reg_key(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            result = api.check_regkey(reg_key)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/check".format(
                reg_key
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_check_reg_key_with_creditcard_auth(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            result = api.check_regkey(reg_key, credit_card_auth=True)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/check?creditCardAuth=true".format(
                reg_key
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_check_reg_key_with_safe_return_code_1190(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "1190"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            result = api.check_regkey(reg_key)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/check".format(
                reg_key
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_check_reg_key_with_safe_return_code_1193(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "1193"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            result = api.check_regkey(reg_key)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/check".format(
                reg_key
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_check_reg_key_with_failed_return_code(self):
        with patch('linepay.api.requests.get') as get:
            get.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                reg_key = "regkey-1234567890"
                result = api.check_regkey(reg_key)

    def test_check_reg_key_with_none_reg_key(self):
        with patch('linepay.api.requests.get') as get:
            get.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = None
                result = api.check_regkey(reg_key)

    def test_check_reg_key_with_invalid_reg_key(self):
        with patch('linepay.api.requests.get') as get:
            get.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = 10
                result = api.check_regkey(reg_key)

    def test_expire_regkey(self):
        with patch('linepay.api.requests.post') as post:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            post.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            reg_key = "regkey-1234567890"
            result = api.expire_regkey(reg_key)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/preapprovedPay/{}/expire".format(
                reg_key
            )
            request_options = {}
            mock_sign.assert_called_once_with(api.headers, path, json.dumps(request_options))

    def test_expire_regkey_with_failed_return_code(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1104"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                reg_key = "regkey-1234567890"
                result = api.expire_regkey(reg_key)

    def test_expire_regkey_with_none_regkey(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = None
                result = api.expire_regkey(reg_key)

    def test_expire_regkey_with_invalid_regkey(self):
        with patch('linepay.api.requests.post') as post:
            post.return_value.json = MagicMock(return_value={"returnCode": "1101"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                reg_key = 9999
                result = api.expire_regkey(reg_key)

    def test_check_payment_status(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.check_payment_status(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/requests/{}/check".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_status_with_safe_return_code_0110(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0110"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.check_payment_status(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/requests/{}/check".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_status_with_safe_return_code_0121(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0121"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.check_payment_status(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/requests/{}/check".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_status_with_safe_return_code_0122(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0122"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.check_payment_status(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/requests/{}/check".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_status_with_safe_return_code_0123(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0123"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.check_payment_status(transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments/requests/{}/check".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_status_with_failed_return_code(self):
        with patch('linepay.api.requests.get') as get:
            get.return_value.json = MagicMock(return_value={"returnCode": "1104"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                transaction_id = "transaction-1234567890"
                result = api.check_payment_status(transaction_id)

    def test_payment_status_with_none_transaction_id(self):
        with patch('linepay.api.requests.get') as get:
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = None
                result = api.check_payment_status(transaction_id)

    def test_payment_status_with_invalid_transaction_id(self):
        with patch('linepay.api.requests.get') as get:
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(ValueError):
                transaction_id = 9999
                result = api.check_payment_status(transaction_id)

    def test_payment_details(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.payment_details()
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_details_with_transaction_id(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            transaction_id = "transaction-1234567890"
            result = api.payment_details(transaction_id=transaction_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments?transactionId={}".format(
                transaction_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_details_with_order_id(self):
        with patch('linepay.api.requests.get') as get:
            mock_api_result = MagicMock(return_value={"returnCode": "0000"})
            get.return_value.json = mock_api_result
            mock_sign = MagicMock(return_value={"X-LINE-Authorization": "dummy"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            api.sign = mock_sign
            order_id = "order-1234567890"
            result = api.payment_details(order_id=order_id)
            self.assertEqual(result, mock_api_result.return_value)
            path = "/v3/payments?orderId={}".format(
                order_id
            )
            mock_sign.assert_called_once_with(api.headers, path, "")

    def test_payment_details_with_failed_return_code(self):
        with patch('linepay.api.requests.get') as get:
            get.return_value.json = MagicMock(return_value={"returnCode": "1104"})
            api = linepay.LinePayApi("channel_id", "channel_secret", is_sandbox=True)
            with self.assertRaises(LinePayApiError):
                result = api.payment_details()
