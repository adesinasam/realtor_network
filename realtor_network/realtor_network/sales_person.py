import frappe
from frappe import _
from frappe import utils
from frappe.utils import cstr, flt, getdate, nowdate
from frappe.utils import cint


def validate_sales_person(doc, method):
    """Ensure sales_person_name is set before saving"""
    if not doc.sales_person_name:
        name_parts = []
        if doc.get("custom_first_name"):
            name_parts.append(doc.custom_first_name.strip())
        if doc.get("custom_last_name"):
            name_parts.append(doc.custom_last_name.strip())
        
        if name_parts:
            doc.sales_person_name = " ".join(name_parts)
        else:
            frappe.throw(_("Sales Person Name is required. Please set either First Name or Last Name"))

    # Email validation
    if doc.get("custom_email") or doc.get("custom_confirm_email"):
        if not doc.get("custom_email"):
            frappe.throw(_("Email is required when Confirm Email is set"))
        if not doc.get("custom_confirm_email"):
            frappe.throw(_("Please confirm your email address"))
        if doc.custom_email.lower() != doc.custom_confirm_email.lower():
            frappe.throw(_("Email addresses do not match. Please ensure both fields are identical."))

def update_referral_and_name(doc, method):
    """Handle referral code and final naming after document is saved"""
    # Skip if this is a fresh install or during migration
    if frappe.flags.in_install or frappe.flags.in_migrate:
        return
    
    # Generate referral code if missing
    if not doc.get("custom_referral_code"):
        last_code = frappe.db.sql("""
            SELECT MAX(CAST(custom_referral_code AS UNSIGNED))
            FROM `tabSales Person`
            WHERE custom_referral_code REGEXP '^[0-9]+$'
            AND name != %s
        """, doc.name)
        
        next_code = (last_code[0][0] or 110000) + 1
        doc.custom_referral_code = str(next_code).zfill(6)

    # Build final uppercase name format
    name_parts = []
    if doc.get("custom_first_name"):
        name_parts.append(doc.custom_first_name.upper().strip())
    if doc.get("custom_last_name"):
        name_parts.append(doc.custom_last_name.upper().strip())
    
    if not name_parts:
        name_parts.append(doc.name.split(" - ")[0].upper().strip())
    
    full_name = " ".join(name_parts)
    new_name = f"{full_name} - {doc.custom_referral_code}" if doc.get("custom_referral_code") else full_name
    
    # Update if needed
    if doc.sales_person_name != new_name or doc.name != new_name:
        frappe.db.set_value("Sales Person", doc.name, {
            "custom_referral_code": doc.custom_referral_code,
            "sales_person_name": new_name,
            "custom_full_name": full_name
        })
        
        # Rename document if name changed
        if doc.name != new_name:
            frappe.rename_doc("Sales Person", doc.name, new_name, force=True)
            frappe.db.commit()
            frappe.msgprint(_("Sales Person renamed to {0}").format(new_name))

