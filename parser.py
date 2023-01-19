from abc import ABC, abstractmethod
from datetime import date
from typing import Any
from py_pdf_parser.loaders import load_file
from transactions import TruistTransaction


class StatementParser(ABC):
    def __init__(self, statement_filepath, la_params=None):
        if isinstance(la_params, dict):
            self._document = load_file(statement_filepath, la_params=la_params)
        else:
            self._document = load_file(statement_filepath)

    @staticmethod
    @abstractmethod
    def _objectify_transactions(transaction_str_list: list[str], is_debit: bool) -> list[Any]:
        pass


class TruistStatementParser(StatementParser):
    _default_la_params = {
        "char_margin": 100.0,
        "word_margin": 0.15,
    }

    def __init__(self, statement_filepath, la_params=None):
        if la_params is None:
            super().__init__(
                statement_filepath, la_params=TruistStatementParser._default_la_params
            )
        else:
            super().__init__(statement_filepath, la_params=la_params)

        self._debits = []
        self._credits = []
        self._found_debits = False
        self._found_credits = False

    @property
    def debits(self):
        if not self._found_debits:
            self._debits = self._find_debits()
            self._found_debits = True

        return self._debits

    @property
    def credits(self):
        if not self._found_credits:
            self._credits = self._find_credits()
            self._found_credits = True
        return self._credits

    def _find_debits(self):
        """Find and return the list of debit transactions across all pages"""

        debits_title = "Other withdrawals, debits and service charges"

        debit_str_list = self._find_transactions(debits_title)

        return self._objectify_transactions(debit_str_list, is_debit=True)

    def _find_credits(self):
        """Find and return the list of credit transactions across all pages"""

        credits_title = "Deposits, credits and interest"

        credit_str_list = self._find_transactions(credits_title)

        return self._objectify_transactions(credit_str_list, is_debit=False)

    def _find_transactions(self, transaction_title_str: str):
        transactions_title_list = self._document.elements.filter_by_text_equal(
            transaction_title_str
        )
        assert len(transactions_title_list) <= 1

        if len(transactions_title_list) == 0:
            return []

        all_transactions: list[str] = []
        current_page_transactions = self._document.elements.move_forwards_from(
            transactions_title_list[0], 1
        )

        current_page_transactions_split = current_page_transactions.text().split("\n")

        while current_page_transactions_split[-1] == "continued":
            all_transactions.extend(current_page_transactions_split[1:-1])

            current_page_transactions = self._document.elements.move_forwards_from(
                current_page_transactions, 3
            )
            current_page_transactions_split = current_page_transactions.text().split(
                "\n"
            )

        all_transactions.extend(current_page_transactions_split[1:-1])

        return all_transactions

    @staticmethod
    def _objectify_transactions(transaction_str_list: list[str], is_debit: bool):
        if len(transaction_str_list) == 0:
            return []

        transactions: list[TruistTransaction] = []

        last_month = int(transaction_str_list[-1][:2])

        current_year = date.today().year

        for transaction_str in transaction_str_list:
            transaction_year = current_year

            month = int(transaction_str[:2])
            if month == 12 and last_month == 1:
                transaction_year = current_year - 1

            transactions.append(
                TruistTransaction(is_debit, transaction_str, transaction_year)
            )

        return transactions
