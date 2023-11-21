# Copyright (c) 2023, Abhishek Chougule and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import base64 
import requests
import json
from datetime import datetime
from frappe.utils.password import get_decrypted_password

@frappe.whitelist()
def complete_fulfillment(shopify_order_id,name):
	ocs=frappe.get_doc('Shopify Setting')
	source_token = get_decrypted_password('Shopify Setting', ocs.name, 'password')

	aps=frappe.get_doc('AusPost Settings')
	current_doc = frappe.get_doc('Delivery Note', name)
	if not current_doc.tracking_number:
		frappe.msgprint('First Need to Create the Shipment !')
	else:
		account_number=str(aps.account_number)
		authorization=str(aps.authorization)

		shs=frappe.get_doc('Shopify Setting')
		shopify_url=shs.shopify_url
		url = f"https://{shopify_url}/admin/api/2023-07/orders/{shopify_order_id}/fulfillment_orders.json?status=in_progress"

		headers = {
		'X-Shopify-Access-Token': source_token,
		'Content-Type': 'application/json'
		}

		response = requests.request("GET", url, headers=headers)

		json_response = response.json()
		
		fulfillment_order_id=str(json_response['fulfillment_orders'][0]['line_items'][0]['fulfillment_order_id'])
		mid=str(json_response['fulfillment_orders'][0]['line_items'][0]['id'])
		
		url = "https://2a5073-4.myshopify.com/admin/api/2023-04/fulfillments.json"

		payload = json.dumps({
		"fulfillment": {
			"line_items_by_fulfillment_order": [
			{
				"fulfillment_order_id": fulfillment_order_id,
				"fulfillment_order_line_items":[{
					"id":mid,
					"quantity":1
				}]
			}
			]
		}
		})
		
		response = requests.request("POST", url, headers=headers, data=payload)

		if response.status_code==201:
			frappe.msgprint('Order Fulfilled !')
		else:
			frappe.msgprint('Order Not Fulfilled !')
@frappe.whitelist()
def fulfillment(shopify_order_id,name):

	ocs=frappe.get_doc('Shopify Setting')
	source_token = get_decrypted_password('Shopify Setting', ocs.name, 'password')

	aps=frappe.get_doc('AusPost Settings')
	current_doc = frappe.get_doc('Delivery Note', name)
	total_items=0
	

	if not current_doc.tracking_number:
		frappe.msgprint('First Need to Create the Shipment !')
	else:
		account_number=str(aps.account_number)
		authorization=str(aps.authorization)

		shs=frappe.get_doc('Shopify Setting')
		shopify_url=shs.shopify_url
		url = f"https://{shopify_url}/admin/api/2023-07/orders/{shopify_order_id}/fulfillment_orders.json?status=open"

		headers = {
		'X-Shopify-Access-Token': source_token,
		'Content-Type': 'application/json'
		}

		response = requests.request("GET", url, headers=headers)

		json_response = response.json()
		
		for total in current_doc.items:
			
			fulfillment_order_id=str(json_response['fulfillment_orders'][total_items]['line_items'][total_items]['fulfillment_order_id'])
			mid=str(json_response['fulfillment_orders'][total_items]['line_items'][total_items]['id'])
			
			url = "https://2a5073-4.myshopify.com/admin/api/2023-04/fulfillments.json"
			item_code_to_check = total.item_code
			item_stock = get_item_stock(item_code_to_check)

			# frappe.msgprint(str(item_stock))
			# frappe.msgprint(str(total.qty))
			
			if item_stock>=total.qty:	
				payload = json.dumps({
				"fulfillment": {
					"line_items_by_fulfillment_order": [
					{
						"fulfillment_order_id": fulfillment_order_id,
						"fulfillment_order_line_items":[{
							"id":mid,
							"quantity":int(total.qty)
						}]
					}
					]
				}
				})
			elif item_stock!=0 and item_stock<=total.qty:
				payload = json.dumps({
				"fulfillment": {
					"line_items_by_fulfillment_order": [
					{
						"fulfillment_order_id": fulfillment_order_id,
						"fulfillment_order_line_items":[{
							"id":mid,
							"quantity":int(item_stock)
						}]
					}
					]
				}
				})
			response = requests.request("POST", url, headers=headers, data=payload)

			if response.status_code==201:
				frappe.msgprint('Order Fulfilled !')
			else:
				frappe.msgprint('Order Not Fulfilled !')
			total_items+=1

def get_item_stock(item_code):
    stock = frappe.get_value('Stock Ledger Entry', 
                             {'item_code': item_code},
                             'SUM(actual_qty)')
    return stock or 0

@frappe.whitelist()
def send_full_shipment_toauspost(name):
	
	aps=frappe.get_doc('AusPost Settings')
	current_doc = frappe.get_doc('Delivery Note', name)
	add=frappe.get_doc('Address',current_doc.shipping_address_name)
	state_mapping = {
		'New South Wales': 'NSW',
		'Victoria': 'VIC',
		'Northern Territory': 'NT',
		'Western Australia': 'WA',
		'Australian Capital Territory': 'ACT',
		'Queensland': 'QLD',
		'Tasmania': 'TAS',
		'South Australia': 'SA'
	}

	if add.state in state_mapping:
		state_code = state_mapping[add.state]

	order_data = {
		"order_reference": name,
		"payment_method": "CHARGE_TO_ACCOUNT",
		"shipments": [
			{
				"shipment_reference": name,
				"customer_reference_1": current_doc.customer,
				"customer_reference_2": "SKU-1",
				"email_tracking_enabled": True,
				"from": {
					"name": aps.full_name,
					"lines": [aps.lines],
					"suburb": aps.suburb,
					"state": aps.state,
					"postcode": aps.postcode,
					"phone": aps.phone if aps.phone else "",
					"email": aps.email if aps.email else ""
				},
				"to": {
					"name": current_doc.customer,
					"business_name": '',
					"lines": [add.address_line1],
					"suburb": add.city,
					"state": str(state_code),
					"postcode": add.pincode,
					"phone": add.phone,
					"email": add.email_id
				},
				"items": []
			}
		]
	}

	
	for item in current_doc.items:
		it=frappe.get_doc('Item',item.item_code)
		item_code_to_check = item.item_code
		item_stock = get_item_stock(item_code_to_check)

		length=current_doc.length
		width=current_doc.width
		height=current_doc.height
		if item_stock>=item.qty:
			item_data = {
				"item_reference": item.item_code,
				"product_id": str(aps.product_id),
				"length": str(length),
				"height": str(height),
				"width": str(width),
				"weight": str(item.qty*it.weight_per_unit),
				"authority_to_leave": False,  
				"allow_partial_delivery": True, 
				"features": {
					"TRANSIT_COVER": {
						"attributes": {
							"cover_amount": 0
						}
					}
				}
			}
			order_data["shipments"][0]["items"].append(item_data)
		else:
			sup=frappe.get_doc('Item Group',it.item_group)
			
			po = frappe.get_doc(
			doctype='Purchase Order', 
			supplier=sup.supplier_info,
			shopify_order_id=current_doc.shopify_order_id,
			shopify_order_number=current_doc.shopify_order_number,
			customer_email=add.email_id,
			)
			
			itemss = [
				{"doctype": "Items", "item_code": item.item_code, 'schedule_date': frappe.utils.today(), "qty": item.qty, "rate":item.rate if item.rate!=0 else 1},
				]
			po.set("items", itemss)
			po.insert()
			po.save()
			frappe.msgprint(f"Created Purchase Order for {item.item_name} ({item_code_to_check}) with quantity : {item.qty}")
		
			
	account_number=str(aps.account_number)
	authorization=str(aps.authorization)
	
	url = "https://digitalapi.auspost.com.au/shipping/v1/shipments"

	json_data = json.dumps(order_data)
	headers = {
	'Content-Type': 'application/json',
	'account-number': account_number,
	'Authorization': authorization
	}

	response = requests.request("POST", url, headers=headers, data=json_data)

	json_response = response.json()

	if response.status_code==201:
		frappe.msgprint('Shipment Created')
		current_doc.tracking_number=str(json_response['shipments'][0]['items'][0]['tracking_details']['article_id'])
		current_doc.save()
	else:
		frappe.msgprint('Required stock quantity is not available ! Try Partial/Full Shipment.')

@frappe.whitelist()
def send_shipment_toauspost(name):
	
	aps=frappe.get_doc('AusPost Settings')
	current_doc = frappe.get_doc('Delivery Note', name)
	add=frappe.get_doc('Address',current_doc.shipping_address_name)
	state_mapping = {
		'New South Wales': 'NSW',
		'Victoria': 'VIC',
		'Northern Territory': 'NT',
		'Western Australia': 'WA',
		'Australian Capital Territory': 'ACT',
		'Queensland': 'QLD',
		'Tasmania': 'TAS',
		'South Australia': 'SA'
	}

	if add.state in state_mapping:
		state_code = state_mapping[add.state]

	order_data = {
		"order_reference": name,
		"payment_method": "CHARGE_TO_ACCOUNT",
		"shipments": [
			{
				"shipment_reference": name,
				"customer_reference_1": current_doc.customer,
				"customer_reference_2": "SKU-1",
				"email_tracking_enabled": True,
				"from": {
					"name": aps.full_name,
					"lines": [aps.lines],
					"suburb": aps.suburb,
					"state": aps.state,
					"postcode": aps.postcode,
					"phone": aps.phone if aps.phone else "",
					"email": aps.email if aps.email else ""
				},
				"to": {
					"name": current_doc.customer,
					"business_name": '',
					"lines": [add.address_line1],
					"suburb": add.city,
					"state": str(state_code),
					"postcode": add.pincode,
					"phone": add.phone,
					"email": add.email_id
				},
				"items": []
			}
		]
	}

	
	for item in current_doc.items:
		it=frappe.get_doc('Item',item.item_code)
		item_code_to_check = item.item_code
		item_stock = get_item_stock(item_code_to_check)

		length=current_doc.length
		width=current_doc.width
		height=current_doc.height
		if item_stock>=item.qty:
			item_data = {
				"item_reference": item.item_code,
				"product_id": str(aps.product_id),
				"length": str(length),
				"height": str(height),
				"width": str(width),
				"weight": str(item.qty*it.weight_per_unit),
				"authority_to_leave": False,  
				"allow_partial_delivery": True, 
				"features": {
					"TRANSIT_COVER": {
						"attributes": {
							"cover_amount": 0
						}
					}
				}
			}
			order_data["shipments"][0]["items"].append(item_data)
		elif item_stock>0:
			item_data = {
				"item_reference": item.item_code,
				"product_id": str(aps.product_id),
				"length": str(length),
				"height": str(height),
				"width": str(width),
				"weight": str(item_stock*it.weight_per_unit),
				"authority_to_leave": False,  
				"allow_partial_delivery": True, 
				"features": {
					"TRANSIT_COVER": {
						"attributes": {
							"cover_amount": 0
						}
					}
				}
			}
			order_data["shipments"][0]["items"].append(item_data)

			sup=frappe.get_doc('Item Group',it.item_group)
			
			po = frappe.get_doc(
			doctype='Purchase Order', 
			supplier=sup.supplier_info,
			shopify_order_id=current_doc.shopify_order_id,
			shopify_order_number=current_doc.shopify_order_number,
			customer_email=add.email_id,
			)
			
			itemss = [
				{"doctype": "Items", "item_code": item.item_code, 'schedule_date': frappe.utils.today(), "qty": item.qty-item_stock, "rate":item.rate if item.rate!=0 else 1},
				]
			po.set("items", itemss)
			po.insert()
			po.save()
			frappe.msgprint(f"Created Purchase Order for {item.item_name} ({item_code_to_check}) with quantity : {item.qty-item_stock}")
		else:
			sup=frappe.get_doc('Item Group',it.item_group)
			
			po = frappe.get_doc(
			doctype='Purchase Order', 
			supplier=sup.supplier_info,
			shopify_order_id=current_doc.shopify_order_id,
			shopify_order_number=current_doc.shopify_order_number,
			customer_email=add.email_id,
			)
			
			itemss = [
				{"doctype": "Items", "item_code": item.item_code, 'schedule_date': frappe.utils.today(), "qty": item.qty, "rate":item.rate if item.rate!=0 else 1},
				]
			po.set("items", itemss)
			po.insert()
			po.save()
			frappe.msgprint(f"Created Purchase Order for {item.item_name} ({item_code_to_check}) with quantity : {item.qty}")
		
			
	account_number=str(aps.account_number)
	authorization=str(aps.authorization)
	
	url = "https://digitalapi.auspost.com.au/shipping/v1/shipments"

	json_data = json.dumps(order_data)
	headers = {
	'Content-Type': 'application/json',
	'account-number': account_number,
	'Authorization': authorization
	}

	response = requests.request("POST", url, headers=headers, data=json_data)

	json_response = response.json()
	if response.status_code==201:
		frappe.msgprint('Shipment Created')
		current_doc.tracking_number=str(json_response['shipments'][0]['items'][0]['tracking_details']['article_id'])
		current_doc.save()
	else:
		if 'errors' in json_response and json_response['errors']:
			error_message = json_response['errors'][0]['message']
			frappe.msgprint(str(error_message))

class AusPostSettings(Document):
	@frappe.whitelist()
	def sync_auspost_shipments(self):
		account_number=str(self.account_number)
		authorization=str(self.authorization)
		url = "https://digitalapi.auspost.com.au/shipping/v1/shipments"

		payload = {}
		headers = {
		'account-number': account_number,
		'Authorization': authorization
		}

		response = requests.request("GET", url, headers=headers, data=payload)

		if response.status_code == 200:
			data = response.json()
    
			for shipment_data in data["shipments"]:
				
				erpnext_data = {
					 "shipment_id": shipment_data.get("shipment_id"),
            "shipment_creation_date": datetime.fromisoformat(shipment_data.get("shipment_creation_date", "")).strftime('%Y-%m-%d %H:%M:%S'),
            "customer_reference_1": shipment_data.get("customer_reference_1", ""),
            "customer_reference_2": shipment_data.get("customer_reference_2", ""),
            "email_tracking_enabled": shipment_data.get("email_tracking_enabled", False),
            "fromtype": shipment_data["from"].get("type", ""),
            "fromlines": ", ".join(shipment_data["from"].get("lines", [])),
            "fromsuburb": shipment_data["from"].get("suburb", ""),
            "frompostcode": shipment_data["from"].get("postcode", ""),
            "fromstate": shipment_data["from"].get("state", ""),
            "fromname": shipment_data["from"].get("name", ""),
            "frombusiness_name": shipment_data["from"].get("business_name", ""),
            "fromcountry": shipment_data["from"].get("country", ""),
            "fromemail": shipment_data["from"].get("email", ""),
            "fromphone": shipment_data["from"].get("phone", ""),
            "totype": shipment_data["to"].get("type", ""),
            "tolines": ", ".join(shipment_data["to"].get("lines", [])),
            "tosuburb": shipment_data["to"].get("suburb", ""),
            "topostcode": shipment_data["to"].get("postcode", ""),
            "tostate": shipment_data["to"].get("state", ""),
            "toname": shipment_data["to"].get("name", ""),
            "tocountry": shipment_data["to"].get("country", ""),
            "toemail": shipment_data["to"].get("email", ""),
            "tophone": shipment_data["to"].get("phone", ""),
            "todelivery_instructions": shipment_data["to"].get("delivery_instructions", ""),
            "shipment_summary_total_cost": shipment_data["shipment_summary"].get("total_cost", 0),
            "shipment_summary_total_cost_ex_gst": shipment_data["shipment_summary"].get("total_cost_ex_gst", 0),
            "shipping_cost": shipment_data["shipment_summary"].get("shipping_cost", 0),
            "fuel_surcharge": shipment_data["shipment_summary"].get("fuel_surcharge", 0),
            "shipment_summary_total_gst": shipment_data["shipment_summary"].get("total_gst", 0),
            "shipment_summary_status": shipment_data["shipment_summary"].get("status", ""),
            "number_of_items": shipment_data["shipment_summary"].get("number_of_items", 0),
            "movement_type": shipment_data.get("movement_type", ""),
            "charge_to_account": shipment_data.get("charge_to_account", ""),
            "shipment_modified_date": datetime.fromisoformat(shipment_data.get("shipment_modified_date", "")).strftime('%Y-%m-%d %H:%M:%S'),
        }

				existing_record = frappe.get_all("AusPost Shipment", filters={"shipment_id": shipment_data["shipment_id"]})

				if existing_record:
					erpnext_data["name"] = existing_record[0]["name"]
					frappe.set_value("AusPost Shipment", existing_record[0]["name"], erpnext_data)
				else:
					frappe.get_doc({"doctype": "AusPost Shipment", **erpnext_data}).insert()

		else:
			frappe.msgprint(f"Error: {response.status_code} - {response.text}")

	@frappe.whitelist()
	def converttobase64(self):
		main_string = str(self.username)+':'+str(self.password)
		main_string_bytes = main_string.encode("ascii") 
		
		base64_bytes = base64.b64encode(main_string_bytes) 
		base64_string = base64_bytes.decode("ascii") 
		self.authorization='Basic '+str(base64_string)
		
		
		account_number=str(self.account_number)
		authorization=str(self.authorization)
		url = "https://digitalapi.auspost.com.au/shipping/v1/shipments"

		payload = {}
		headers = {
		'account-number': account_number,
		'Authorization': authorization
		}

		response = requests.request("GET", url, headers=headers, data=payload)

		if response.status_code==200:
			if self.status!='Connected.':
				self.status='Connected.'
				frappe.msgprint('AusPost : Connected.')
		else:
			self.status='Authentication Failed !'
			frappe.msgprint('Authentication Failed !')