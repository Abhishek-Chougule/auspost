## Auspost

Australia Post

#### License

MIT

## Delivery Note - Form
        frappe.ui.form.on('Delivery Note', {
            refresh(frm) {
            frm.add_custom_button(__(''), function () {
                if(frm.doc.print_url)
                {
                    window.open(frm.doc.print_url, '_blank');
                }
                else
                {
                    frappe.msgprint('Please First Generate Print Label');
                }
                }).addClass('fa fa-print');
                
                frm.add_custom_button(__('Generate Print Label'), function () {
                    
                    if(frm.doc.shipment_id && frm.doc.item_id)
                    {
                    
                    frappe.call({
                    method: 'auspost.auspost.doctype.auspost_settings.auspost_settings.print_label',
                    args:{'name':frm.doc.name},
                    callback: function(d) {}
                });
                    }
                    else
                    {
                        frappe.msgprint('Please Create Shipment First!');
                    }
                
                });
                    
                frm.add_custom_button(__('Partial/Full Shipment'), function(){
                    frappe.call({
                    method: 'auspost.auspost.doctype.auspost_settings.auspost_settings.send_shipment_toauspost',
                    args:{'name':frm.doc.name},
                    callback: function(d) {}
                });
            }, __("Create"));
            
            frm.add_custom_button(__('Partial Fulfillment'), function(){
                    frappe.call({
                    method: 'auspost.auspost.doctype.auspost_settings.auspost_settings.fulfillment',
                    args:{'shopify_order_id':frm.doc.shopify_order_id,'name':frm.doc.name},
                    callback: function(d) {}
                });
            }, __("Change Fulfillment Status"));
            frm.add_custom_button(__('Complete Fulfillment'), function(){
                    frappe.call({
                    method: 'auspost.auspost.doctype.auspost_settings.auspost_settings.complete_fulfillment',
                    args:{'shopify_order_id':frm.doc.shopify_order_id,'name':frm.doc.name},
                    callback: function(d) {}
                });
            }, __("Change Fulfillment Status"));
            
            
            $(document).ready(function() {
                
                    var divToHide = $('button.text-muted.btn.btn-default.icon-btn');
                    divToHide.hide();
                });
            frm.add_custom_button(__('Complete Shipment'), function(){
                    frappe.call({
                    method: 'auspost.auspost.doctype.auspost_settings.auspost_settings.send_full_shipment_toauspost',
                    args:{'name':frm.doc.name},
                    callback: function(d) {}
                });
            }, __("Create"));
            
                
            }
        }) 