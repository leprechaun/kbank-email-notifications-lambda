import datetime
import re
#import pytz

from datetime import datetime
from dataclasses import dataclass


class Parser2:
    field_map = {
        'Transaction Number': ('id',),
        'Transaction Date': ('datetime', lambda x: datetime.strptime(x, "%d/%m/%Y  %H:%M:%S")),
        'Transaction No.': ('reference', ),

        'From Account': ('from-id',),
        'Paid From Account': ('from-id',),

        'To PromptPay ID': ('to-id',),
        'SHOP ID': ("to-id",),
        'To Account': ("to-id",),
        'MERCHANTNO.1': ("to-id",),
        'MERCHANT NO.1': ("to-id",),
        'MerchantID': ("to-id",),

        'Received Name': ('to-name',),
        'Company Name': ("to-name", ),
        'Account Name': ("to-name",),

        'To Bank': ("to-bank",),

        'Amount (THB)': ('amount', lambda x: float(x.replace(",",""))),
        'Fee (THB)': ('fee', float),

        'Available Balance (THB)': ('balance', lambda x: float(x.replace(",", ""))),
    }

    def parse(self, body: str):
        lines = []
        fields = []

        lines = body.split("\n")
        lines = [line for line in lines if line.strip() != '']

        fields = {}

        for line in lines:
            if matches := re.match(r"^\t([\w ()0-9.]+): (.+)$", line):
                #print(line)
                fields[matches.groups()[0]] = matches.groups()[1].strip()

        aliased_fields = {}

        for key, value in fields.items():
            field = key.strip()

            if field not in self.field_map.keys():
                continue

            alias = self.field_map[field][0]

            if len(self.field_map[field]) > 1 and callable(self.field_map[field][1]):
                #print(field," = ", "'" + value.strip() + "'")
                value = self.field_map[field][1](value.strip())

            if type(value) == dict:
                aliased_fields = aliased_fields | value
            else:
                aliased_fields[alias] = value

        if 'datetime' in aliased_fields:
            bkk = pytz.timezone("Asia/Bangkok")
            aliased_fields['datetime'] = bkk.localize(aliased_fields['datetime'])

        return aliased_fields



@dataclass
class Recipient:
    bank: str
    account: str
    name: str


@dataclass
class Transaction:
    timestamp: datetime
    id: str
    amount: float
    source: str
    recipient: Recipient
    fee: float
    balance: float


class TransactionFactory:
    def construct(self, databag):
        print(databag)
        return Transaction(
            self.get_timestamp(databag),
            self.get_id(databag),
            self.get_amount(databag),
            self.get_source(databag),
            self.get_recipient(databag),
            float(databag['Fee (THB)']),
            float(databag['Available Balance (THB)'].replace(",", ""))
        )

    def get_id(self, databag):
        return databag['Transaction Number']

    def get_first(self, field, databag, methods):
        for method in methods:
            try:
                if result := method(databag):
                    return result
            except Exception as e:
                pass

        raise Exception("Could not extract: %s" % field)

    def get_timestamp(self, databag):
        methods = [
            lambda db: datetime.strptime(db['Transaction Date'], "%d/%m/%Y  %H:%M:%S")
        ]

        return self.get_first(
            "timestamp",
            databag,
            methods
        )

    def get_amount(self, databag):
        methods = [
            lambda db: float(db['Amount (THB)'].replace(",",""))
        ]

        return self.get_first(
            "timestamp",
            databag,
            methods
        )

    def get_source(self, databag):
        methods = [
            lambda db: db['From Account'],
            lambda db: db['Paid From Account'],
        ]

        return self.get_first(
            "source",
            databag,
            methods
        )

    def get_recipient(self, databag):

        return Recipient(
            databag.get('To Bank'),
            self.get_to_account(databag),
            self.get_to_name(databag)
        )

    def get_to_account(self, databag):
        methods = [
            lambda x: x['To Account'],
            lambda x: x['To PromptPay ID'],
            lambda x: x["MerchantID"],
        ]

        try:
            return self.get_first("to_account", databag, methods)
        except:
            return None


    def get_to_name(self, databag):
        methods = [
            lambda x: x['Account Name'],
            lambda x: x['Received Name'],
            lambda x: x['Company Name'],
        ]

        return self.get_first("to_name", databag, methods)


class Parser:
    def __init__(self, tf: TransactionFactory):
        self.tf = tf

    def parse(self, body):
        databag = self.process_body(body)
        try:
            return self.tf.construct(databag)
        except Exception as e:
            print(databag)
            raise e

    def get_relevant_lines(self, body):
        starts_with_tab = lambda s: s.startswith("\t")
        is_bullet = lambda s: s.startswith("\t-")
        is_lower_ascii = lambda s: ord(s[0]) < 128

        return [line.strip() for line in body.split("\n") if starts_with_tab(line) and not is_bullet(line) and is_lower_ascii(line.strip())]

    def process_body(self, body):
        lines = self.get_relevant_lines(body)

        fields = {}

        for line in lines:
            #print(line)
            (key, value)  = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            fields[key] = value

        return fields
