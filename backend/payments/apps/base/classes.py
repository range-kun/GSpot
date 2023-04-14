from abc import ABC, abstractmethod


class AbstractPaymentClass(ABC):
    @abstractmethod
    def request_balance_deposit_url(self, payment_data):
        pass

    @abstractmethod
    def request_balance_withdraw_url(self, payment_data):
        pass

    @abstractmethod
    def parse_income_data(self, payment_response):
        pass

    @abstractmethod
    def validate_income_data(self, balance_object, invoice_object: None = None):
        pass
