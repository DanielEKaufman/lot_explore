from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any, List
import json
import re

app = FastAPI(title="LA Zoning Lookup API - County Data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LA County GIS endpoints
COUNTY_PARCEL_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query"
COUNTY_ASSESSOR_URL = "https://maps.assessor.lacounty.gov/GIS/rest/services/AssessorMap_Information/MapServer/0/query"

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
    address: Optional[str] = None
    use_code: Optional[str] = None
    use_description: Optional[str] = None
    land_value: Optional[float] = None
    improvement_value: Optional[float] = None
    total_value: Optional[float] = None
    year_built: Optional[str] = None
    sq_ft_land: Optional[float] = None
    sq_ft_building: Optional[float] = None
    units: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None

def format_apn(apn: str) -> str:
    """Format APN with dashes: XXXX-XXX-XXX"""
    clean = re.sub(r'[^0-9]', '', str(apn))
    if len(clean) >= 10:
        return f"{clean[:4]}-{clean[4:7]}-{clean[7:]}"
    return apn

def parse_apn_from_input(input_str: str) -> Optional[str]:
    """Try to extract APN if user entered it directly"""
    clean = re.sub(r'[^0-9]', '', input_str)
    if len(clean) >= 10 and len(clean) <= 13:
        return clean
    return None

async def query_county_parcel(apn: str) -> Optional[Dict]:
    """Query LA County parcel data"""
    formatted_apn = re.sub(r'[^0-9]', '', apn)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try LA County Parcel service
        params = {
            "where": f"AIN='{formatted_apn}' OR APN='{formatted_apn}'",
            "outFields": "*",
            "f": "json",
            "returnGeometry": "false"
        }
        
        try:
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    return {
                        "data": data["features"][0].get("attributes", {}),
                        "source": "LA County Parcel Service"
                    }
        except Exception as e:
            print(f"County parcel error: {e}")
        
        # Try Assessor Map service
        try:
            response = await client.get(COUNTY_ASSESSOR_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    return {
                        "data": data["features"][0].get("attributes", {}),
                        "source": "LA County Assessor"
                    }
        except Exception as e:
            print(f"Assessor error: {e}")
    
    return None

def normalize_address(address: str) -> str:
    """Extract just the street address part from a full address"""
    # Remove common suffixes like city, state, zip
    address = address.strip()
    
    # Remove everything after common city indicators
    for separator in [", Los Angeles", ", LA", " Los Angeles", " LA"]:
        if separator in address:
            address = address.split(separator)[0]
            break
    
    # Remove ZIP codes (5 digits at end)
    import re
    address = re.sub(r'\s+\d{5}(-\d{4})?$', '', address)
    
    # Remove state codes at end
    address = re.sub(r',?\s+(CA|CALIFORNIA)$', '', address, flags=re.IGNORECASE)
    
    return address.strip()

async def geocode_address(address: str) -> Optional[Dict]:
    """Geocode address using multiple services"""
    
    # Check if it's already an APN
    potential_apn = parse_apn_from_input(address)
    if potential_apn:
        return {"apn": potential_apn}
    
    # Normalize the address to extract street address
    normalized_address = normalize_address(address)
    print(f"Normalized '{address}' to '{normalized_address}'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try searching directly in parcel data by address
        try:
            # Try exact match first
            params = {
                "where": f"SitusAddress = '{normalized_address.upper()}' OR SitusFullAddress LIKE '%{normalized_address.upper()}%'",
                "outFields": "AIN,APN,SitusAddress,SitusFullAddress",
                "f": "json",
                "returnGeometry": "false",
                "resultRecordCount": "5"
            }
            
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    attributes = data["features"][0].get("attributes", {})
                    apn = attributes.get("AIN") or attributes.get("APN")
                    if apn:
                        print(f"Found APN {apn} for address {normalized_address}")
                        return {"apn": str(apn)}
            
            # If exact match fails, try partial match
            params["where"] = f"SitusAddress LIKE '%{normalized_address.upper()}%' OR SitusFullAddress LIKE '%{normalized_address.upper()}%'"
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    attributes = data["features"][0].get("attributes", {})
                    apn = attributes.get("AIN") or attributes.get("APN")
                    if apn:
                        print(f"Found APN {apn} with partial match for address {normalized_address}")
                        return {"apn": str(apn)}
                        
        except Exception as e:
            print(f"Direct address search error: {e}")
        
        # Try LA County geocoder as backup
        try:
            geocode_url = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/GeocodeServer/findAddressCandidates"
            params = {
                "SingleLine": f"{address}, Los Angeles, CA",
                "f": "json",
                "outFields": "*",
                "maxLocations": "1"
            }
            
            response = await client.get(geocode_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("candidates") and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    location = candidate.get("location", {})
                    score = candidate.get("score", 0)
                    print(f"Geocoded {address} with score {score}")
                    
                    # Now we need to find the parcel at this location
                    if location and score >= 80:  # Only use high-confidence matches
                        result = await find_parcel_by_location(location["x"], location["y"])
                        if result:
                            return result
        except Exception as e:
            print(f"Geocode error: {e}")
        
        # Try OpenStreetMap Nominatim as final backup
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
                    lat = float(data[0].get("lat", 0))
                    lon = float(data[0].get("lon", 0))
                    print(f"Nominatim geocoded {address} to {lat}, {lon}")
                    # Convert to Web Mercator for LA County services
                    # Rough conversion - for production would use proper projection
                    x = lon * 111320  # Very rough conversion
                    y = lat * 111320
                    return await find_parcel_by_location(x, y)
        except Exception as e:
            print(f"Nominatim error: {e}")
    
    return None

async def find_parcel_by_location(x: float, y: float) -> Optional[Dict]:
    """Find parcel at given coordinates"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "geometry": f"{x},{y}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "AIN,APN,SitusAddress",
            "f": "json",
            "returnGeometry": "false"
        }
        
        try:
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    attributes = data["features"][0].get("attributes", {})
                    apn = attributes.get("AIN") or attributes.get("APN")
                    if apn:
                        return {"apn": str(apn)}
        except Exception as e:
            print(f"Location query error: {e}")
    
    return None

def parse_county_data(raw_data: Dict, source: str) -> ZoningResponse:
    """Parse LA County data into our response format"""
    
    data = raw_data.get("data", {})
    
    # Get APN - try multiple field names
    apn = str(data.get("AIN") or data.get("APN") or data.get("APN_CHR") or "")
    apn = format_apn(apn)
    
    # Get address
    address = data.get("SitusAddress") or data.get("SITUS_ADDR") or data.get("SitusFullAddress") or ""
    
    # Get use code and description
    use_code = data.get("UseCode") or data.get("USECODE") or data.get("UseType") or ""
    use_desc = data.get("UseDescription") or data.get("USEDESC") or data.get("UseType_Description") or ""
    
    # Get values
    land_value = data.get("LandValue") or data.get("Roll_LandValue") or 0
    improvement_value = data.get("ImprovementValue") or data.get("Roll_ImpValue") or 0
    total_value = data.get("TotalValue") or data.get("Roll_TotalValue") or (land_value + improvement_value)
    
    # Get building info - check multiple possible field names
    year_built = str(data.get("YearBuilt1") or data.get("YearBuilt") or data.get("YEAR_BUILT") or "")
    sq_ft_land = data.get("SQFTMain") or data.get("LandSqFt") or data.get("Shape_Area") or 0
    sq_ft_building = data.get("SQFTmain1") or data.get("SQFTMain2") or data.get("BuildingSqFt") or 0
    
    # Get units, bedrooms, bathrooms if available
    units = data.get("Units1") or data.get("Units") or ""
    bedrooms = data.get("Bedrooms1") or data.get("Bedrooms") or ""
    bathrooms = data.get("Bathrooms1") or data.get("Bathrooms") or ""
    
    # Try to infer zoning from use code (basic mapping)
    zone = ""
    if use_code:
        if use_code.startswith("1"):
            zone = "Residential"
        elif use_code.startswith("2"):
            zone = "Commercial"
        elif use_code.startswith("3"):
            zone = "Industrial"
        elif use_code.startswith("5"):
            zone = "Agricultural"
    
    return ZoningResponse(
        apn=apn,
        zone=zone or use_desc[:20] if use_desc else "",
        height_district="",
        toc_tier=None,
        overlays={},
        rent_stabilization=False,
        hazards={},
        raw_data=data,
        data_source=source,
        address=address,
        use_code=use_code,
        use_description=use_desc,
        land_value=float(land_value) if land_value else None,
        improvement_value=float(improvement_value) if improvement_value else None,
        total_value=float(total_value) if total_value else None,
        year_built=year_built if year_built and year_built != "0" else None,
        sq_ft_land=float(sq_ft_land) if sq_ft_land else None,
        sq_ft_building=float(sq_ft_building) if sq_ft_building else None,
        units=int(units) if units else None,
        bedrooms=int(bedrooms) if bedrooms else None,
        bathrooms=int(bathrooms) if bathrooms else None
    )

@app.get("/")
async def root():
    return {
        "message": "LA Zoning Lookup API - Using LA County Data",
        "endpoints": ["/lookup", "/apn/{apn}"],
        "note": "Using LA County GIS services for parcel data"
    }

@app.post("/lookup")
async def lookup_address(request: AddressRequest):
    """Lookup parcel information by address or APN"""
    
    # Try to geocode or extract APN
    geocode_result = await geocode_address(request.address)
    
    if not geocode_result:
        raise HTTPException(status_code=404, detail="Could not find address or APN")
    
    apn = geocode_result.get("apn")
    if not apn:
        raise HTTPException(status_code=404, detail="Could not determine APN for address")
    
    # Query parcel data
    result = await query_county_parcel(apn)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    return parse_county_data(result, result.get("source", "LA County"))

@app.get("/apn/{apn}")
async def lookup_by_apn(apn: str):
    """Direct lookup by APN"""
    
    result = await query_county_parcel(apn)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    return parse_county_data(result, result.get("source", "LA County"))

@app.get("/test-apn/{apn}")
async def test_apn(apn: str):
    """Test endpoint to see raw data for an APN"""
    result = await query_county_parcel(apn)
    return result if result else {"error": "No data found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)