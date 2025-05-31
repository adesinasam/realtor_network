import frappe
from frappe import _
from frappe.website.utils import get_home_page

no_cache = 1

def get_context(context):

    docname = frappe.form_dict.get('docname')

    context.docname = None
    context.referral = None

    if docname:
        try:
            sales_person = frappe.get_doc("Sales Person", {"custom_referral_code": docname})
            if sales_person:
                context.docname = docname
                context.referral = sales_person
        except Exception:
            pass  # Silently ignore the error

    # Fetch the current user's details
    current_user = frappe.get_doc("User", frappe.session.user)
    context.current_user = current_user

    # Fetch the roles of the current user
    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles

    # Split the company name into parts
    parts = current_user.full_name.split(" ")

    # Create the abbreviation by taking the first letter of each part
    context.abbr = "".join([p[0] for p in parts[:2] if p])

    # nav
    context.active_route = "clients"

    context.realtor_settings = frappe.call('realtor_network.api.get_realtor_settings')

    context.countrys = frappe.call('realtor_network.api.get_country')

    context.banks= frappe.call('realtor_network.api.get_bank')

    return context
