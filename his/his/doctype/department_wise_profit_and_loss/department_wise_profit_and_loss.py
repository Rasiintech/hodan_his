import frappe
from frappe.model.document import Document
from frappe.utils import flt

class DepartmentWiseProfitandLoss(Document):
    @frappe.whitelist()
    def get_account_balance(self):
        total_balance = abs(flt(self.get_total_account_balance()))
        previously_allocated = abs(flt(self.get_previously_allocated_amount()))
        remaining_balance = abs(total_balance - previously_allocated)

        return {
            "total_balance": total_balance,
            "previously_allocated": previously_allocated,
            "remaining_balance": remaining_balance,
        }

    def get_total_account_balance(self):
        account_doc = frappe.get_doc("Account", self.account)

        if account_doc.is_group:
            return self.get_group_balance(self.account, self.from_date, self.to_date)

        if account_doc.root_type == "Income":
            return self.get_gl_balance(self.account, self.from_date, self.to_date)
        elif account_doc.root_type == "Expense":
            return self.get_gl_balance(self.account, self.from_date, self.to_date)

        return 0

    def get_previously_allocated_amount(self):
        if not (self.account and self.from_date and self.to_date):
            return 0

        conditions = [
            "d.account = %s",
            "d.from_date = %s",
            "d.to_date = %s",
            "d.docstatus < 2",
        ]
        values = [self.account, self.from_date, self.to_date]

        # if self.type:
        #     conditions.append("d.type = %s")
        #     values.append(self.type)

        if self.name and not self.name.startswith("new-"):
            conditions.append("d.name != %s")
            values.append(self.name)

        query = f"""
            SELECT COALESCE(SUM(t.allocatated_amount), 0)
            FROM `tabDepartment Wise Profit and Loss` d
            LEFT JOIN `tabAllocation Table` t
              ON t.parent = d.name
             AND t.parenttype = 'Department Wise Profit and Loss'
            WHERE {' AND '.join(conditions)}
        """

        return flt(frappe.db.sql(query, values)[0][0] or 0)

    def get_group_balance(self, parent_account, from_date, to_date):
        group_balance = 0

        child_accounts = frappe.get_all(
            "Account",
            filters={"parent_account": parent_account},
            fields=["name", "is_group", "root_type"]
        )

        for child in child_accounts:
            if child.is_group:
                group_balance += self.get_group_balance(child.name, from_date, to_date)
            else:
                if child.root_type == "Income":
                    group_balance += self.get_gl_balance(child.name, from_date, to_date)
                elif child.root_type == "Expense":
                    group_balance += self.get_gl_debit_balance(child.name, from_date, to_date)

        return group_balance

    def get_leaf_accounts(self, parent_account, root_type=None):
        leaf_accounts = []

        child_accounts = frappe.get_all(
            "Account",
            filters={"parent_account": parent_account},
            fields=["name", "is_group", "root_type"],
        )

        for child in child_accounts:
            if child.is_group:
                leaf_accounts.extend(self.get_leaf_accounts(child.name, root_type=root_type))
            elif not root_type or child.root_type == root_type:
                leaf_accounts.append(child.name)

        return leaf_accounts

    def get_gl_balance(self, account, from_date, to_date):
        query = """
            SELECT SUM(debit), SUM(credit)
            FROM `tabGL Entry`
            WHERE account = %s
              AND posting_date BETWEEN %s AND %s and is_cancelled = 0
        """
        result = frappe.db.sql(query, (account, from_date, to_date), as_list=True)

        if result and result[0]:
            debit_sum, credit_sum = result[0]
            return (credit_sum or 0) - (debit_sum or 0)

        return 0

    def get_gl_debit_balance(self, account, from_date, to_date):
        query = """
            SELECT SUM(debit), SUM(credit)
            FROM `tabGL Entry`
            WHERE account = %s
              AND posting_date BETWEEN %s AND %s and is_cancelled = 0
        """
        result = frappe.db.sql(query, (account, from_date, to_date), as_list=True)

        if result and result[0]:
            debit_sum, credit_sum = result[0]
            return (debit_sum or 0) - (credit_sum or 0)

            return 0

    def get_remaining_balance_amount(self):
        total_balance = abs(flt(self.get_total_account_balance()))
        previously_allocated = abs(flt(self.get_previously_allocated_amount()))
        return max(total_balance - previously_allocated, 0)

    def get_account_rule_allocations(self):
        if not self.account:
            return []

        account_doc = frappe.get_doc("Account", self.account)
        rules = [
            row for row in (account_doc.get("account_allocation_rule") or [])
            if row.consultant and flt(row.percentage)
        ]
        if not rules:
            return []

        total_percentage = sum(flt(row.percentage) for row in rules)
        if abs(total_percentage - 100) > 0.001:
            frappe.throw("Account Allocation Rules total percentage must be 100")

        remaining_balance = self.get_remaining_balance_amount()
        allocations = []

        for row in rules:
            department = row.department or frappe.db.get_value(
                "Healthcare Practitioner", row.consultant, "department"
            )
            allocations.append(
                {
                    "consultant": row.consultant,
                    "department": department,
                    "allocatated_percentage": flt(row.percentage),
                    "allocatated_amount": remaining_balance * flt(row.percentage) / 100,
                }
            )

        return self.merge_account_rule_allocations(allocations)

    def merge_account_rule_allocations(self, allocations):
        merged = {}
        for row in allocations:
            key = (row.get("consultant"), row.get("department"))
            if key not in merged:
                merged[key] = {
                    "consultant": row.get("consultant"),
                    "department": row.get("department"),
                    "allocatated_percentage": 0,
                    "allocatated_amount": 0,
                }

            merged[key]["allocatated_percentage"] += flt(row.get("allocatated_percentage"))
            merged[key]["allocatated_amount"] += flt(row.get("allocatated_amount"))

        return list(merged.values())
   
   
    @frappe.whitelist()
    def get_direct_expense_by_practitioner(self):
        rule_allocations = self.get_account_rule_allocations()
        if rule_allocations:
            return rule_allocations

        account_doc = frappe.get_doc("Account", self.account)
        allocation_doc = account_doc.allocation_doc

        if not allocation_doc:
            frappe.throw(
                "This account has no Allocation Doc. Either configure Account Allocation Rules on the Account or set Allocation Doc."
            )

        if allocation_doc == "Lab Test Template":
            return self.get_lab_test_cost_by_practitioner()

        if allocation_doc == "Salary Slip":
            query = """
                SELECT
                    e.allocated_consultant AS consultant,
                    hp.department AS department,
                    SUM(ss.net_pay) AS allocatated_amount
                FROM `tabSalary Slip` ss
                INNER JOIN `tabEmployee` e
                    ON e.name = ss.employee
                LEFT JOIN `tabHealthcare Practitioner` hp
                    ON hp.name = e.allocated_consultant
                WHERE ss.posting_date BETWEEN %s AND %s
             
                AND ss.docstatus = 1
                AND e.allocated_consultant IS NOT NULL
                AND e.allocated_consultant != ''
                GROUP BY e.allocated_consultant, hp.department
            """

            result = frappe.db.sql(
                query,
                (self.from_date, self.to_date),
                as_dict=True
            )

            return result

        else:
            allocation_map = {
                "Sales Invoice": {
                    "join": "INNER JOIN `tabSales Invoice` d ON d.name = gl.voucher_no",
                    "consultant_field": "d.ref_practitioner",
                    "department_join": "LEFT JOIN `tabHealthcare Practitioner` h ON h.name = d.ref_practitioner",
                    "department_field": "h.department",
                    "extra_where": "AND d.docstatus = 1 AND gl.voucher_type = 'Sales Invoice'",
                    "group_by": "d.ref_practitioner, h.department"
                },
                "Stock Entry": {
                    "join": "INNER JOIN `tabStock Entry` d ON d.name = gl.voucher_no",
                    "consultant_field": "d.ref_practitioner",
                    "department_join": "LEFT JOIN `tabHealthcare Practitioner` h ON h.name = d.ref_practitioner",
                    "department_field": "h.department",
                    "extra_where": "AND d.docstatus = 1 AND gl.voucher_type = 'Stock Entry'",
                    "group_by": "d.ref_practitioner, h.department"
                },
                "Journal Entry": {
                    "join": "INNER JOIN `tabJournal Entry` d ON d.name = gl.voucher_no",
                    "consultant_field": "d.ref_practitioner",
                    "department_join": "LEFT JOIN `tabHealthcare Practitioner` h ON h.name = d.ref_practitioner",
                    "department_field": "h.department",
                    "extra_where": "AND d.docstatus = 1 AND gl.voucher_type = 'Journal Entry'",
                    "group_by": "d.ref_practitioner, h.department"
                }
            }

            if allocation_doc not in allocation_map:
                frappe.throw(f"Unsupported Allocation Doc: {allocation_doc}")

            config = allocation_map[allocation_doc]

            query = f"""
                SELECT
                    {config['consultant_field']} AS consultant,
                    {config['department_field']} AS department,
                    SUM(gl.debit - gl.credit) AS allocatated_amount
                FROM `tabGL Entry` gl
                {config['join']}
                {config['department_join']}
                WHERE gl.account = %s
                AND gl.posting_date BETWEEN %s AND %s
                AND gl.is_cancelled = 0
                AND {config['consultant_field']} IS NOT NULL
                AND {config['consultant_field']} != ''
                {config['extra_where']}
                GROUP BY {config['group_by']}
            """

            result = frappe.db.sql(
                query,
                (self.account, self.from_date, self.to_date),
                as_dict=True
            )

            return result

    def get_lab_test_cost_by_practitioner(self):
        sold_tests = frappe.db.sql(
            """
                SELECT
                    s.ref_practitioner AS consultant,
                    hp.department AS department,
                    si.item_code,
                    SUM(ABS(si.qty)) AS sold_qty
                FROM `tabSales Invoice Item` si
                INNER JOIN `tabSales Invoice` s
                    ON s.name = si.parent
                LEFT JOIN `tabHealthcare Practitioner` hp
                    ON hp.name = s.ref_practitioner
                WHERE s.posting_date BETWEEN %s AND %s
                    AND s.docstatus = 1
                    AND IFNULL(s.is_return, 0) = 0
                    AND s.ref_practitioner IS NOT NULL
                    AND s.ref_practitioner != ''
                    AND si.item_group = 'Laboratory'
                GROUP BY s.ref_practitioner, hp.department, si.item_code
            """,
            (self.from_date, self.to_date),
            as_dict=True,
        )

        if not sold_tests:
            return []

        item_codes = sorted({row.item_code for row in sold_tests if row.item_code})
        template_by_item = self.get_lab_template_details_by_item(item_codes)

        consultant_totals = {}
        for row in sold_tests:
            template_details = template_by_item.get(row.item_code)
            if not template_details:
                continue

            consultant = row.consultant
            department = row.department
            key = (consultant, department)
            if key not in consultant_totals:
                consultant_totals[key] = {
                    "consultant": consultant,
                    "department": department,
                    "allocatated_amount": 0,
                }

            consultant_totals[key]["allocatated_amount"] += flt(row.sold_qty) * flt(
                template_details.get("cost")
            )

        return [row for row in consultant_totals.values() if flt(row.get("allocatated_amount"))]

    def get_lab_template_details_by_item(self, item_codes):
        if not item_codes:
            return {}

        templates = frappe.get_all(
            "Lab Test Template",
            filters={"item": ["in", item_codes]},
            fields=["name", "item"],
        )

        template_map = {}
        for template in templates:
            cost = self.get_lab_template_cost(template.name)
            template_map[template.item] = {
                "template": template.name,
                "cost": cost,
            }

        return template_map

    def get_lab_template_cost(self, template_name):
        meta = frappe.get_meta("Lab Test Template")
        for fieldname in ("cost", "lab_test_cost", "total_cost"):
            if meta.has_field(fieldname):
                value = frappe.db.get_value("Lab Test Template", template_name, fieldname)
                if flt(value):
                    return flt(value)

        template_doc = frappe.get_doc("Lab Test Template", template_name)
        total_cost = 0
        for row in template_doc.get("inventory") or []:
            valuation_rate = frappe.db.get_value("Item", row.item, "valuation_rate")
            total_cost += flt(row.qty) * flt(valuation_rate)

        return total_cost

    @frappe.whitelist()
    def get_all_consultants(self):
        rule_allocations = self.get_account_rule_allocations()
        if rule_allocations:
            return rule_allocations

        query = """
                SELECT
                    name as consultant,
                    department AS department 
                    
                    from `tabHealthcare Practitioner` where status = "Active"
                    """
        result = frappe.db.sql(
                query,
                
                as_dict=True
            )
        return result


    @frappe.whitelist()
    def get_sales_invoice_by_practitioner(self):
        if not (self.account and self.from_date and self.to_date):
            return []

        account_doc = frappe.get_doc("Account", self.account)
        if account_doc.is_group:
            accounts = self.get_leaf_accounts(self.account, root_type="Income")
        else:
            accounts = [self.account]

        if not accounts:
            return []

        account_placeholders = ", ".join(["%s"] * len(accounts))

        # Allocate income from the actual GL impact of the selected account.
        # This keeps allocations aligned with the account balance and excludes
        # cancelled entries or unrelated sales invoices.
        query = f"""
            SELECT
                SUM(gl.credit - gl.debit) AS allocatated_amount,
                s.ref_practitioner AS consultant,
                h.department AS department
            FROM `tabGL Entry` gl
            INNER JOIN `tabSales Invoice` s
                ON s.name = gl.voucher_no
            LEFT JOIN `tabHealthcare Practitioner` h
                ON h.name = s.ref_practitioner
            WHERE gl.account IN ({account_placeholders})
              AND gl.posting_date BETWEEN %s AND %s
              AND gl.is_cancelled = 0
              AND gl.voucher_type = 'Sales Invoice'
              AND s.docstatus = 1
              AND s.ref_practitioner IS NOT NULL
              AND s.ref_practitioner != ''
            GROUP BY s.ref_practitioner, h.department
            HAVING ABS(SUM(gl.credit - gl.debit)) > 0.0001
        """
        result = frappe.db.sql(query, tuple(accounts) + (self.from_date, self.to_date), as_dict=True)

        balance = flt(self.balance)

        # for row in result:
        #     row["allocatated_percentage"] = (flt(row["allocatated_amount"]) / balance * 100) if balance else 0

        return result

    @frappe.whitelist()
    def get_indirect_expense_by_revenue(self):
        rule_allocations = self.get_account_rule_allocations()
        if rule_allocations:
            return rule_allocations

        query = """
            SELECT
                SUM(s.net_total) AS revenue_amount,
                s.ref_practitioner AS consultant,
                h.department AS department
            FROM `tabSales Invoice` s
            LEFT JOIN `tabHealthcare Practitioner` h
                ON h.name = s.ref_practitioner
            WHERE s.posting_date BETWEEN %s AND %s
              AND s.docstatus = 1
              AND s.ref_practitioner IS NOT NULL
              AND s.ref_practitioner != ''
            GROUP BY s.ref_practitioner, h.department
        """
        result = frappe.db.sql(query, (self.from_date, self.to_date), as_dict=True)

        total_revenue = sum(flt(row.get("revenue_amount")) for row in result)
        balance = flt(self.balance)

        for row in result:
            revenue_amount = flt(row.get("revenue_amount"))
            percentage = (revenue_amount / total_revenue * 100) if total_revenue else 0
            row["allocatated_percentage"] = percentage
            row["allocatated_amount"] = balance * percentage / 100 if balance else 0
            row.pop("revenue_amount", None)

        return result
