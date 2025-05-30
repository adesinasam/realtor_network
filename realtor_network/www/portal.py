import frappe
from frappe import _
from frappe.website.utils import get_home_page

no_cache = 1

def get_context(context):

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

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

    try:
        realtor = frappe.get_doc("Sales Person", {"custom_user_id": current_user.name})
        if realtor:
            context.realtor = realtor
    except Exception as e:
        pass
    else:
        context.realtor = realtor

    # nav
    context.active_route = "home"

    context.realtor_settings = frappe.call('realtor_network.api.get_realtor_settings')


    return context
