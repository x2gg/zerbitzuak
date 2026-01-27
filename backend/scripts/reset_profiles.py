#!/usr/bin/env python3
import requests
import os

APISIX_ADMIN_URL = os.getenv("APISIX_ADMIN_URL", "http://localhost:9180")
APISIX_ADMIN_KEY = os.getenv("APISIX_ADMIN_KEY", "edd1c9f034335f136f87ad84b625c8f1")

headers = {
	"X-API-KEY": APISIX_ADMIN_KEY,
	"Content-Type": "application/json"
}

def delete_consumer_group(group_name):
	url = f"{APISIX_ADMIN_URL}/apisix/admin/consumer_groups/{group_name}"
	response = requests.delete(url, headers=headers)
	return response.status_code in [200, 404]

# Limpiar grupos existentes
for group in ["basic", "pro"]:
	if delete_consumer_group(group):
		print(f"✅ Deleted consumer group: {group}")
	else:
		print(f"❌ Failed to delete consumer group: {group}")

print("\nNow you can create fresh profiles via the API")