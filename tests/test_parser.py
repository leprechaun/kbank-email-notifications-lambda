import unittest

import email
import email.message
from email.utils import formatdate
from datetime import datetime

from kbank_email_notifications_lambda.parser import TransactionFactory

class TestTransactionData(unittest.TestCase):
    databag = {
        "Transaction Date": "26/03/2025  11:29:30",
        "Transaction Number":  "015085112930COR03074",
        "From Account": "xxx-x-x9191-x",
        "To Bank": "BANK OF AYUDHYA",
        "To Account": "123-4567-890",
        "Account Name": "Khun Lolen",
        "Amount (THB)": "1,000.00",
        "Fee (THB)": "0.00",
        "Available Balance (THB)":  "1,234,567.89"
    }

    factory = TransactionFactory()


    def test_get_timestamp(self):
        x = self.factory.get_timestamp(self.databag)

        self.assertEqual(
            x,
            datetime(2025, 3, 26, 11, 29, 30)
        )

    def test_get_id(self):
        x = self.factory.get_id(self.databag)

        self.assertEqual(
            x,
            "015085112930COR03074",
        )

    def test_get_amount(self):
        x = self.factory.get_amount(self.databag)

        self.assertEqual(
            x,
            1000
        )

    def test_get_source(self):
        x = self.factory.get_source(self.databag)

        self.assertEqual(
            x,
            "xxx-x-x9191-x"
        )

    def test_get_recipient(self):
        x = self.factory.get_recipient(self.databag)

        self.assertEqual(
            x.name,
            "Khun Lolen"
        )

        self.assertEqual(
            x.account,
            "123-4567-890"
        )

        self.assertEqual(
            x.bank,
            "BANK OF AYUDHYA"
        )

    def test_to_account_uses_to_account_first(self):
        r = self.factory.get_to_account({"To Account":"to-account","To PromptPay ID":"to-promptpay-id","MerchantID":"merchant-id"})

        self.assertEqual(r, "to-account")

    def test_to_account_uses_promptpay_id_second(self):
        r = self.factory.get_to_account({"To PromptPay ID":"to-promptpay-id","MerchantID":"merchant-id"})

        self.assertEqual(r, "to-promptpay-id")

    def test_to_account_uses_merchant_id_last(self):
        r = self.factory.get_to_account({"MerchantID":"merchant-id"})

        self.assertEqual(r, "merchant-id")

    def test_to_name_uses_account_name_first(self):
        r = self.factory.get_to_name({"Account Name":"account-name","Received Name":"received-name","Company Name":"company-name"})

        self.assertEqual(r, "account-name")

    def test_to_name_uses_received_name_second(self):
        r = self.factory.get_to_name({"Received Name":"received-name","Company Name":"company-name"})

        self.assertEqual(r, "received-name")

    def test_to_name_uses_company_name_last(self):
        r = self.factory.get_to_name({"Company Name":"company-name"})

        self.assertEqual(r, "company-name")


    def test_get_fee(self):
        t = self.factory.construct(self.databag)

        self.assertEqual(
            t.fee,
            0
        )

    def test_get_balance(self):
        t = self.factory.construct(self.databag)

        self.assertEqual(
            t.balance,
            1_234_567.89
        )


if __name__ == '__main__':
    unittest.main()
