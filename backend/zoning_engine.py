"""
LA Zoning Analysis Engine
Comprehensive entitlement analysis for LA properties
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class ZoneType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED = "mixed"
    PUBLIC = "public"

@dataclass
class CoreZoningEnvelope:
    zone: str
    height_district: str
    zone_complete: str

@dataclass
class LotUnits:
    lot_area_sqft: float
    baseline_units: float
    existing_units: int
    replacement_units: float

@dataclass
class Overlays:
    specific_plan: Optional[str] = None
    specific_plan_id: Optional[str] = None
    cpio: Optional[str] = None
    q_conditions: List[str] = None
    d_conditions: List[str] = None
    t_conditions: List[str] = None
    hpoz: bool = False
    hpoz_name: Optional[str] = None
    historic_resource: bool = False

@dataclass
class TOCInfo:
    eligible: bool
    tier: Optional[int] = None
    distance_meters: Optional[float] = None

@dataclass
class StateDensityBonus:
    eligible: bool
    bonus_pct: float = 0
    affordable_required: float = 0

@dataclass
class ED1Info:
    eligible: bool
    ministerial: bool = False

@dataclass
class SB9Info:
    eligible: bool
    lot_split_eligible: bool = False
    duplex_eligible: bool = False

@dataclass
class IncentiveEligibility:
    toc: TOCInfo
    state_density_bonus: StateDensityBonus
    ed1: ED1Info
    sb9: SB9Info

@dataclass
class TransitParking:
    nearest_mts_meters: Optional[float]
    qualifies_ab2097: bool
    parking_baseline: float

@dataclass
class Hazards:
    methane_buffer: bool = False
    fault_zone: bool = False
    fault_distance_meters: Optional[float] = None
    liquefaction: bool = False
    very_high_fire_hazard: bool = False
    landslide: bool = False
    flood_zone: bool = False

@dataclass
class BaselineEnvelope:
    units: float
    far: float
    height_ft: float
    yards: Dict[str, float]
    open_space: float
    parking: float

@dataclass
class Scenario:
    units: float
    far: Optional[float] = None
    height_ft: Optional[float] = None
    parking: float = 0
    concessions: List[str] = None
    ministerial: bool = False
    units_range: Optional[Tuple[float, float]] = None

@dataclass
class DerivedEnvelopes:
    baseline: BaselineEnvelope
    toc: Optional[Scenario] = None
    state_db: Optional[Scenario] = None
    ed1: Optional[Scenario] = None
    sb9: Optional[Scenario] = None

@dataclass
class Citation:
    code: str
    description: str
    value: Any
    source: str

class ZoningEngine:
    """LA Municipal Code zoning analysis engine"""
    
    # Zone density factors (sq ft per unit)
    DENSITY_FACTORS = {
        'R1': 5000,     # Single family
        'RS': 5000,     # Suburban
        'RE': 2000,     # Estate
        'RA': 2000,     # Agricultural
        'RD1.5': 1500,  # Multiple dwelling
        'RD2': 2000,
        'RD3': 1500,
        'RD4': 1200,
        'RD5': 1000,
        'RD6': 800,
        'RU': 800,      # Urban
        'R2': 800,      # Two-family
        'R3': 800,      # Multiple dwelling
        'R4': 400,      # Multiple dwelling
        'R5': 200,      # Multiple dwelling
        'RAS3': 800,    # Residential/Accessory Services
        'RAS4': 400,
    }
    
    # Height limits by height district
    HEIGHT_LIMITS = {
        '1': 45,    # Height District 1
        '1L': 30,   # Height District 1L (Limited)
        '1VL': 25,  # Height District 1VL (Very Limited)
        '1XL': 20,  # Height District 1XL (Extra Limited)
        '2': 75,    # Height District 2
        '3': 150,   # Height District 3
        '4': 275,   # Height District 4
        'NL': None, # No Limit
    }
    
    # Parking requirements (spaces per unit)
    PARKING_REQUIREMENTS = {
        'R1': 2.0,
        'R2': 1.0,
        'R3': 1.0,
        'R4': 1.0,
        'R5': 1.0,
        'studio': 1.0,
        'bachelor': 1.0,
        '1_bedroom': 1.0,
        '2_bedroom': 1.5,
        '3_bedroom': 2.0,
    }
    
    def __init__(self):
        self.citations = []
    
    def parse_zone(self, zone_str: str) -> Tuple[str, Optional[str]]:
        """Parse zone string into base zone and modifiers"""
        if not zone_str:
            return "", None
        
        # Handle common formats like R4-2, PF-1, etc.
        if '-' in zone_str:
            parts = zone_str.split('-')
            return parts[0], parts[1] if len(parts) > 1 else None
        
        return zone_str, None
    
    def get_core_zoning_envelope(self, zone: str, height_district: str) -> CoreZoningEnvelope:
        """Extract core zoning parameters"""
        base_zone, modifier = self.parse_zone(zone)
        
        zone_complete = f"{base_zone}"
        if height_district and height_district not in ['', 'None']:
            zone_complete += f"-{height_district}"
        
        return CoreZoningEnvelope(
            zone=base_zone or zone,
            height_district=height_district or "",
            zone_complete=zone_complete
        )
    
    def calculate_lot_units(self, lot_area_sqft: float, zone: str, existing_units: int, 
                           is_rso: bool = False) -> LotUnits:
        """Calculate unit counts based on lot area and zoning"""
        base_zone, _ = self.parse_zone(zone)
        
        # Get density factor
        density_factor = self.DENSITY_FACTORS.get(base_zone, 1000)  # Default fallback
        self.citations.append(Citation(
            code=f"LAMC 12.03-{base_zone}",
            description=f"Density factor for {base_zone} zone",
            value=density_factor,
            source="LA Municipal Code"
        ))
        
        baseline_units = lot_area_sqft / density_factor if density_factor > 0 else 0
        
        # RSO/SB 330 replacement requirement
        replacement_units = max(baseline_units, existing_units) if is_rso else baseline_units
        
        if is_rso:
            self.citations.append(Citation(
                code="SB 330",
                description="Replacement housing requirement for RSO properties",
                value=existing_units,
                source="State Law"
            ))
        
        return LotUnits(
            lot_area_sqft=lot_area_sqft,
            baseline_units=baseline_units,
            existing_units=existing_units,
            replacement_units=replacement_units
        )
    
    def detect_overlays(self, raw_data: Dict) -> Overlays:
        """Detect planning overlays and conditions"""
        overlays = Overlays(q_conditions=[], d_conditions=[], t_conditions=[])
        
        # Specific Plan
        sp = raw_data.get('SPECIFIC_PLAN') or raw_data.get('SpecificPlan')
        if sp and sp.strip():
            overlays.specific_plan = sp
        
        # HPOZ
        hpoz = raw_data.get('HPOZ') or raw_data.get('Historic_Preservation')
        if hpoz and str(hpoz).upper() in ['YES', 'Y', 'TRUE', '1']:
            overlays.hpoz = True
            overlays.hpoz_name = hpoz if isinstance(hpoz, str) else None
        
        # Q/D/T Conditions - would need specific overlay data
        # For now, placeholder logic
        
        return overlays
    
    def analyze_toc_eligibility(self, location_data: Dict) -> TOCInfo:
        """Analyze Transit Oriented Communities eligibility"""
        # This would require actual transit stop data
        # For now, use basic heuristics
        
        # Check if TOC tier is already in data
        toc_tier = location_data.get('TOC_TIER')
        if toc_tier and str(toc_tier).isdigit():
            tier = int(toc_tier)
            return TOCInfo(eligible=True, tier=tier)
        
        return TOCInfo(eligible=False)
    
    def analyze_state_density_bonus(self, zone: str) -> StateDensityBonus:
        """Analyze State Density Bonus eligibility"""
        base_zone, _ = self.parse_zone(zone)
        
        # State DB available for most residential zones
        eligible = base_zone.startswith('R') and base_zone not in ['R1', 'RS']
        
        return StateDensityBonus(
            eligible=eligible,
            bonus_pct=35,  # Maximum bonus, would calculate based on affordability
            affordable_required=11  # VLI percentage for maximum bonus
        )
    
    def analyze_ed1_eligibility(self, zone: str) -> ED1Info:
        """Analyze Executive Directive 1 eligibility"""
        base_zone, _ = self.parse_zone(zone)
        
        # ED-1 available for residential zones, ministerial if 100% affordable
        eligible = base_zone.startswith('R')
        
        return ED1Info(
            eligible=eligible,
            ministerial=True  # Assumes 100% affordable
        )
    
    def analyze_sb9_eligibility(self, zone: str, lot_area_sqft: float) -> SB9Info:
        """Analyze SB 9 (duplex/lot split) eligibility"""
        base_zone, _ = self.parse_zone(zone)
        
        # SB 9 only for R1 zones
        eligible = base_zone == 'R1'
        lot_split_eligible = eligible and lot_area_sqft >= 2400  # Minimum lot size
        duplex_eligible = eligible
        
        if eligible:
            self.citations.append(Citation(
                code="SB 9",
                description="California duplex and lot split law",
                value="Eligible for R1 zones",
                source="State Law"
            ))
        
        return SB9Info(
            eligible=eligible,
            lot_split_eligible=lot_split_eligible,
            duplex_eligible=duplex_eligible
        )
    
    def calculate_transit_parking(self, zone: str) -> TransitParking:
        """Calculate parking requirements considering AB 2097"""
        base_zone, _ = self.parse_zone(zone)
        
        baseline_parking = self.PARKING_REQUIREMENTS.get(base_zone, 1.0)
        
        # AB 2097 - would need actual transit data
        qualifies_ab2097 = False  # Placeholder
        
        return TransitParking(
            nearest_mts_meters=None,  # Would calculate from transit data
            qualifies_ab2097=qualifies_ab2097,
            parking_baseline=baseline_parking
        )
    
    def analyze_hazards(self, raw_data: Dict) -> Hazards:
        """Analyze hazard constraints"""
        return Hazards(
            methane_buffer=bool(raw_data.get('METHANE_ZONE')),
            fault_zone=bool(raw_data.get('ALQUIST_PRIOLO_FAULT_ZONE')),
            liquefaction=bool(raw_data.get('LIQUEFACTION')),
            very_high_fire_hazard=bool(raw_data.get('VERY_HIGH_FIRE_HAZARD_SEVERITY_ZONE')),
            landslide=bool(raw_data.get('LANDSLIDE')),
            flood_zone=bool(raw_data.get('FLOOD_ZONE'))
        )
    
    def create_baseline_envelope(self, lot_units: LotUnits, zone: str, 
                                height_district: str) -> BaselineEnvelope:
        """Create baseline development envelope"""
        base_zone, _ = self.parse_zone(zone)
        
        # Height calculation
        height_ft = self.HEIGHT_LIMITS.get(height_district, 45)
        if height_ft is None:
            height_ft = 200  # Reasonable default for NL
        
        # FAR calculation (simplified)
        far = 1.0  # Would be more complex based on zone
        
        # Yards (setbacks) - simplified
        yards = {
            'front': 20,
            'rear': 15,
            'side': 5
        }
        
        # Open space requirement (simplified)
        open_space = lot_units.lot_area_sqft * 0.25  # 25% typical
        
        # Parking
        parking = lot_units.baseline_units * self.PARKING_REQUIREMENTS.get(base_zone, 1.0)
        
        return BaselineEnvelope(
            units=lot_units.baseline_units,
            far=far,
            height_ft=height_ft,
            yards=yards,
            open_space=open_space,
            parking=parking
        )
    
    def create_toc_scenario(self, baseline: BaselineEnvelope, toc: TOCInfo, 
                           lot_units: LotUnits) -> Optional[Scenario]:
        """Create TOC bonus scenario"""
        if not toc.eligible or not toc.tier:
            return None
        
        # TOC bonus percentages by tier
        bonus_pct = {1: 50, 2: 60, 3: 70, 4: 80}.get(toc.tier, 50)
        
        units = baseline.units * (1 + bonus_pct / 100)
        parking = 0 if toc.tier >= 3 else baseline.parking * 0.5  # Reduced parking
        
        return Scenario(
            units=units,
            parking=parking,
            concessions=['Height', 'Parking', 'Open Space']
        )
    
    def analyze_comprehensive(self, zone: str, height_district: str, 
                            lot_area_sqft: float, existing_units: int, 
                            raw_data: Dict, is_rso: bool = False) -> Dict:
        """Perform comprehensive zoning analysis"""
        self.citations = []  # Reset citations
        
        # Core zoning
        core = self.get_core_zoning_envelope(zone, height_district)
        
        # Lot and units
        lot_units = self.calculate_lot_units(lot_area_sqft, zone, existing_units, is_rso)
        
        # Overlays
        overlays = self.detect_overlays(raw_data)
        
        # Incentive eligibility
        toc = self.analyze_toc_eligibility(raw_data)
        state_db = self.analyze_state_density_bonus(zone)
        ed1 = self.analyze_ed1_eligibility(zone)
        sb9 = self.analyze_sb9_eligibility(zone, lot_area_sqft)
        
        incentives = IncentiveEligibility(
            toc=toc,
            state_density_bonus=state_db,
            ed1=ed1,
            sb9=sb9
        )
        
        # Transit and parking
        transit_parking = self.calculate_transit_parking(zone)
        
        # Hazards
        hazards = self.analyze_hazards(raw_data)
        
        # Baseline envelope
        baseline = self.create_baseline_envelope(lot_units, zone, height_district)
        
        # Scenarios
        scenarios = DerivedEnvelopes(
            baseline=baseline,
            toc=self.create_toc_scenario(baseline, toc, lot_units) if toc.eligible else None
        )
        
        return {
            'core_zoning_envelope': asdict(core),
            'lot_units': asdict(lot_units),
            'overlays': asdict(overlays),
            'incentive_eligibility': asdict(incentives),
            'transit_parking': asdict(transit_parking),
            'hazards': asdict(hazards),
            'derived_envelopes': asdict(scenarios),
            'citations': [asdict(c) for c in self.citations]
        }