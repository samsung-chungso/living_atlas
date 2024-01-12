import os

from arcgis.gis import GIS
from arcgis.features import GeoAccessor, GeoSeriesAccessor, FeatureLayerCollection
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def connect_to_agol() -> GIS:
    """
    환경변수로 저장된 정보로 사내포털에 로그인
    """
    _ID = os.getenv("ESRIKR_ID")
    _PW = os.getenv("ESRIKR_PW")
    gis = GIS(url=os.getenv("ESRIKR_URL"), username=_ID, password=_PW)
    
    return gis

def get_flc_by_id(gis: GIS, id: str) -> FeatureLayerCollection:
    """
    매개변수로 받은 GIS에서 피처의 ID로 쿼리된 FeatureLayerCollection을 반환
    """
    flc = gis.content.search(
        query=f"id:{id}",
        item_type="Feature Layer Collection",
    )
    if len(flc) == 0:
        raise RuntimeError("주어진 ID에 해당하는 피처가 없습니다. ID를 다시 확인하세요.")
    return flc[0]

def get_layer_data(gis: GIS, feature_id: str) -> list:
    feature_layer = get_flc_by_id(gis, feature_id)
    layer = feature_layer.layers[0]
    layer_data = layer.query().features
    
    return layer_data
