from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any
import json

app = FastAPI(title="LA Zoning Lookup API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ZIMAS_BASE_URL = "https://maps.zimas.lacity.org/arcgis/rest/services/ZIMAS/MapServer"
GEOCODE_URL = f"{ZIMAS_BASE_URL}/find"
PARCEL_QUERY_URL = f"{ZIMAS_BASE_URL}/105/query"

class AddressRequest(BaseModel):
    address: str

class ZoningResponse(BaseModel):
    apn: str
    zone: Optional[str] = None
    height_district: Optional[str] = None
    toc_tier: Optional[str] = None
    overlays: Dict[str, Any] = {}
    rent_stabilization: bool = False
    hazards: Dict[str, bool] = {}
    raw_data: Optional[Dict] = None

async def geocode_address(address: str) -> Optional[str]:
    """Geocode address to APN using ZIMAS geocoding service"""
    async with httpx.AsyncClient() as client:
        params = {
            "searchText": address,
            "contains": False,
            "searchFields": "Full_Address",
            "sr": 4326,
            "layers": "105",
            "layerDefs": "",
            "returnGeometry": True,
            "maxAllowableOffset": "",
            "geometryPrecision": "",
            "dynamicLayers": "",
            "returnZ": False,
            "returnM": False,
            "gdbVersion": "",
            "f": "json"
        }
        
        try:
            response = await client.get(GEOCODE_URL, params=params)
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                attributes = data["results"][0].get("attributes", {})
                apn = attributes.get("APN", "").replace("-", "")
                return apn if apn else None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

async def query_parcel_by_apn(apn: str) -> Optional[Dict]:
    """Query ZIMAS for parcel data by APN"""
    async with httpx.AsyncClient() as client:
        formatted_apn = apn.replace("-", "")
        
        params = {
            "where": f"APN='{formatted_apn}'",
            "text": "",
            "objectIds": "",
            "time": "",
            "geometry": "",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "",
            "spatialRel": "esriSpatialRelIntersects",
            "relationParam": "",
            "outFields": "*",
            "returnGeometry": False,
            "returnTrueCurves": False,
            "maxAllowableOffset": "",
            "geometryPrecision": "",
            "outSR": "",
            "returnIdsOnly": False,
            "returnCountOnly": False,
            "orderByFields": "",
            "groupByFieldsForStatistics": "",
            "outStatistics": "",
            "returnZ": False,
            "returnM": False,
            "gdbVersion": "",
            "returnDistinctValues": False,
            "resultOffset": "",
            "resultRecordCount": "",
            "f": "json"
        }
        
        try:
            response = await client.get(PARCEL_QUERY_URL, params=params, timeout=30.0)
            data = response.json()
            
            if data.get("features") and len(data["features"]) > 0:
                return data["features"][0].get("attributes", {})
        except Exception as e:
            print(f"Query error: {e}")
            return None

def parse_zoning_data(raw_data: Dict) -> ZoningResponse:
    """Parse raw ZIMAS data into structured response"""
    
    apn = raw_data.get("APN", "").replace("-", "")
    
    zone = raw_data.get("ZONE_CLASS", "")
    height_district = raw_data.get("HEIGHT_DISTRICT", "")
    
    toc_tier = None
    for field in ["TOC_TIER", "TOC_Tier", "TOCTier"]:
        if raw_data.get(field):
            toc_tier = str(raw_data[field])
            break
    
    overlays = {}
    if raw_data.get("SPECIFIC_PLAN"):
        overlays["specific_plan"] = raw_data["SPECIFIC_PLAN"]
    if raw_data.get("HPOZ"):
        overlays["hpoz"] = raw_data["HPOZ"]
    if raw_data.get("CRA"):
        overlays["cra"] = raw_data["CRA"]
    if raw_data.get("CPIO"):
        overlays["cpio"] = raw_data["CPIO"]
    if raw_data.get("CDO"):
        overlays["cdo"] = raw_data["CDO"]
    if raw_data.get("NSO"):
        overlays["nso"] = raw_data["NSO"]
    
    rent_stabilization = False
    rso_field = raw_data.get("RSO") or raw_data.get("RENT_STABILIZATION")
    if rso_field and str(rso_field).upper() in ["YES", "Y", "TRUE", "1"]:
        rent_stabilization = True
    
    hazards = {
        "fault_zone": bool(raw_data.get("ALQUIST_PRIOLO_FAULT_ZONE")),
        "methane_zone": bool(raw_data.get("METHANE_ZONE")),
        "liquefaction": bool(raw_data.get("LIQUEFACTION")),
        "landslide": bool(raw_data.get("LANDSLIDE")),
        "flood_zone": bool(raw_data.get("FLOOD_ZONE")),
        "fire_severity": bool(raw_data.get("VERY_HIGH_FIRE_HAZARD_SEVERITY_ZONE"))
    }
    
    return ZoningResponse(
        apn=apn,
        zone=zone,
        height_district=height_district,
        toc_tier=toc_tier,
        overlays=overlays,
        rent_stabilization=rent_stabilization,
        hazards=hazards,
        raw_data=raw_data
    )

@app.get("/")
async def root():
    return {"message": "LA Zoning Lookup API", "endpoints": ["/lookup", "/apn/{apn}"]}

@app.post("/lookup")
async def lookup_address(request: AddressRequest):
    """Lookup zoning information by address"""
    
    apn = await geocode_address(request.address)
    
    if not apn:
        apn = request.address.replace("-", "")
        if len(apn) < 10:
            raise HTTPException(status_code=404, detail="Could not geocode address to APN")
    
    raw_data = await query_parcel_by_apn(apn)
    
    if not raw_data:
        raise HTTPException(status_code=404, detail="No parcel data found for this address/APN")
    
    return parse_zoning_data(raw_data)

@app.get("/apn/{apn}")
async def lookup_by_apn(apn: str):
    """Direct lookup by APN"""
    
    raw_data = await query_parcel_by_apn(apn)
    
    if not raw_data:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    return parse_zoning_data(raw_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)