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

AIR_PRES_FEATURE_ID = "7c33171a6a2a4771a2438d781459388b"

def call_khoa_api(obs_code: str, datestring: str, datatype: str) -> dict:
    try:
        response = requests.get(
            url=f"http://www.khoa.go.kr/api/oceangrid/{datatype}/search.do",
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
    except requests.exceptions.JSONDecodeError as e:
        print(response)
        print(e)

def parse(value: str) -> int:
    try:
        return float(value)
    except ValueError:
        print(f"{value} is not a number")
        return 0

def build_update_data(gis: GIS) -> list[dict]:
    layer_data = get_layer_data(gis, AIR_PRES_FEATURE_ID)
    today = f"{datetime.now():%Y%m%d}"
    for feature in tqdm(layer_data):
        obs_code = feature.attributes["station_no"]
        obs_type = "tidalBuAirPres" if feature.attributes["obs_type"] == "해양관측부이" else "tideObsAirPres"
        resp_json = call_khoa_api(obs_code=obs_code, datestring=today, datatype=obs_type)
        try:
            latest_record = resp_json["result"]["data"][-1]
            feature.attributes["record_time"] = latest_record["record_time"]
            feature.attributes["air_pres"] = parse(latest_record["air_pres"])
        except KeyError as e:
            print(e)
            continue
    return layer_data

def update(gis: GIS, layer_data: list[dict]) -> None:
    layer = get_flc_by_id(gis, AIR_PRES_FEATURE_ID).layers[0]
    result = layer.edit_features(updates=layer_data)
    return result

if __name__ == "__main__":
    gis = connect_to_agol()
    layer_data = build_update_data(gis=gis)
    updates = update(gis=gis, layer_data=layer_data)
    print(updates)

        