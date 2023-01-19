from abc import ABC, abstractmethod
from datetime import date
from py_pdf_parser.loaders import load_file
from py_pdf_parser.visualise import visualise
from transactions import TruistTransaction


class StatementParser(ABC):
    def __init__(self, statement_filepath, la_params=None):
        if isinstance(la_params, dict):
            self.document = load_file(statement_filepath, la_params=la_params)
        else:
            self.document = load_file(statement_filepath)

    @staticmethod
    @abstractmethod
    def _objectify_transactions(transaction_str_list: list[str], is_debit: bool):
        pass


class TruistStatementParser(StatementParser):
    default_la_params = {
        "char_margin": 100.0,
        "word_margin": 0.15,
    }

    def __init__(self, statement_filepath, la_params=None):
        if la_params is None:
            super().__init__(
                statement_filepath, la_params=TruistStatementParser.default_la_params
            )
        else:
            super().__init__(statement_filepath, la_params=la_params)

        debits = self._find_debits()
        for debit in debits:
            print(debit)

    def _find_debits(self):
        """Find and return the list of debit strings across all pages"""

        debits_title_list = self.document.elements.filter_by_text_equal(
            "Other withdrawals, debits and service charges"
        )
        assert len(debits_title_list) <= 1

        if len(debits_title_list) == 0:
            return []

        all_debits: list[str] = []
        current_page_debits = self.document.elements.move_forwards_from(
            debits_title_list[0], 1
        )

        current_page_debits_split = current_page_debits.text().split("\n")

        while current_page_debits_split[-1] == "continued":  # more debits on next page
            all_debits.extend(current_page_debits_split[1:-1])

            # update `current_page_debits` to next page of debits
            current_page_debits = self.document.elements.move_forwards_from(
                current_page_debits, 3
            )
            current_page_debits_split = current_page_debits.text().split("\n")

        all_debits.extend(current_page_debits_split[1:-1])

        return self._objectify_transactions(all_debits, True)

    @staticmethod
    def _objectify_transactions(transaction_str_list: list[str], is_debit: bool):
        transactions: list[TruistTransaction] = []

        last_month = int(transaction_str_list[-1][:2])

        current_year = date.today().year

        for transaction_str in transaction_str_list:
            transaction_year = current_year

            month = int(transaction_str[:2])
            if month == 12 and last_month == 1:
                transaction_year = current_year - 1

            transactions.append(TruistTransaction(is_debit, transaction_str, transaction_year))
        
        return transactions


def main():
    parser = TruistStatementParser("statements/truist_statement_2022-10.pdf")


if __name__ == "__main__":
    main()
