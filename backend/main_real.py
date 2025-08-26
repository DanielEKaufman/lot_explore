from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any
import json
import re

app = FastAPI(title="LA Zoning Lookup API - Real Data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alternative endpoints to try - updated with working ZIMAS endpoints
ZIMAS_ENDPOINTS = [
    "https://zimas.lacity.org/arcgis/rest/services/D_BASEMAPS/MapServer/11/query",  # Zoning layer
    "https://zimas.lacity.org/arcgis/rest/services/D_LEGENDLAYERS/MapServer/142/query",  # Parcel layer
    "http://zimas.lacity.org/arcgis/rest/services/D_LEGENDLAYERS/MapServer/272/query"  # Zoning boundaries
]

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
    data_source: Optional[str] = None

def format_apn(apn: str) -> str:
    """Format APN with dashes: XXXX-XXX-XXX"""
    clean = re.sub(r'[^0-9]', '', apn)
    if len(clean) >= 10:
        return f"{clean[:4]}-{clean[4:7]}-{clean[7:]}"
    return apn

def parse_apn_from_address(address: str) -> Optional[str]:
    """Try to extract APN if user entered it directly"""
    # Remove common separators and check if it looks like an APN
    clean = re.sub(r'[^0-9]', '', address)
    if len(clean) >= 10 and len(clean) <= 13:
        return clean
    return None

async def query_parcel_data(apn: str) -> Optional[Dict]:
    """Try multiple endpoints to get parcel data"""
    formatted_apn = re.sub(r'[^0-9]', '', apn)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in ZIMAS_ENDPOINTS:
            params = {
                "where": f"APN='{formatted_apn}' OR AIN='{formatted_apn}'",
                "outFields": "*",
                "f": "json",
                "returnGeometry": "false"
            }
            
            try:
                response = await client.get(endpoint, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("features") and len(data["features"]) > 0:
                        return {
                            "data": data["features"][0].get("attributes", {}),
                            "source": endpoint
                        }
            except Exception as e:
                print(f"Error with {endpoint}: {e}")
                continue
    
    # Try LA County Assessor as fallback
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            assessor_url = f"https://portal.assessor.lacounty.gov/api/search?ain={formatted_apn}"
            response = await client.get(assessor_url)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        "data": {
                            "APN": formatted_apn,
                            "ADDRESS": data.get("situsAddress", ""),
                            "USE_CODE": data.get("useCode", ""),
                            "USE_DESCRIPTION": data.get("useDescription", ""),
                            "LAND_VALUE": data.get("landValue", 0),
                            "IMPROVEMENT_VALUE": data.get("improvementValue", 0),
                            "SQ_FT": data.get("sqFootage", 0),
                            "YEAR_BUILT": data.get("yearBuilt", "")
                        },
                        "source": "LA County Assessor"
                    }
    except Exception as e:
        print(f"Assessor error: {e}")
    
    return None

async def geocode_address(address: str) -> Optional[str]:
    """Geocode address to APN using various services"""
    
    # First check if it's already an APN
    potential_apn = parse_apn_from_address(address)
    if potential_apn:
        return potential_apn
    
    # Try geocoding services
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try Nominatim (OpenStreetMap)
        try:
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": f"{address}, Los Angeles, CA",
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            headers = {"User-Agent": "LA-Zoning-Lookup/1.0"}
            
            response = await client.get(nominatim_url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # We got coordinates, but need to find APN
                    # This would require a parcel lookup by coordinates
                    lat = data[0].get("lat")
                    lon = data[0].get("lon")
                    print(f"Geocoded to: {lat}, {lon}")
        except Exception as e:
            print(f"Nominatim error: {e}")
    
    return None

def parse_zoning_data(raw_data: Dict, source: str) -> ZoningResponse:
    """Parse raw data into structured response"""
    
    data = raw_data.get("data", {})
    
    # Get APN
    apn = data.get("APN") or data.get("AIN") or ""
    apn = format_apn(apn)
    
    # Get zone - try multiple field names
    zone = data.get("ZONE_CLASS") or data.get("ZONING") or data.get("Zone") or ""
    
    # Get height district
    height_district = data.get("HEIGHT_DISTRICT") or data.get("Height_District") or ""
    
    # Get TOC tier
    toc_tier = None
    for field in ["TOC_TIER", "TOC_Tier", "TOCTier", "TOC"]:
        if data.get(field):
            toc_tier = str(data[field])
            break
    
    # Get overlays
    overlays = {}
    overlay_fields = {
        "specific_plan": ["SPECIFIC_PLAN", "Specific_Plan", "SP"],
        "hpoz": ["HPOZ", "Historic_Preservation"],
        "cra": ["CRA", "Redevelopment_Area"],
        "cpio": ["CPIO", "Community_Plan_Imp"],
        "cdo": ["CDO", "Community_Design"],
        "nso": ["NSO", "Neighborhood_Stabilization"]
    }
    
    for key, fields in overlay_fields.items():
        for field in fields:
            if data.get(field):
                overlays[key] = data[field]
                break
    
    # Get rent stabilization
    rent_stabilization = False
    rso_fields = ["RSO", "RENT_STABILIZATION", "Rent_Stabilized"]
    for field in rso_fields:
        value = data.get(field)
        if value and str(value).upper() in ["YES", "Y", "TRUE", "1"]:
            rent_stabilization = True
            break
    
    # Get hazards
    hazards = {
        "fault_zone": bool(data.get("ALQUIST_PRIOLO_FAULT_ZONE") or data.get("Fault_Zone")),
        "methane_zone": bool(data.get("METHANE_ZONE") or data.get("Methane")),
        "liquefaction": bool(data.get("LIQUEFACTION") or data.get("Liquefaction_Zone")),
        "landslide": bool(data.get("LANDSLIDE") or data.get("Landslide_Zone")),
        "flood_zone": bool(data.get("FLOOD_ZONE") or data.get("Flood")),
        "fire_severity": bool(data.get("VERY_HIGH_FIRE_HAZARD_SEVERITY_ZONE") or data.get("Fire_Zone"))
    }
    
    return ZoningResponse(
        apn=apn,
        zone=zone,
        height_district=height_district,
        toc_tier=toc_tier,
        overlays=overlays,
        rent_stabilization=rent_stabilization,
        hazards=hazards,
        raw_data=data,
        data_source=source
    )

@app.get("/")
async def root():
    return {
        "message": "LA Zoning Lookup API - Real Data",
        "endpoints": ["/lookup", "/apn/{apn}"],
        "note": "Attempting to connect to real ZIMAS/LA City data sources"
    }

@app.post("/lookup")
async def lookup_address(request: AddressRequest):
    """Lookup zoning information by address"""
    
    # Try to get APN from address
    apn = await geocode_address(request.address)
    
    if not apn:
        # Check if the input itself might be an APN
        apn = parse_apn_from_address(request.address)
        if not apn:
            raise HTTPException(status_code=404, detail="Could not geocode address to APN")
    
    # Query parcel data
    result = await query_parcel_data(apn)
    
    if not result:
        raise HTTPException(status_code=404, detail="No parcel data found for this address/APN")
    
    return parse_zoning_data(result, result.get("source", "Unknown"))

@app.get("/apn/{apn}")
async def lookup_by_apn(apn: str):
    """Direct lookup by APN"""
    
    result = await query_parcel_data(apn)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    return parse_zoning_data(result, result.get("source", "Unknown"))

@app.get("/test-endpoints")
async def test_endpoints():
    """Test which endpoints are accessible"""
    results = {}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in ZIMAS_ENDPOINTS:
            try:
                response = await client.get(f"{endpoint}?f=json")
                results[endpoint] = {
                    "status": response.status_code,
                    "accessible": response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "accessible": False,
                    "error": str(e)
                }
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)