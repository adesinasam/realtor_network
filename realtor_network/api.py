
import json

import frappe
from frappe import _
from frappe.utils import get_url
from frappe.email.doctype.email_group.email_group import add_subscribers
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, getdate, nowdate
from frappe.utils.dateutils import get_dates_from_timegrain
from datetime import datetime


@frappe.whitelist()
def get_realtor_settings():
    realtorsetting = frappe.get_doc('Realtor Settings')
    return realtorsetting


@frappe.whitelist(allow_guest=True)
def newrealtor_form(first_name, last_name, phone, email, confirm_email, dob=None,
                   address=None, gender=None, city=None, state=None, country=None,
                   accountno=None, accountname=None, bank=None, terms=None,
                   upline=None, initial_url=None):
    """Process new realtor registration form with referral code generation"""
    
    # Validate required fields
    required_fields = {
        'First Name': first_name,
        'Last Name': last_name,
        'Phone': phone,
        'Email': email,
        'Confirm Email': confirm_email,
        'Country': country,
        'Terms Agreement': terms
    }
    
    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        return error_response(initial_url, f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate email match and format
    if email != confirm_email:
        return error_response(initial_url, "Email addresses do not match")
    if not frappe.utils.validate_email_address(email):
        return error_response(initial_url, "Invalid email address format")
    if frappe.db.exists("Sales Person", {"custom_email": email}):
        return error_response(initial_url, "Email already registered")
    if (frappe.db.exists("User", {"email": email}) and "Sales User" not in frappe.get_roles(email)):
        return error_response(initial_url, "Email already has a user account")

    try:
        # Handle upline assignment
        if not upline:
            try:
                realtorsetting = frappe.get_doc('Realtor Settings')
                company_realtor = frappe.get_doc('Sales Person', {
                    'custom_is_company': 1,
                    'custom_company': realtorsetting.company
                })
                upline = company_realtor.name
            except Exception as e:
                frappe.log_error(
                    title="Default Upline Assignment Failed",
                    message=f"Error assigning default upline: {str(e)}\n{frappe.get_traceback()}"
                )
                return error_response(
                    initial_url,
                    "Could not assign default upline. Please contact support."
                )

        # Generate referral code
        referral_code = generate_referral_code()
        
        # Format name components
        first_name_clean = first_name.upper().strip() if first_name else ""
        last_name_clean = last_name.upper().strip() if last_name else ""
        full_name = " ".join(filter(None, [first_name_clean, last_name_clean]))
        
        # Create document name format
        doc_name = f"{full_name} - {referral_code}" if full_name else referral_code

        # Create and save new realtor
        sales_person = frappe.new_doc("Sales Person")
        sales_person.update({
            'sales_person_name': doc_name,
            'custom_full_name': full_name,
            'custom_referral_code': referral_code,
            'custom_first_name': first_name,
            'custom_last_name': last_name,
            'custom_mobile_no': phone,
            'custom_email': email,
            'custom_confirm_email': confirm_email,
            'custom_dob': dob,
            'custom_address': address,
            'custom_gender': gender,
            'custom_city': city,
            'custom_state': state,
            'custom_country': country,
            'custom_account_no': accountno,
            'custom_account_name': accountname,
            'custom_bank': bank,
            'custom_terms': terms,
            'custom_upline_1': upline
        })
        
        sales_person.insert(ignore_permissions=True)
        
        # Create Web User
        if "Sales User" not in frappe.get_roles(email):
            user = frappe.new_doc("User")
            user.update({
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'send_welcome_email': 1,
                'role_profile_name': 'Realtor',
                'module_profile': None,
                'user_type': 'Website User'
            })
            user.insert(ignore_permissions=True)
        
        # Update Sales Person with user ID
        sales_person.custom_user_id = email
        sales_person.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        return success_response(
            initial_url, referral_code
        )
        
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return error_response(initial_url, f"Validation error: {str(e)}")
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(
            title="Realtor Registration Failed",
            message=frappe.get_traceback()
        )
        return error_response(
            initial_url,
            "Registration failed. Please try again or contact support."
        )

def generate_referral_code():
    """Generate a 6-digit incremental referral code"""
    last_code = frappe.db.sql("""
        SELECT MAX(CAST(custom_referral_code AS UNSIGNED))
        FROM `tabSales Person`
        WHERE custom_referral_code REGEXP '^[0-9]+$'
    """)[0][0] or 110000
    
    return str(last_code + 1).zfill(6)

def error_response(redirect_url, message):
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = redirect_url + "?error=" + frappe.utils.quote(message)
    
def success_response(redirect_url, referral_code):
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/confirm_email/" + referral_code

@frappe.whitelist(allow_guest=True)
def get_country():
    country = frappe.get_all('Country', fields=['name', 'code'])
    return country


@frappe.whitelist(allow_guest=True)
def get_bank():
    return frappe.get_all('Bank', filters={'custom_category': 2}, fields=['name'])

@frappe.whitelist()
def get_sales_person(custom_upline=None, upline=None):
    filters = {}
    if upline and custom_upline:
        filters[custom_upline] = upline
    return frappe.get_all(
        'Sales Person', 
        filters=filters, 
        fields=['sales_person_name', 'name', 'enabled', 'custom_full_name', 'custom_mobile_no',
        'creation', 'custom_email', 'custom_commission_upline_1', 'custom_commission_upline_2']
        )
