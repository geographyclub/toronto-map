#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta, timezone

# =========================================================
# CONFIG
# =========================================================

OUTPUT_FILE = "data/toronto_events.geojson"

BASE_URL = (
    "https://secure.toronto.ca/"
    "c3api_data/v2/DataAccess.svc/festivals_events/events"
)

CALENDAR_IDS = [
    "a4f795ff-e94f-46bd-a1c3-c94ec1549567",
    "adb9c00b-5f61-4a01-90b5-6cf00d00faf0",
    "ad38461b-1274-4afe-ae3a-320fba6b28b0",
    "66ac8918-922b-4eff-98db-7784bf842523",
    "ee486807-a5e6-44fd-8c98-496caaca50a1",
    "5ec2e57f-03d6-499b-b46c-8f0babf97e0a",
    "3197d23d-c257-4584-89b2-b100f99ce6d4",
    "4a75ca32-c2b0-4baa-a0ee-703cd9e53b03",
    "ae3fcc96-e2eb-4522-95bd-5ba198ccf6de",
    "2603f051-0d4d-48db-95f0-b3061b210efd",
    "82f36b6c-101e-41a9-81c5-1434d7ae673b",
    "da506e92-d63c-43fa-864a-78a53b52f706",
]

# =========================================================
# DATE RANGE (30 DAYS)
# =========================================================

start = datetime.now(timezone.utc)
end = start + timedelta(days=30)

DATE_START = start.strftime("%Y-%m-%dT%H:%M:%SZ")
DATE_END = end.strftime("%Y-%m-%dT%H:%M:%SZ")

TOP = 5000
SKIP = 0

# =========================================================
# FILTER
# =========================================================

calendar_filter = " or ".join(
    [f"calendar_id eq '{x}'" for x in CALENDAR_IDS]
)

filter_query = (
    f"({calendar_filter}) "
    f"and calendar_date ge {DATE_START} "
    f"and calendar_date lt {DATE_END}"
)

params = {
    "$format": "application/json;odata.metadata=none",
    "$skip": str(SKIP),
    "$top": str(TOP),
    "$filter": filter_query,
}

query_string = urllib.parse.urlencode(
    params,
    safe="(),':$",
    quote_via=urllib.parse.quote,
)

url = f"{BASE_URL}?{query_string}"

print("Downloading events...")

req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    },
)

with urllib.request.urlopen(req) as response:
    data = json.load(response)

events = data.get("value", [])

# =========================================================
# GEOJSON BUILD
# =========================================================

features = []

for i, e in enumerate(events):

    loc = (e.get("event_locations") or [None])[0]

    lat = None
    lng = None

    if loc and loc.get("location_gps"):
        try:
            gps = json.loads(loc["location_gps"])[0]
            lat = float(gps.get("gps_lat"))
            lng = float(gps.get("gps_lng"))
        except:
            pass

    if lat is None or lng is None:
        continue

    # =====================================================
    # STABLE ID
    # =====================================================

    raw_id = e.get("id") or e.get("submission_id")
    feature_id = f"event-{raw_id or i}"

    feature = {
        "type": "Feature",

        # optional but useful for MapLibre indexing
        "id": feature_id,

        "geometry": {
            "type": "Point",
            "coordinates": [lng, lat]
        },

        "properties": {

            # ✅ CRITICAL: THIS IS NOW THE MAIN ID
            "id": feature_id,

            "title": e.get("short_name"),
            "description": e.get("short_description"),

            "start": e.get("event_startdate"),
            "end": e.get("event_enddate"),

            "category": e.get("event_category"),
            "subcategory": e.get("event_sub_category"),

            "calendar_name": e.get("calendar_name"),

            "free": e.get("free_event") == "Yes",
            "featured": e.get("featured_event") == "Yes",
            "accessible": e.get("accessible_event") == "Yes",

            "website": e.get("event_website"),
            "tickets": e.get("ticket_website"),

            "image": (
                e.get("event_image")[0]
                if e.get("event_image")
                else None
            ),

            "location_name": loc.get("location_name") if loc else None,
            "location_address": loc.get("location_address") if loc else None,
        }
    }

    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

Path(OUTPUT_FILE).write_text(
    json.dumps(geojson, indent=2),
    encoding="utf-8",
)

print(f"Saved to: {OUTPUT_FILE}")
print(f"Features: {len(features)}")