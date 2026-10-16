from frappe.utils import flt

from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry


class CustomJournalEntry(JournalEntry):
    def check_credit_limit(self):
        customers = list(
            set(
                row.party
                for row in self.get("accounts")
                if row.party_type == "Customer" and row.party and flt(row.debit) > 0
            )
        )
        if customers:
            from erpnext.selling.doctype.customer.customer import check_credit_limit

            for customer in customers:
                check_credit_limit(customer, self.company, True)
