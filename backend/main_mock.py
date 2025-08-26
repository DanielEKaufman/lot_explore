from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

app = FastAPI(title="LA Zoning Lookup API - Mock Version")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

MOCK_DATA = {
    "200 N Spring St": {
        "apn": "5077-019-011",
        "zone": "PF-1",
        "height_district": "1",
        "toc_tier": "3",
        "overlays": {
            "specific_plan": "Downtown Center",
            "cra": "City Center Redevelopment"
        },
        "rent_stabilization": False,
        "hazards": {
            "fault_zone": False,
            "methane_zone": False,
            "liquefaction": True,
            "landslide": False,
            "flood_zone": False,
            "fire_severity": False
        }
    },
    "1 World Way": {
        "apn": "4129-028-906",
        "zone": "LAX",
        "height_district": "None",
        "toc_tier": None,
        "overlays": {
            "specific_plan": "LAX Specific Plan"
        },
        "rent_stabilization": False,
        "hazards": {
            "fault_zone": False,
            "methane_zone": True,
            "liquefaction": False,
            "landslide": False,
            "flood_zone": False,
            "fire_severity": False
        }
    },
    "default": {
        "apn": "5128-014-900",
        "zone": "R4-2",
        "height_district": "2",
        "toc_tier": "4",
        "overlays": {
            "specific_plan": None,
            "hpoz": "Miracle Mile HPOZ"
        },
        "rent_stabilization": True,
        "hazards": {
            "fault_zone": True,
            "methane_zone": False,
            "liquefaction": False,
            "landslide": False,
            "flood_zone": False,
            "fire_severity": False
        }
    }
}

@app.get("/")
async def root():
    return {
        "message": "LA Zoning Lookup API - Mock Version", 
        "note": "Using mock data as ZIMAS API is unavailable",
        "endpoints": ["/lookup", "/apn/{apn}"]
    }

@app.post("/lookup")
async def lookup_address(request: AddressRequest):
    """Lookup zoning information by address (using mock data)"""
    
    address_key = None
    for key in MOCK_DATA.keys():
        if key.lower() in request.address.lower():
            address_key = key
            break
    
    if not address_key:
        address_key = "default"
    
    data = MOCK_DATA[address_key].copy()
    
    raw_data = {
        "APN": data["apn"],
        "ZONE_CLASS": data["zone"],
        "HEIGHT_DISTRICT": data["height_district"],
        "TOC_TIER": data.get("toc_tier"),
        "SPECIFIC_PLAN": data["overlays"].get("specific_plan"),
        "HPOZ": data["overlays"].get("hpoz"),
        "CRA": data["overlays"].get("cra"),
        "RSO": "Yes" if data["rent_stabilization"] else "No",
        "ALQUIST_PRIOLO_FAULT_ZONE": data["hazards"]["fault_zone"],
        "METHANE_ZONE": data["hazards"]["methane_zone"],
        "LIQUEFACTION": data["hazards"]["liquefaction"],
        "LANDSLIDE": data["hazards"]["landslide"],
        "FLOOD_ZONE": data["hazards"]["flood_zone"],
        "VERY_HIGH_FIRE_HAZARD_SEVERITY_ZONE": data["hazards"]["fire_severity"]
    }
    
    return ZoningResponse(
        apn=data["apn"],
        zone=data["zone"],
        height_district=data["height_district"],
        toc_tier=data.get("toc_tier"),
        overlays={k: v for k, v in data["overlays"].items() if v},
        rent_stabilization=data["rent_stabilization"],
        hazards=data["hazards"],
        raw_data=raw_data
    )

@app.get("/apn/{apn}")
async def lookup_by_apn(apn: str):
    """Direct lookup by APN (using mock data)"""
    
    for key, data in MOCK_DATA.items():
        if data["apn"].replace("-", "") == apn.replace("-", ""):
            raw_data = {
                "APN": data["apn"],
                "ZONE_CLASS": data["zone"],
                "HEIGHT_DISTRICT": data["height_district"],
                "TOC_TIER": data.get("toc_tier"),
                "SPECIFIC_PLAN": data["overlays"].get("specific_plan"),
                "HPOZ": data["overlays"].get("hpoz"),
                "CRA": data["overlays"].get("cra"),
                "RSO": "Yes" if data["rent_stabilization"] else "No",
                "ALQUIST_PRIOLO_FAULT_ZONE": data["hazards"]["fault_zone"],
                "METHANE_ZONE": data["hazards"]["methane_zone"],
                "LIQUEFACTION": data["hazards"]["liquefaction"],
                "LANDSLIDE": data["hazards"]["landslide"],
                "FLOOD_ZONE": data["hazards"]["flood_zone"],
                "VERY_HIGH_FIRE_HAZARD_SEVERITY_ZONE": data["hazards"]["fire_severity"]
            }
            
            return ZoningResponse(
                apn=data["apn"],
                zone=data["zone"],
                height_district=data["height_district"],
                toc_tier=data.get("toc_tier"),
                overlays={k: v for k, v in data["overlays"].items() if v},
                rent_stabilization=data["rent_stabilization"],
                hazards=data["hazards"],
                raw_data=raw_data
            )
    
    raise HTTPException(status_code=404, detail=f"No parcel data found for APN: {apn}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)