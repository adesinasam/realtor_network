frappe.ui.form.on('Sales Person', {
    // Uppercase conversion for first and last names
    custom_first_name: function(frm) {
        if (frm.doc.custom_first_name) {
            frm.set_value('custom_first_name', 
                frm.doc.custom_first_name.toUpperCase().trim());
        }
        update_sales_person_name(frm);
    },
    custom_last_name: function(frm) {
        if (frm.doc.custom_last_name) {
            frm.set_value('custom_last_name', 
                frm.doc.custom_last_name.toUpperCase().trim());
        }
        update_sales_person_name(frm);
    },
    refresh: function(frm) {
        // Initialize if empty
        if (!frm.doc.sales_person_name && 
            (frm.doc.custom_first_name || frm.doc.custom_last_name)) {
            update_sales_person_name(frm);
        }
    }
});

function update_sales_person_name(frm) {
    let name_parts = [];
    if (frm.doc.custom_first_name) {
        name_parts.push(frm.doc.custom_first_name.trim());
    }
    if (frm.doc.custom_last_name) {
        name_parts.push(frm.doc.custom_last_name.trim());
    }
    
    if (name_parts.length > 0) {
        let new_name = name_parts.join(' ');
        if (frm.doc.sales_person_name !== new_name) {
            frm.set_value('sales_person_name', new_name);
        }
    }
}

frappe.ui.form.on('Sales Person', {
    custom_first_name: function(frm) {
        update_sales_person_name(frm);
    },
    custom_last_name: function(frm) {
        update_sales_person_name(frm);
    }
});

function update_sales_person_name(frm) {
    // Combine first and last name for initial sales_person_name
    let name_parts = [];
    if (frm.doc.custom_first_name) {
        name_parts.push(frm.doc.custom_first_name.trim());
    }
    if (frm.doc.custom_last_name) {
        name_parts.push(frm.doc.custom_last_name.trim());
    }
    
    if (name_parts.length > 0) {
        frm.set_value('sales_person_name', name_parts.join(' '));
    }
}

frappe.ui.form.on('Sales Person', {
    custom_email: function(frm) {
        validate_email_match(frm);
    },
    custom_confirm_email: function(frm) {
        validate_email_match(frm);
    }
});

function validate_email_match(frm) {
    if (frm.doc.custom_email && frm.doc.custom_confirm_email) {
        if (frm.doc.custom_email.toLowerCase() !== frm.doc.custom_confirm_email.toLowerCase()) {
            frappe.msgprint({
                title: __('Email Mismatch'),
                indicator: 'red',
                message: __('Email addresses do not match. Please ensure both fields are identical.')
            });
            // Optional: Highlight the fields
            frm.fields_dict['custom_email'].df.is_dirty = true;
            frm.fields_dict['custom_confirm_email'].df.is_dirty = true;
            frm.refresh_fields(['custom_email', 'custom_confirm_email']);
        }
    }
}
