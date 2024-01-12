import os
import pandas as pd
import requests

from arcgis.gis import GIS
from arcgis.features import GeoAccessor, GeoSeriesAccessor, FeatureLayerCollection
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

from arcgis_utils import connect_to_agol, get_flc_by_id, get_layer_data

TIDE_LEVEL_FEATURE_ID = "c2c42c28c50e4fd8b1838835d0e7b17c"

def call_khoa_api(obs_code: str, datestring: str) -> dict:
    response = requests.get(
        url="http://www.khoa.go.kr/api/oceangrid/tideObs/search.do",
        params={
            "ServiceKey": os.getenv("KHOA_APIKEY"),
            "ObsCode": obs_code,
            "Date":datestring,
            # "ResultType": "json"
        }
    )
    return response.json()

def parse_tide_level(tide_level: str) -> int:
    try:
        return int(float(tide_level))
    except ValueError:
        print(f"{tide_level} is not an integer")
        return 0

def build_update_data(gis: GIS) -> list[dict]:
    layer_data = get_layer_data(gis, TIDE_LEVEL_FEATURE_ID)
    today = f"{datetime.now():%Y%m%d}"
    for feature in tqdm(layer_data):
        obs_code = feature.attributes["station_no"]
        resp_json = call_khoa_api(obs_code=obs_code, datestring=today)
        latest_record = resp_json["result"]["data"][-1]
        feature.attributes["record_time"] = latest_record["record_time"]
        feature.attributes["tide_level"] = parse_tide_level(latest_record["tide_level"])
    return layer_data

def update(gis: GIS, layer_data: list[dict]) -> list[dict]:
    layer = get_flc_by_id(gis, TIDE_LEVEL_FEATURE_ID).layers[0]
    results = layer.edit_features(updates=layer_data)
    return results

if __name__ == "__main__":
    gis = connect_to_agol()
    layer_data = build_update_data(gis=gis)
    updates = update(gis=gis, layer_data=layer_data)
    print(updates)

        