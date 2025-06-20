
import json

import frappe
from frappe import _
import time
from frappe.utils import random_string, now
from frappe.utils import get_url
from frappe.email.doctype.email_group.email_group import add_subscribers
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, getdate, nowdate
from frappe.utils.dateutils import get_dates_from_timegrain
from datetime import datetime
from frappe.utils import random_string, getdate, now_datetime
from frappe.utils.password import get_decrypted_password


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

@frappe.whitelist(allow_guest=True)
def get_realtor_item():
    return frappe.get_all(
        'Realtor Item', 
        filters={'published': 1}, 
        fields=['*'])


@frappe.whitelist()
def create_user_for_sales_person(sales_person_name=None, batch_size=100, delay=0.1):
    try:
        # Convert parameters to correct types
        batch_size = int(batch_size) if batch_size else 100
        delay = float(delay) if delay else 0.1
        
        if sales_person_name:
            return create_single_user(sales_person_name)
        else:
            return create_users_in_batch(batch_size, delay)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error creating user for Sales Person"))
        frappe.db.rollback()
        return {"error": str(e)}

def create_single_user(sales_person_name):
    try:
        sales_person = frappe.get_doc("Sales Person", str(sales_person_name))
        
        if sales_person.custom_user_id:
            return {"skipped": _("User already exists for this Sales Person")}
        
        user_data = prepare_user_data(sales_person)
        
        # Check if user exists first
        if frappe.db.exists("User", user_data['email']):
            return {"skipped": _("User with email {0} already exists").format(user_data['email'])}
        
        # Get current timestamp
        current_time = now_datetime()
        
        # Create user directly in DB
        frappe.db.sql("""
            INSERT INTO `tabUser` 
            (`name`, `email`, `first_name`, `username`, `phone`, `send_welcome_email`, 
             `role_profile_name`, `user_type`, `creation`, `modified`, `modified_by`, `owner`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            user_data['email'],
            user_data['email'],
            user_data['first_name'],
            user_data['username'],
            user_data['phone'],
            0,
            'Realtor',
            'Website User',
            current_time,
            current_time,
            frappe.session.user,
            frappe.session.user
        ])
        
        # Add role directly
        frappe.db.sql("""
            INSERT INTO `tabHas Role` 
            (`name`, `parent`, `parentfield`, `parenttype`, `role`, `modified_by`, `owner`)
            VALUES (%s, %s, 'roles', 'User', 'Realtor', %s, %s)
        """, [
            frappe.generate_hash(length=10),
            user_data['email'],
            frappe.session.user,
            frappe.session.user
        ])
        
        # Update sales person
        frappe.db.set_value("Sales Person", sales_person.name, "custom_user_id", user_data['email'])
        
        return {"success": _("User created successfully"), "user_id": user_data['email']}
    
    except Exception as e:
        return {"error": str(e)}

def create_users_in_batch(batch_size=100, delay=0.1):
    try:
        # Ensure batch_size is integer
        batch_size = int(batch_size)
        sales_persons = frappe.get_all("Sales Person",
            filters={
            "custom_user_id": ["in", ["", None]],
            "is_group": 0
            },
            fields=["name"],
            limit=batch_size
        )
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        for i, sp in enumerate(sales_persons):
            try:
                if i > 0:
                    time.sleep(float(delay))  # Ensure delay is float
                    
                result = create_single_user(sp.name)
                
                if result.get("success"):
                    created_count += 1
                elif result.get("skipped"):
                    skipped_count += 1
                elif result.get("error"):
                    errors.append(f"{sp.name}: {result['error']}")
                    
            except Exception as e:
                skipped_count += 1
                errors.append(f"{sp.name}: {str(e)}")
                frappe.log_error(title=f"Failed to create user for {sp.name}")
        
        frappe.db.commit()
        
        return {
            "message": _("Batch user creation completed"),
            "created": created_count,
            "skipped": skipped_count,
            "errors": errors if errors else None
        }
    except Exception as e:
        frappe.db.rollback()
        return {"error": str(e)}

def prepare_user_data(sales_person):
    # Convert all values to strings explicitly
    email = str(sales_person.custom_email or f"{sales_person.name}@example.com").strip().lower()
    first_name = str(sales_person.custom_first_name or sales_person.name).strip()
    phone = str(sales_person.custom_mobile_no or "").strip()
    username = str(sales_person.custom_referral_code or frappe.generate_hash(length=8)).strip().lower()
    
    # Validate email format
    if "@" not in email:
        email = f"{sales_person.name}@example.com"
    
    return {
        'email': email,
        'first_name': first_name[:50],  # Truncate to 50 chars
        'username': username[:20],     # Truncate to 20 chars
        'phone': phone[:20]            # Truncate to 20 chars
    }
