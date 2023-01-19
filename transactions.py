from abc import ABC, abstractmethod
from datetime import date
import re


class Transaction(ABC):
    @abstractmethod
    def __init__(self):
        self._transaction_date = date.min
        self._transaction_description = ""
        self._transaction_amount = 0.0
        self._is_debit = False

    @property
    def transaction_date(self) -> date:
        return self._transaction_date

    @property
    def transaction_description(self) -> str:
        return self._transaction_description

    @property
    def transaction_amount(self) -> float:
        return self._transaction_amount

    @property
    def is_debit(self) -> bool:
        return self._is_debit

    def __repr__(self) -> str:
        return f'{self.transaction_date} ${self.transaction_amount} {self.transaction_description}'


class TruistTransaction(Transaction):
    def __init__(self, is_debit: bool, transaction_str: str, transaction_year: int):
        regex_pattern = re.compile(
            r"(?P<month>\d{2})\/(?P<day>\d{2}) (?P<description>.+) (?P<amount>[\d,]+\.\d{2})"
        )
        re_match = regex_pattern.match(transaction_str)
        assert re_match is not None

        self._transaction_date = date(
            transaction_year, int(re_match.group("month")), int(re_match.group("day"))
        )
        self._transaction_description = re_match.group("description")
        self._transaction_amount = float(re_match.group("amount"))
        self._is_debit = is_debit
