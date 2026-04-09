import json
import os
import ee

key_json = json.loads(os.environ["GEE_KEY"])

credentials = ee.ServiceAccountCredentials(
    key_json["client_email"],   # ✅ lấy từ JSON
    key_data=key_json
)

ee.Initialize(credentials)