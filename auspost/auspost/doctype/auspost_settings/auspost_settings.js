// Copyright (c) 2023, Abhishek Chougule and contributors
// For license information, please see license.txt

frappe.ui.form.on('AusPost Settings', {
	before_save: function(frm) {
		frappe.call({
			method:'converttobase64',
			doc:frm.doc,
			callback:{}
		});
	},
	sync_now: function(frm) {
		frappe.call({
			method:'sync_auspost_shipments',
			doc:frm.doc,
			callback:{}
		});
	}
	
});
