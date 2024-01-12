import os
import pandas as pd
import requests

from arcgis.gis import GIS
from arcgis.features import GeoAccessor, GeoSeriesAccessor, FeatureLayerCollection
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

from arcgis_utils import connect_to_agol, get_flc_by_id, get_layer_data

load_dotenv()

TIDAL_CURRENT_FEATURE_ID = "24f75791829440ffb46b4d15360aec7d"

def call_khoa_api(obs_code: str, datestring: str) -> dict:
    try:
        response = requests.get(
            url="http://www.khoa.go.kr/api/oceangrid/fcTidalCurrent/search.do",
            params={
                "ServiceKey": os.getenv("KHOA_APIKEY"),
                "ObsCode": obs_code,
                "Date":datestring,
                "ResultType": "json"
            }
        )
        return response.json()
    except KeyError as e:
        print(e)

def parse_current_speed(current_speed: str) -> int:
    try:
        return float(current_speed)
    except ValueError:
        print(f"{current_speed} is not a number")
        return 0

def build_update_data(gis: GIS) -> list[dict]:
    layer_data = get_layer_data(gis, TIDAL_CURRENT_FEATURE_ID)
    today = f"{datetime.now():%Y%m%d}"
    for feature in tqdm(layer_data):
        obs_code = feature.attributes["station_no"]
        resp_json = call_khoa_api(obs_code=obs_code, datestring=today)
        try:
            latest_record = resp_json["result"]["data"][-1]
            feature.attributes["pred_time"] = latest_record["pred_time"]
            feature.attributes["current_dir"] = latest_record["current_dir"]
            feature.attributes["current_speed"] = parse_current_speed(latest_record["current_speed"])
        except KeyError as e:
            print(e)
            continue
    return layer_data

def update(gis: GIS, layer_data: list[dict]) -> None:
    layer = get_flc_by_id(gis, TIDAL_CURRENT_FEATURE_ID).layers[0]
    result = layer.edit_features(updates=layer_data)
    return result

if __name__ == "__main__":
    gis = connect_to_agol()
    layer_data = build_update_data(gis=gis)
    updates = update(gis=gis, layer_data=layer_data)
    print(updates)

        