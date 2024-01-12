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

SEAFOG_FEATURE_ID = "e6e10d2d56004bd2ac0914842d19769f"

def call_khoa_api(obs_code: str, datestring: str) -> dict:
    try:
        response = requests.get(
            url="http://www.khoa.go.kr/api/oceangrid/seafog/search.do",
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

def parse(value: str) -> int:
    try:
        return int(float(value))
    except ValueError:
        print(f"{value} is not a number")
        return 0

def build_update_data(gis: GIS) -> list[dict]:
    layer_data = get_layer_data(gis, SEAFOG_FEATURE_ID)
    today = f"{datetime.now():%Y%m%d%H}"
    for feature in tqdm(layer_data):
        obs_code = feature.attributes["station_no"]
        resp_json = call_khoa_api(obs_code=obs_code, datestring=today)
        try:
            latest_record = resp_json["result"]["data"][-1]
            feature.attributes["pre_time"] = latest_record["pre_time"]
            feature.attributes["seafog_master"] = parse(latest_record["seafog_master"])
        except KeyError as e:
            print(resp_json)
            continue
    return layer_data

def update(gis: GIS, layer_data: list[dict]) -> None:
    layer = get_flc_by_id(gis, SEAFOG_FEATURE_ID).layers[0]
    result = layer.edit_features(updates=layer_data)
    return result

if __name__ == "__main__":
    gis = connect_to_agol()
    layer_data = build_update_data(gis=gis)
    updates = update(gis=gis, layer_data=layer_data)
    print(updates)

        