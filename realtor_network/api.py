
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
