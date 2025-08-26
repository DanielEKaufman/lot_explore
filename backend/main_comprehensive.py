from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from typing import Optional, Dict, Any, List
import json
import re
from zoning_engine import ZoningEngine

app = FastAPI(title="LA Zoning Lookup API - Comprehensive Analysis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LA County GIS endpoints
COUNTY_PARCEL_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query"
ZIMAS_ZONING_URL = "https://zimas.lacity.org/arcgis/rest/services/D_BASEMAPS/MapServer/11/query"

class AddressRequest(BaseModel):
    address: str

class ComprehensiveZoningResponse(BaseModel):
    # Basic info
    apn: str
    address: Optional[str] = None
    data_source: Optional[str] = None
    
    # Original simple fields for backward compatibility
    zone: Optional[str] = None
    height_district: Optional[str] = None
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
    
    # Comprehensive zoning analysis
    core_zoning_envelope: Optional[Dict] = None
    lot_units: Optional[Dict] = None
    overlays: Optional[Dict] = None
    incentive_eligibility: Optional[Dict] = None
    transit_parking: Optional[Dict] = None
    hazards: Optional[Dict] = None
    derived_envelopes: Optional[Dict] = None
    citations: Optional[List[Dict]] = None
    
    # Legacy fields
    rent_stabilization: bool = False
    toc_tier: Optional[str] = None
    raw_data: Optional[Dict] = None

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
        # Try LA County Parcel service
        params = {
            "where": f"AIN='{formatted_apn}' OR APN='{formatted_apn}'",
            "outFields": "*",
            "f": "json",
            "returnGeometry": "true"  # Need geometry for area calculation
        }
        
        try:
            response = await client.get(COUNTY_PARCEL_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    return {
                        "data": data["features"][0].get("attributes", {}),
                        "geometry": data["features"][0].get("geometry", {}),
                        "source": "LA County Parcel Service"
                    }
        except Exception as e:
            print(f"County parcel error: {e}")
    
    return None

async def query_zimas_zoning(geometry: Dict) -> Optional[Dict]:
    """Query ZIMAS for actual zoning information"""
    if not geometry:
        return None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Use the parcel centroid to query zoning
            if geometry.get("rings"):
                # Calculate rough centroid of polygon
                rings = geometry["rings"][0]
                x_coords = [point[0] for point in rings]
                y_coords = [point[1] for point in rings]
                centroid_x = sum(x_coords) / len(x_coords)
                centroid_y = sum(y_coords) / len(y_coords)
                
                params = {
                    "geometry": f"{centroid_x},{centroid_y}",
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "*",
                    "f": "json",
                    "returnGeometry": "false"
                }
                
                response = await client.get(ZIMAS_ZONING_URL, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("features") and len(data["features"]) > 0:
                        return data["features"][0].get("attributes", {})
        except Exception as e:
            print(f"ZIMAS zoning error: {e}")
    
    return None

def calculate_lot_area(geometry: Dict) -> float:
    """Calculate lot area from polygon geometry"""
    if not geometry or not geometry.get("rings"):
        return 0.0
    
    # Use the Shape.STArea from county data if available
    # Otherwise would need to implement polygon area calculation
    return 0.0  # Placeholder - would calculate from coordinates

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
    
    return None

def parse_comprehensive_data(county_result: Dict, zimas_result: Optional[Dict] = None) -> ComprehensiveZoningResponse:
    """Parse data and perform comprehensive zoning analysis"""
    
    county_data = county_result.get("data", {})
    geometry = county_result.get("geometry", {})
    source = county_result.get("source", "LA County")
    
    # Basic property info
    apn = str(county_data.get("AIN") or county_data.get("APN") or "")
    apn = format_apn(apn)
    address = county_data.get("SitusAddress") or county_data.get("SITUS_ADDR") or ""
    
    # Property details
    use_code = county_data.get("UseCode") or county_data.get("USECODE") or ""
    use_desc = county_data.get("UseDescription") or county_data.get("USEDESC") or ""
    
    # Values
    land_value = county_data.get("Roll_LandValue") or county_data.get("LandValue") or 0
    improvement_value = county_data.get("Roll_ImpValue") or county_data.get("ImprovementValue") or 0
    total_value = county_data.get("Roll_TotalValue") or (land_value + improvement_value) if land_value and improvement_value else 0
    
    # Building info
    year_built = str(county_data.get("YearBuilt1") or county_data.get("YearBuilt") or "")
    sq_ft_building = county_data.get("SQFTmain1") or county_data.get("BuildingSqFt") or 0
    units = county_data.get("Units1") or county_data.get("Units") or 0
    bedrooms = county_data.get("Bedrooms1") or county_data.get("Bedrooms") or 0
    bathrooms = county_data.get("Bathrooms1") or county_data.get("Bathrooms") or 0
    
    # Lot area - use Shape.STArea from county data or calculate from geometry
    lot_area = county_data.get("Shape.STArea()") or calculate_lot_area(geometry) or 0
    
    # Zoning info - prefer ZIMAS data if available, fall back to county
    zone = ""
    height_district = ""
    
    if zimas_result:
        zone = zimas_result.get("ZONE_CLASS") or zimas_result.get("Zone") or ""
        height_district = zimas_result.get("HEIGHT_DISTRICT") or zimas_result.get("HD") or ""
    else:
        # Try to infer from use code
        if use_code:
            if use_code.startswith("1"):
                zone = "R1"
            elif use_code == "0500":
                zone = "R4"  # Multi-family
    
    # RSO status
    rso_fields = ["RSO", "RENT_STABILIZATION", "Rent_Stabilized"]
    rent_stabilization = False
    for field in rso_fields:
        value = county_data.get(field)
        if value and str(value).upper() in ["YES", "Y", "TRUE", "1"]:
            rent_stabilization = True
            break
    
    # Initialize zoning engine
    engine = ZoningEngine()
    
    # Perform comprehensive analysis if we have enough data
    comprehensive_analysis = {}
    if zone and lot_area > 0:
        try:
            comprehensive_analysis = engine.analyze_comprehensive(
                zone=zone,
                height_district=height_district,
                lot_area_sqft=float(lot_area),
                existing_units=int(units) if units else 0,
                raw_data=county_data,
                is_rso=rent_stabilization
            )
        except Exception as e:
            print(f"Comprehensive analysis error: {e}")
            comprehensive_analysis = {}
    
    return ComprehensiveZoningResponse(
        apn=apn,
        address=address,
        data_source=source,
        
        # Basic fields
        zone=zone,
        height_district=height_district,
        use_code=use_code,
        use_description=use_desc,
        land_value=float(land_value) if land_value else None,
        improvement_value=float(improvement_value) if improvement_value else None,
        total_value=float(total_value) if total_value else None,
        year_built=year_built if year_built and year_built != "0" else None,
        sq_ft_land=float(lot_area) if lot_area else None,
        sq_ft_building=float(sq_ft_building) if sq_ft_building else None,
        units=int(units) if units else None,
        bedrooms=int(bedrooms) if bedrooms else None,
        bathrooms=int(bathrooms) if bathrooms else None,
        
        # Comprehensive analysis
        core_zoning_envelope=comprehensive_analysis.get('core_zoning_envelope'),
        lot_units=comprehensive_analysis.get('lot_units'),
        overlays=comprehensive_analysis.get('overlays'),
        incentive_eligibility=comprehensive_analysis.get('incentive_eligibility'),
        transit_parking=comprehensive_analysis.get('transit_parking'),
        hazards=comprehensive_analysis.get('hazards'),
        derived_envelopes=comprehensive_analysis.get('derived_envelopes'),
        citations=comprehensive_analysis.get('citations'),
        
        # Legacy
        rent_stabilization=rent_stabilization,
        toc_tier=comprehensive_analysis.get('incentive_eligibility', {}).get('toc', {}).get('tier'),
        raw_data=county_data
    )

@app.get("/")
async def root():
    return {
        "message": "LA Zoning Lookup API - Comprehensive Entitlement Analysis",
        "endpoints": ["/lookup", "/apn/{apn}"],
        "features": [
            "Core zoning envelope analysis",
            "Unit calculations and replacement requirements", 
            "Overlay detection and conditions",
            "Incentive program eligibility (TOC, State DB, ED-1, SB-9)",
            "Transit proximity and parking calculations",
            "Hazard constraint analysis",
            "Derived development scenarios",
            "Regulatory citations and references"
        ]
    }

@app.post("/lookup")
async def lookup_address(request: AddressRequest):
    """Comprehensive zoning lookup by address or APN"""
    
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
    
    # Query ZIMAS for actual zoning data
    zimas_result = await query_zimas_zoning(county_result.get("geometry"))
    
    return parse_comprehensive_data(county_result, zimas_result)

@app.get("/apn/{apn}")
async def lookup_by_apn(apn: str):
    """Direct comprehensive lookup by APN"""
    
    county_result = await query_county_parcel(apn)
    
    if not county_result:
        raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")
    
    # Query ZIMAS for actual zoning data
    zimas_result = await query_zimas_zoning(county_result.get("geometry"))
    
    return parse_comprehensive_data(county_result, zimas_result)

@app.get("/test-zoning-engine")
async def test_zoning_engine():
    """Test the zoning engine with sample data"""
    engine = ZoningEngine()
    
    sample_analysis = engine.analyze_comprehensive(
        zone="R4",
        height_district="2", 
        lot_area_sqft=10000,
        existing_units=8,
        raw_data={},
        is_rso=True
    )
    
    return {
        "message": "Zoning engine test",
        "sample_analysis": sample_analysis
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)