from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any, List
import json
import re
from development_analyzer import DevelopmentAnalyzer

app = FastAPI(title="LA Development Potential Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LA County GIS endpoints
COUNTY_PARCEL_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query"

class AddressRequest(BaseModel):
    address: str

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

def normalize_address(address: str) -> str:
    """Extract just the street address part from a full address"""
    address = address.strip()
    
    # Remove everything after common city indicators
    for separator in [", Los Angeles", ", LA", " Los Angeles", " LA"]:
        if separator in address:
            address = address.split(separator)[0]
            break
    
    # Remove ZIP codes (5 digits at end)
    address = re.sub(r'\s+\d{5}(-\d{4})?$', '', address)
    
    # Remove state codes at end
    address = re.sub(r',?\s+(CA|CALIFORNIA)$', '', address, flags=re.IGNORECASE)
    
    return address.strip()

async def query_county_parcel(apn: str) -> Optional[Dict]:
    """Query LA County parcel data"""
    formatted_apn = re.sub(r'[^0-9]', '', apn)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "where": f"AIN='{formatted_apn}' OR APN='{formatted_apn}'",
            "outFields": "*",
            "f": "json",
            "returnGeometry": "true"
        }
        
        try:
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    # Get all addresses for this parcel
                    all_addresses = await get_all_parcel_addresses(formatted_apn)
                    
                    return {
                        "data": data["features"][0].get("attributes", {}),
                        "geometry": data["features"][0].get("geometry", {}),
                        "all_addresses": all_addresses,
                        "source": "LA County Parcel Service"
                    }
        except Exception as e:
            print(f"County parcel error: {e}")
    
    return None

async def get_all_parcel_addresses(apn: str) -> List[str]:
    """Get all addresses associated with a parcel APN"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "where": f"AIN='{apn}' OR APN='{apn}'",
            "outFields": "SitusAddress,SitusFullAddress",
            "f": "json",
            "returnGeometry": "false"
        }
        
        try:
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                addresses = set()  # Use set to avoid duplicates
                
                for feature in data.get("features", []):
                    attrs = feature.get("attributes", {})
                    situs_addr = attrs.get("SitusAddress", "").strip()
                    full_addr = attrs.get("SitusFullAddress", "").strip()
                    
                    if situs_addr:
                        addresses.add(situs_addr)
                    if full_addr and full_addr != situs_addr:
                        addresses.add(full_addr)
                
                return sorted(list(addresses))
        except Exception as e:
            print(f"Error fetching all addresses for APN {apn}: {e}")
    
    return []

async def geocode_address(address: str) -> Optional[Dict]:
    """Geocode address using LA County services"""
    
    # Check if it's already an APN
    potential_apn = parse_apn_from_input(address)
    if potential_apn:
        return {"apn": potential_apn}
    
    # Normalize the address to extract street address
    normalized_address = normalize_address(address)
    print(f"Normalized '{address}' to '{normalized_address}'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
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
    
    return None

def prepare_property_data(county_result: Dict) -> Dict:
    """Prepare property data for development analysis"""
    
    county_data = county_result.get("data", {})
    geometry = county_result.get("geometry", {})
    all_addresses = county_result.get("all_addresses", [])
    
    # Basic property info
    apn = str(county_data.get("AIN") or county_data.get("APN") or "")
    apn = format_apn(apn)
    address = county_data.get("SitusAddress") or ""
    
    # Property details
    use_code = county_data.get("UseCode") or ""
    use_desc = county_data.get("UseDescription") or ""
    
    # Building info
    year_built = str(county_data.get("YearBuilt1") or county_data.get("YearBuilt") or "")
    existing_units = county_data.get("Units1") or county_data.get("Units") or 0
    building_sf = county_data.get("SQFTmain1") or county_data.get("BuildingSqFt") or 0
    
    # Lot area
    lot_area = county_data.get("Shape.STArea()") or 0
    
    # Infer zone from use code
    zone = ""
    height_district = ""
    if use_code == "0500":
        zone = "R4"  # Multi-family
        height_district = "2"  # Common for urban multi-family
    elif use_code.startswith("1"):
        zone = "R1"
        height_district = "1"
    
    # RSO status - simplified logic
    is_rso = False
    if use_code == "0500" and existing_units >= 2:  # Multi-family with 2+ units
        is_rso = True
    
    return {
        'apn': apn,
        'address': address,
        'all_addresses': all_addresses,
        'lot_area_sqft': float(lot_area) if lot_area else 0,
        'existing_units': int(existing_units) if existing_units else 0,
        'building_sf': float(building_sf) if building_sf else 0,
        'year_built': year_built if year_built and year_built != "0" else "",
        'zone': zone,
        'height_district': height_district,
        'use_code': use_code,
        'use_description': use_desc,
        'is_rso': is_rso,
        'raw_data': county_data
    }

@app.get("/")
async def root():
    return {
        "message": "LA Development Potential Analyzer",
        "tagline": "What can be built on this lot?",
        "endpoints": ["/analyze", "/apn/{apn}"],
        "focus": "Development scenarios, unit yields, and feasibility analysis"
    }

@app.post("/analyze")
async def analyze_development_potential(request: AddressRequest):
    """Analyze development potential by address or APN"""
    
    # Try to geocode or extract APN
    geocode_result = await geocode_address(request.address)
    
    if not geocode_result:
        raise HTTPException(status_code=404, detail="Could not find address or APN")
    
    apn = geocode_result.get("apn")
    if not apn:
        raise HTTPException(status_code=404, detail="Could not determine APN for address")
    
    # Query county parcel data
    county_result = await query_county_parcel(apn)
    
    if not county_result:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    # Prepare data for analysis
    property_data = prepare_property_data(county_result)
    
    # Run development analysis
    analyzer = DevelopmentAnalyzer()
    analysis = analyzer.analyze_development_potential(property_data)
    
    return analysis

@app.get("/apn/{apn}")
async def analyze_by_apn(apn: str):
    """Direct development analysis by APN"""
    
    county_result = await query_county_parcel(apn)
    
    if not county_result:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    # Prepare data for analysis
    property_data = prepare_property_data(county_result)
    
    # Run development analysis
    analyzer = DevelopmentAnalyzer()
    analysis = analyzer.analyze_development_potential(property_data)
    
    return analysis

@app.get("/test-analyzer")
async def test_analyzer():
    """Test the development analyzer with sample data"""
    sample_data = {
        'apn': '5077-019-011',
        'address': '2910 LEEWARD AVE',
        'lot_area_sqft': 11135.09,
        'existing_units': 30,
        'building_sf': 22620,
        'year_built': '1924',
        'zone': 'R4',
        'height_district': '2',
        'use_code': '0500',
        'use_description': 'Five or more apartments',
        'is_rso': True,
        'toc_tier': '3',  # Mock TOC data
        'raw_data': {
            'METHANE_ZONE': True,
            'ALQUIST_PRIOLO_FAULT_ZONE': False,
            'LIQUEFACTION': True
        }
    }
    
    analyzer = DevelopmentAnalyzer()
    analysis = analyzer.analyze_development_potential(sample_data)
    
    return analysis

@app.get("/test-sb9")
async def test_sb9():
    """Test SB-9 scenarios with R1 property"""
    sample_data = {
        'apn': '1234-567-890',
        'address': '123 SINGLE FAMILY ST',
        'lot_area_sqft': 5000,  # Large enough for lot split
        'existing_units': 1,
        'building_sf': 1500,
        'year_built': '1950',
        'zone': 'R1',  # Single-family zone eligible for SB-9
        'height_district': '1',
        'use_code': '0100',
        'use_description': 'Single Family Residence',
        'is_rso': False,
        'raw_data': {}
    }
    
    analyzer = DevelopmentAnalyzer()
    analysis = analyzer.analyze_development_potential(sample_data)
    
    return analysis

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)