from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
from erpnext.stock.utils import get_incoming_rate


class StandalonePurchaseReturnMixin:
    def set_rate_for_standalone_debit_note(self):
        if not (
            self.get("is_return")
            and self.get("update_stock")
            and not self.return_against
        ):
            return

        for row in self.items:
            if not row.rate:
                row.rate = get_incoming_rate(
                    {
                        "item_code": row.item_code,
                        "warehouse": row.warehouse,
                        "posting_date": self.get("posting_date"),
                        "posting_time": self.get("posting_time"),
                        "qty": row.qty,
                        "serial_and_batch_bundle": row.get("serial_and_batch_bundle"),
                        "company": self.company,
                        "voucher_type": self.doctype,
                        "voucher_no": self.name,
                    },
                    raise_error_if_no_rate=False,
                )

                row.discount_percentage = 0.0
                row.discount_amount = 0.0
                row.margin_rate_or_amount = 0.0


class CustomPurchaseInvoice(StandalonePurchaseReturnMixin, PurchaseInvoice):
    pass


class CustomPurchaseReceipt(StandalonePurchaseReturnMixin, PurchaseReceipt):
    pass
