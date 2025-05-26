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
        
        next_code = (last_code[0][0] or 10000) + 1
        doc.custom_referral_code = str(next_code).zfill(5)
    
    # Build final name format
    name_parts = []
    if doc.get("custom_first_name"):
        name_parts.append(doc.custom_first_name.strip())
    if doc.get("custom_last_name"):
        name_parts.append(doc.custom_last_name.strip())
    
    if not name_parts:
        name_parts.append(doc.name.split(" - ")[0])
    
    full_name = " ".join(name_parts)
    new_name = f"{full_name} - {doc.custom_referral_code}" if doc.get("custom_referral_code") else full_name
    
    # Update if needed
    if doc.sales_person_name != new_name or doc.name != new_name:
        frappe.db.set_value("Sales Person", doc.name, {
            "custom_referral_code": doc.custom_referral_code,
            "sales_person_name": new_name
        })
        
        # Rename document if name changed
        if doc.name != new_name:
            frappe.rename_doc("Sales Person", doc.name, new_name)
            frappe.db.commit()
            frappe.msgprint(_("Sales Person renamed to {0}").format(new_name))


def before_save(doc, method):
    """Hook to generate referral code and ensure proper sales person naming"""
    
    # 1. Generate ascending numeric referral code if not set
    if not doc.custom_referral_code:
        max_code = frappe.db.sql("""
            SELECT MAX(CAST(custom_referral_code AS UNSIGNED))
            FROM `tabSales Person`
            WHERE custom_referral_code REGEXP '^[0-9]+$'
        """)[0][0] or 10000  # Default starting number
        
        doc.custom_referral_code = str(max_code + 1).zfill(5)  # 4-digit format (e.g., "10001")
    
    # 2. Build the sales_person_name (mandatory field)
    name_parts = []
    if doc.custom_first_name:
        name_parts.append(doc.custom_first_name)
    if doc.custom_last_name:
        name_parts.append(doc.custom_last_name)
    
    # Fallback names if no first/last name provided
    if not name_parts:
        if doc.name and doc.name != "New Sales Person":
            name_parts.append(doc.name)
        else:
            name_parts.append(_("Sales Person"))
    
    # Combine with referral code if exists
    if doc.custom_referral_code:
        doc.sales_person_name = f"{' '.join(name_parts)} - {doc.custom_referral_code}"
    else:
        doc.sales_person_name = ' '.join(name_parts)
    
    # 3. Validation for mandatory fields
    if not doc.sales_person_name:
        frappe.throw(_("Sales Person Name is required"))
