import frappe

@frappe.whitelist()
def enqueue_bulk_asset_cancel():
    frappe.enqueue(
        "his.api.cancelasset.bulk_cancel_assets",
        queue="long",
        timeout=7200,
        job_name="Bulk Cancel Assets"
    )
    return "Bulk cancel job queued"


def bulk_cancel_assets(batch_size=100):
    asset_codes = frappe.get_all(
        "Asset Cancelling",
       
        pluck="name",
        order_by="name asc"
    )

    success = 0
    failed = []

    for i, asset_code in enumerate(asset_codes, 1):
        try:
            asset_name = frappe.db.get_value(
                "Asset",
                {"asset_code": asset_code, "docstatus": 1},
                "name"
            )

            if asset_name:
                asset_doc = frappe.get_doc("Asset", asset_name)
                asset_doc.cancel()

            # frappe.db.set_value(
            #     "Asset Cancelling",
            #     asset_code,
            #     "status",
            #     "Cancelled",
            #     update_modified=False
            # )

            success += 1

        except Exception:
            failed.append(asset_code)
            frappe.log_error(
                title=f"Bulk Asset Cancel Failed: {asset_code}",
                message=frappe.get_traceback()
            )

        if i % batch_size == 0:
            frappe.db.commit()

    frappe.db.commit()

    return {
        "total": len(asset_codes),
        "success": success,
        "failed_count": len(failed),
        "failed": failed[:20]
    }