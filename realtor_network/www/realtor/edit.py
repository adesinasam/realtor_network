import frappe
from frappe import _
from frappe.website.utils import get_home_page

no_cache = 1

def get_context(context):
    docname = frappe.form_dict.get('docname')

    context.docname = None
    context.realtor_doc = None

    # Login check
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    # Fetch the current user's details
    current_user = frappe.get_doc("User", frappe.session.user)
    context.current_user = current_user

    # Fetch the roles of the current user
    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles

    # Check if user has required roles
    has_realtor_role = "Realtor User" in user_roles
    has_realtor_manager_role = "Realtor Manager" in user_roles
    
    if not (has_realtor_role or has_realtor_manager_role):
        frappe.throw(_("You need to be a Realtor or Realtor Manager to access this page"), frappe.PermissionError)

    # Only allow docname access if user is Realtor Manager or it's their own record
    if docname:
        try:
            # Check if user has permission to view this Sales Person
            if has_realtor_manager_role:
                # Realtor Manager can view any Sales Person
                sales_person = frappe.get_doc("Sales Person", docname)
            else:
                # Regular realtor can only view their own record
                sales_person = frappe.get_doc("Sales Person", {"custom_user_id": current_user.name})

            if sales_person:
                context.docname = docname
                context.realtor_doc = sales_person
                # Fetch the sales_person user's details
                context.sales_person_user = frappe.get_doc("User", sales_person.custom_user_id)
                
        except Exception as e:
            frappe.log_error(f"Error fetching Sales Person: {str(e)}")
            pass  # Silently ignore the error

    if sales_person.name != docname:
        frappe.throw(_("You can only view your own profile"), frappe.PermissionError)

    # Split the company name into parts
    parts = current_user.full_name.split(" ")
    context.abbr = "".join([p[0] for p in parts[:2] if p])

    # Get realtor record for current user
    try:
        realtor = frappe.get_doc("Sales Person", {"custom_user_id": current_user.name})
        context.realtor = realtor
    except Exception as e:
        context.realtor = None
        # Don't throw error here as user might not have a Sales Person record yet

    # Navigation
    context.active_route = "Realtors"
    context.active_subroute = "Edit"

    # API calls with error handling
    try:
        context.realtor_settings = frappe.call('realtor_network.api.get_realtor_settings')
    except Exception as e:
        context.realtor_settings = {}
        frappe.log_error(f"Error getting realtor settings: {str(e)}")

    try:
        context.countrys = frappe.call('realtor_network.api.get_country')
    except Exception as e:
        context.countrys = []
        frappe.log_error(f"Error getting countries: {str(e)}")

    try:
        context.banks = frappe.call('realtor_network.api.get_bank')
    except Exception as e:
        context.banks = []
        frappe.log_error(f"Error getting banks: {str(e)}")

    # Fetch courses based on the selected section, if any
    success = frappe.form_dict.get('success')
    if success:
        context.success = success
    else:
        context.success = None

    error = frappe.form_dict.get('error')
    if error:
        context.error = error
    else:
        context.error = None

    return context