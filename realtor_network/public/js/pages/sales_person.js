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