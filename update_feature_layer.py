import os
import requests
import time
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

# Connect with credentials from environment
gis = GIS(
    "https://www.arcgis.com",
    os.environ["ARCGIS_USER"],
    os.environ["ARCGIS_PASS"]
)

# Use direct feature layer URL instead of search
layer = FeatureLayer(os.environ["FEATURE_LAYER_URL"])

param_map = {
    "00010": "temp_c",
    "00095": "spec_cond",
    "00300": "do_mgL",
    "00400": "ph",
    "32295": "no3_no2",
    "63680": "turb_ntu"
}

url = (
    "https://waterservices.usgs.gov/nwis/iv/?format=json"
    "&huc=17090011&siteStatus=active"
    "&parameterCd=" + ",".join(param_map.keys()) +
    "&period=P1D"
)

response = requests.get(url, headers={"Cache-Control": "no-cache"})
response.raise_for_status()
data = response.json()

features = {}

for ts in data["value"]["timeSeries"]:
    site = ts["sourceInfo"]["siteCode"][0]["value"]
    name = ts["sourceInfo"]["siteName"]
    lat = float(ts["sourceInfo"]["geoLocation"]["geogLocation"]["latitude"])
    lon = float(ts["sourceInfo"]["geoLocation"]["geogLocation"]["longitude"])
    param = ts["variable"]["variableCode"][0]["value"]

    values = ts["values"][0]["value"]
    if not values or param not in param_map:
        continue

    latest = values[-1]

    if site not in features:
        features[site] = {
            "attributes": {
                "site_no": site,
                "site_name": name,
                "datetime": latest["dateTime"]
            },
            "geometry": {"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}
        }

    features[site]["attributes"][param_map[param]] = float(latest["value"])

# Update layer
layer.delete_features(where="1=1")
result = layer.edit_features(adds=list(features.values()))

print(f"Updated {len(features)} sites at {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
