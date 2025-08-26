"""
Development Potential Analyzer
Focus: What can be built on this lot?
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re

@dataclass
class DevelopmentScenario:
    name: str
    description: str
    total_units: float
    net_new_units: float
    affordability_required: str
    approval_path: str
    key_benefits: List[str]
    constraints: List[str]
    feasibility: str
    unit_calculation_justification: str = ""
    legal_citations: List[str] = None
    regulatory_pathway_explanation: str = ""
    recommendation_score: float = 0.0
    recommendation_reason: str = ""
    
    def __post_init__(self):
        if self.legal_citations is None:
            self.legal_citations = []
        else:
            # Filter out None values from legal citations
            self.legal_citations = [citation for citation in self.legal_citations if citation is not None]
    
@dataclass
class BaseZoning:
    zone: str
    height_district: str
    complete_zone: str
    density_factor: int
    baseline_units: float
    height_limit_ft: float
    far_limit: float
    interpretation: str

@dataclass
class ExistingConditions:
    units: int
    building_sf: float
    year_built: str
    is_rso: bool
    replacement_required: int
    above_baseline: bool
    demolition_constraints: List[str]

@dataclass
class IncentiveOpportunities:
    toc_tier: Optional[int] = None
    toc_distance_description: str = ""
    state_density_bonus: bool = False
    ab2097_eligible: bool = False
    opportunity_zone: bool = False
    adaptive_reuse: bool = False
    ed1_eligible: bool = False
    sb9_eligible: bool = False
    sb9_lot_split_eligible: bool = False
    
    # New comprehensive state programs
    sb35_eligible: bool = False
    sb35_description: str = ""
    sb330_eligible: bool = False
    sb330_description: str = ""
    ab2011_eligible: bool = False
    ab2011_description: str = ""
    sb423_eligible: bool = False
    sb423_description: str = ""
    sb4_eligible: bool = False
    sb4_description: str = ""
    ab1287_eligible: bool = False
    ab1287_description: str = ""
    ab1449_eligible: bool = False
    ab1449_description: str = ""
    sb684_eligible: bool = False
    sb684_description: str = ""
    ab2334_eligible: bool = False
    ab2334_description: str = ""

@dataclass
class Constraints:
    environmental_hazards: List[str]
    historic_restrictions: List[str]
    overlay_requirements: List[str]
    rso_replacement_units: int
    
@dataclass
class DevelopmentAnalysis:
    property_summary: str
    base_zoning: BaseZoning
    existing_conditions: ExistingConditions
    incentive_opportunities: IncentiveOpportunities
    constraints: Constraints
    development_scenarios: List[DevelopmentScenario]
    bottom_line: str
    next_steps: List[str]

class DevelopmentAnalyzer:
    """Analyzes what can be built on a lot"""
    
    FEASIBILITY_CRITERIA = {
        "High": [
            "Clear regulatory pathway with established precedent",
            "Minimal environmental or historic constraints", 
            "Strong market demand for housing type",
            "Streamlined approval process available"
        ],
        "Medium": [
            "Some complexity due to constraints or over-built conditions",
            "Additional studies or mitigation may be required",
            "RSO replacement adds complexity but manageable",
            "Environmental hazards require engineering solutions"
        ],
        "Low": [
            "Significant regulatory or environmental barriers",
            "Historic restrictions or community opposition likely",
            "Complex approval process with uncertain outcome",
            "Market conditions unfavorable for housing type"
        ]
    }
    
    DENSITY_FACTORS = {
        'R1': 5000, 'RS': 5000, 'RE': 2000, 'RA': 2000,
        'RD1.5': 1500, 'RD2': 2000, 'RD3': 1500, 'RD4': 1200, 'RD5': 1000, 'RD6': 800,
        'RU': 800, 'R2': 800, 'R3': 800, 'R4': 400, 'R5': 200
    }
    
    HEIGHT_LIMITS = {
        '1': 45, '1L': 30, '1VL': 25, '1XL': 20, '2': 75, '3': 150, '4': 275, 'NL': None
    }
    
    FAR_LIMITS = {
        '1': 1.5, '2': 6.0, '3': 6.0, '4': 13.0, 'NL': None
    }
    
    def analyze_development_potential(self, property_data: Dict) -> DevelopmentAnalysis:
        """Main analysis function"""
        
        # Parse basic data
        zone = self._extract_zone(property_data)
        height_district = self._extract_height_district(property_data)
        lot_area = property_data.get('lot_area_sqft', 0)
        existing_units = property_data.get('existing_units', 0)
        building_sf = property_data.get('building_sf', 0)
        year_built = property_data.get('year_built', '')
        is_rso = property_data.get('is_rso', False)
        address = property_data.get('address', '')
        
        # Base zoning analysis
        base_zoning = self._analyze_base_zoning(zone, height_district, lot_area)
        
        # Existing conditions
        existing_conditions = self._analyze_existing_conditions(
            existing_units, building_sf, year_built, is_rso, base_zoning.baseline_units
        )
        
        # Incentive opportunities
        incentives = self._analyze_incentives(property_data, zone)
        
        # Constraints
        constraints = self._analyze_constraints(property_data, existing_conditions)
        
        # Development scenarios
        scenarios = self._generate_scenarios(
            base_zoning, existing_conditions, incentives, constraints, lot_area
        )
        # Consolidate scenarios with same unit count
        scenarios = self._consolidate_scenarios(scenarios)
        
        # Score and rank scenarios
        scenarios = self._score_scenarios(scenarios, base_zoning, existing_conditions, lot_area)
        
        # Bottom line assessment
        bottom_line = self._generate_bottom_line(base_zoning, existing_conditions, scenarios)
        
        # Next steps
        next_steps = self._generate_next_steps(scenarios, constraints)
        
        # Property summary
        summary = self._generate_property_summary(property_data, lot_area, base_zoning, existing_conditions)
        
        analysis = DevelopmentAnalysis(
            property_summary=summary,
            base_zoning=base_zoning,
            existing_conditions=existing_conditions,
            incentive_opportunities=incentives,
            constraints=constraints,
            development_scenarios=scenarios,
            bottom_line=bottom_line,
            next_steps=next_steps
        )
        
        # Add feasibility criteria to the analysis
        analysis.feasibility_criteria = self.FEASIBILITY_CRITERIA
        
        return analysis
    
    def _extract_zone(self, data: Dict) -> str:
        """Extract base zone from various data sources"""
        zone = data.get('zone', '')
        
        # First try ZIMAS comprehensive data
        if not zone:
            zimas_data = data.get('zimas_data', {})
            if zimas_data and 'zoning' in zimas_data:
                # Look through all zoning layers
                for layer_name, attributes in zimas_data['zoning'].items():
                    if isinstance(attributes, dict):
                        # Try ZONE_CLASS first (clean base zone)
                        zone_class = attributes.get('ZONE_CLASS')
                        if zone_class and zone_class != 'Null':
                            zone = zone_class
                            break
                        # Fallback to ZONE_CMPLT (complete zone)
                        zone_cmplt = attributes.get('ZONE_CMPLT')
                        if zone_cmplt and zone_cmplt != 'Null':
                            zone = zone_cmplt.split('-')[0]  # Extract base zone from R3-1
                            break
        
        # Fallback: infer from use code if still no zone
        if not zone:
            use_code = data.get('use_code', '')
            if use_code == '0500':
                return 'R4'  # Multi-family
            elif use_code.startswith('1'):
                return 'R1'  # Single family
        
        return zone.split('-')[0] if zone and '-' in zone else zone or ''
    
    def _extract_height_district(self, data: Dict) -> str:
        """Extract height district"""
        hd = data.get('height_district', '')
        
        # First try ZIMAS comprehensive data
        if not hd:
            zimas_data = data.get('zimas_data', {})
            if zimas_data and 'zoning' in zimas_data:
                # Look through all zoning layers
                for layer_name, attributes in zimas_data['zoning'].items():
                    if isinstance(attributes, dict):
                        # Try to extract from ZONE_CMPLT (e.g., "R3-1")
                        zone_cmplt = attributes.get('ZONE_CMPLT')
                        if zone_cmplt and '-' in zone_cmplt:
                            hd = zone_cmplt.split('-')[1]
                            break
        
        # Fallback: extract from zone if available
        if not hd:
            zone = data.get('zone', '')
            if '-' in zone:
                hd = zone.split('-')[1]
                
        return hd
    
    def _analyze_base_zoning(self, zone: str, height_district: str, lot_area: float) -> BaseZoning:
        """Analyze base zoning envelope"""
        density_factor = self.DENSITY_FACTORS.get(zone, 1000)
        baseline_units = lot_area / density_factor if density_factor > 0 else 0
        height_limit = self.HEIGHT_LIMITS.get(height_district, 45)
        far_limit = self.FAR_LIMITS.get(height_district, 1.5)
        
        # Interpretation
        interpretation = f"{zone} allows ~1 unit per {density_factor:,} sq ft of lot area."
        if height_district == '2':
            interpretation += f" Height District 2 allows up to {height_limit} ft height and {far_limit}:1 FAR."
        
        return BaseZoning(
            zone=zone,
            height_district=height_district,
            complete_zone=f"{zone}-{height_district}" if height_district else zone,
            density_factor=density_factor,
            baseline_units=baseline_units,
            height_limit_ft=height_limit or 200,
            far_limit=far_limit or 6.0,
            interpretation=interpretation
        )
    
    def _analyze_existing_conditions(self, existing_units: int, building_sf: float, 
                                   year_built: str, is_rso: bool, baseline_units: float) -> ExistingConditions:
        """Analyze existing building conditions"""
        replacement_required = existing_units if is_rso else 0
        above_baseline = existing_units > baseline_units
        
        demolition_constraints = []
        if is_rso:
            demolition_constraints.append("RSO replacement: Must replace existing rent-stabilized units 1:1")
        if year_built and int(year_built or 0) < 1978:
            demolition_constraints.append("Historic review may be required for pre-1978 buildings")
        
        return ExistingConditions(
            units=existing_units,
            building_sf=building_sf,
            year_built=year_built,
            is_rso=is_rso,
            replacement_required=replacement_required,
            above_baseline=above_baseline,
            demolition_constraints=demolition_constraints
        )
    
    def _analyze_incentives(self, data: Dict, zone: str) -> IncentiveOpportunities:
        """Analyze available incentive programs"""
        
        # Real ZIMAS TOC analysis
        toc_tier = None
        toc_description = "TOC eligibility requires proximity analysis to major transit"
        
        # Check comprehensive ZIMAS data for TOC information
        zimas_data = data.get('zimas_data', {})
        if zimas_data:
            # Look for TOC tier in transit_housing section
            transit_housing = zimas_data.get('transit_housing', {})
            for layer_name, attributes in transit_housing.items():
                if 'toc' in layer_name.lower():
                    # Look for tier information in attributes
                    for key, value in attributes.items():
                        if 'tier' in key.lower() and str(value).isdigit():
                            toc_tier = int(value)
                            toc_description = f"Property is within TOC Tier {toc_tier} area (ZIMAS verified)"
                            break
                        elif 'tier' in str(value).lower():
                            # Extract tier number from string like "Tier 1"
                            import re
                            tier_match = re.search(r'tier\s*(\d+)', str(value).lower())
                            if tier_match:
                                toc_tier = int(tier_match.group(1))
                                toc_description = f"Property is within TOC Tier {toc_tier} area (ZIMAS verified)"
                                break
                if toc_tier:
                    break
        
        # Fallback to mock/manual data if available
        if not toc_tier and data.get('toc_tier'):
            toc_tier = int(data['toc_tier'])
            toc_description = f"Property is within TOC Tier {toc_tier} area"
        
        # SB-9 (duplex/lot split) - only for R1 zones
        lot_area = data.get('lot_area_sqft', 0) or data.get('Shape.STArea()', 0) or 0
        sb9_eligible = zone == 'R1'
        sb9_lot_split_eligible = sb9_eligible and lot_area >= 2400  # Min lot size for split
        
        # SB-35/SB-423 Streamlined Affordable Housing
        # Eligible if jurisdiction hasn't met RHNA goals (would need HCD data)
        sb35_eligible = zone.startswith('R') and zone not in ['R1', 'RS']
        sb35_description = "Ministerial approval for affordable housing if jurisdiction hasn't met RHNA goals"
        sb423_eligible = sb35_eligible
        sb423_description = "Extended SB-35 through 2036 with broader application including coastal zones"
        
        # SB-330 Housing Crisis Act / Builder's Remedy
        # Available when housing element not certified (would need HCD certification status)
        sb330_eligible = zone.startswith('R')
        sb330_description = "Builder's Remedy available if housing element not certified by HCD"
        
        # AB-2011 Commercial to Housing
        # Commercial zones can be converted to housing
        commercial_zones = ['C1', 'C2', 'C4', 'CM', 'CR', 'CW']
        use_code = data.get('use_code', '')
        is_commercial = any(zone.startswith(cz) for cz in commercial_zones) or use_code.startswith('5')
        ab2011_eligible = is_commercial or zone.startswith('R')
        ab2011_description = "Ministerial approval for housing on commercially-zoned land"
        
        # SB-4 Faith-Based/University Housing
        # Would need to check if property is owned by faith-based or educational institution
        sb4_eligible = zone.startswith('R')  # Conservative - all residential zones
        sb4_description = "Streamlined 100% affordable housing on faith-based or university land"
        
        # AB-1287 Enhanced Density Bonus (up to 100%)
        ab1287_eligible = zone.startswith('R') and zone not in ['R1', 'RS']
        ab1287_description = "Up to 100% density bonus for moderate and very low income units"
        
        # AB-1449 CEQA Exemption for Affordable Housing
        ab1449_eligible = zone.startswith('R')
        ab1449_description = "CEQA exemption for affordable housing on infill sites near transit"
        
        # SB-684 Small Site Housing (up to 10 units) - CORRECTED RULES
        # Eligible for multifamily zones, urban lots under 5 acres
        sb684_eligible = zone.startswith('R') and zone not in ['R1', 'RS'] and lot_area < 217800  # 5 acres = 217,800 sf
        sb684_description = "Ministerial approval for up to 10 units on urban lots under 5 acres. No affordability requirement."
        
        # AB-2334 Enhanced Base Density Definition
        ab2334_eligible = zone.startswith('R') and zone not in ['R1', 'RS']
        ab2334_description = "Clarified base density calculation and additional concessions for 100% affordable projects"
        
        return IncentiveOpportunities(
            toc_tier=toc_tier,
            toc_distance_description=toc_description,
            state_density_bonus=zone.startswith('R') and zone not in ['R1', 'RS'],
            ab2097_eligible=True,  # Would check transit proximity
            opportunity_zone=False,  # Would check OZ designation
            adaptive_reuse=False,   # Would check ARIA designation
            ed1_eligible=zone.startswith('R'),
            sb9_eligible=sb9_eligible,
            sb9_lot_split_eligible=sb9_lot_split_eligible,
            
            # New comprehensive state programs
            sb35_eligible=sb35_eligible,
            sb35_description=sb35_description,
            sb330_eligible=sb330_eligible, 
            sb330_description=sb330_description,
            ab2011_eligible=ab2011_eligible,
            ab2011_description=ab2011_description,
            sb423_eligible=sb423_eligible,
            sb423_description=sb423_description,
            sb4_eligible=sb4_eligible,
            sb4_description=sb4_description,
            ab1287_eligible=ab1287_eligible,
            ab1287_description=ab1287_description,
            ab1449_eligible=ab1449_eligible,
            ab1449_description=ab1449_description,
            sb684_eligible=sb684_eligible,
            sb684_description=sb684_description,
            ab2334_eligible=ab2334_eligible,
            ab2334_description=ab2334_description
        )
    
    def _analyze_constraints(self, data: Dict, existing: ExistingConditions) -> Constraints:
        """Analyze development constraints"""
        
        hazards = []
        raw_data = data.get('raw_data', {})
        if raw_data.get('METHANE_ZONE'):
            hazards.append("Methane buffer zone - special foundation/venting required")
        if raw_data.get('ALQUIST_PRIOLO_FAULT_ZONE'):
            hazards.append("Seismic fault zone - enhanced seismic design required")
        if raw_data.get('LIQUEFACTION'):
            hazards.append("Liquefaction risk - foundation considerations")
        
        historic = []
        if existing.year_built and int(existing.year_built or 0) < 1960:
            historic.append("Pre-1960 building may require historic review")
        
        overlays = []
        # Would add specific plan requirements, CPIO, etc.
        
        return Constraints(
            environmental_hazards=hazards,
            historic_restrictions=historic,
            overlay_requirements=overlays,
            rso_replacement_units=existing.replacement_required
        )
    
    def _generate_scenarios(self, base: BaseZoning, existing: ExistingConditions, 
                          incentives: IncentiveOpportunities, constraints: Constraints,
                          lot_area: float) -> List[DevelopmentScenario]:
        """Generate development scenarios with clear unlock requirements"""
        scenarios = []
        
        # Scenario 1: By-Right
        by_right_units = max(base.baseline_units, existing.units)  # Can't go below existing if RSO
        
        # Feasibility logic for by-right
        if existing.is_rso and existing.units > base.baseline_units:
            feasibility = "Medium"  # Over-built RSO properties are complex
            feasibility_reason = "Existing building exceeds base zoning density"
        elif len(constraints.environmental_hazards) > 2:
            feasibility = "Medium"  # Multiple hazards complicate development
            feasibility_reason = "Multiple environmental hazards present"
        else:
            feasibility = "High"
            feasibility_reason = "Clear regulatory path"
            
        scenarios.append(DevelopmentScenario(
            name="By-Right",
            description=f"UNLOCK: Automatic right under {base.complete_zone} zoning. No special requirements.",
            total_units=by_right_units,
            net_new_units=max(0, by_right_units - existing.units),
            affordability_required="None",
            approval_path="Administrative (if no demo) or CPC (if demo required)",
            key_benefits=["No affordability requirement", "Predictable approval", "Fastest path"],
            constraints=["Limited unit count"] + (["RSO replacement required"] if existing.is_rso else []),
            feasibility=f"{feasibility} - {feasibility_reason}",
            unit_calculation_justification=f"STEP 1: Calculate baseline density\n{lot_area:,.0f} sq ft lot ÷ {base.density_factor:,} sq ft/unit ({base.zone} requirement) = {base.baseline_units:.1f} units\n\nSTEP 2: Apply zoning rules\nBy-right development = {base.baseline_units:.1f} units maximum\n\nFINAL: {by_right_units:.0f} units total" + (f"\n(Note: Must maintain {existing.units} existing RSO units)" if existing.is_rso else ""),
            legal_citations=[
                f"LAMC 12.{base.zone[1:] if base.zone.startswith('R') and len(base.zone) > 1 else '07'}: {base.zone} zone density requirement",
                f"LAMC 12.21.C: Height District {base.height_district} regulations" if base.height_district else "LAMC 12.21.C: Height regulations",
                "SB 330 Housing Crisis Act: RSO replacement requirements" if existing.is_rso else None
            ],
            regulatory_pathway_explanation=f"Submit building permit application to LADBS for {base.zone} zoned property. Administrative approval if no demolition required. If demolition needed, may require City Planning Commission (CPC) approval and historic review process. Standard plan check, building inspection, and certificate of occupancy process. Timeline: 3-6 months for permits, 6-18 months construction depending on project size."
        ))
        
        # Scenario 2: TOC (if eligible)
        if incentives.toc_tier:
            tier = incentives.toc_tier
            bonus_pct = {1: 50, 2: 60, 3: 70, 4: 80}.get(tier, 50)
            affordability_req = {1: "8% VLI", 2: "9% VLI", 3: "10% VLI", 4: "11% VLI"}.get(tier, "11% VLI")
            toc_units = base.baseline_units * (1 + bonus_pct / 100)
            toc_total = max(toc_units, existing.units)  # Must still replace existing
            
            # TOC feasibility logic
            if existing.is_rso:
                toc_feasibility = "High - RSO replacement required but TOC streamlines process"
            elif len(constraints.environmental_hazards) > 1:
                toc_feasibility = "Medium - Environmental hazards may complicate construction"
            else:
                toc_feasibility = "High - Clear path with strong incentives"
            
            scenarios.append(DevelopmentScenario(
                name=f"TOC Tier {tier}",
                description=f"UNLOCK: Property within ½ mile of major transit stop (Tier {tier} area). Requires {affordability_req} affordable units.",
                total_units=toc_total,
                net_new_units=toc_total - existing.units,
                affordability_required=affordability_req,
                approval_path="Administrative approval (no CUP required)",
                key_benefits=[f"{bonus_pct}% density bonus", "Reduced parking (0.5/unit or none)", "Height bonus possible", "Streamlined approval", "No parking minimums if Tier 3+"],
                constraints=["Affordability requirement"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility=toc_feasibility,
                unit_calculation_justification=f"Baseline {base.baseline_units:.2f} units × {bonus_pct/100 + 1:.2f} (TOC Tier {tier} = {bonus_pct}% bonus) = {toc_units:.2f} units" + (f" (floor = {existing.units} existing due to RSO)" if existing.is_rso and existing.units > toc_units else ""),
                legal_citations=[
                    f"LAMC 12.22-A.31: TOC Tier {tier} density bonus ({bonus_pct}%)",
                    f"TOC Guidelines: {affordability_req} affordability requirement for Tier {tier}",
                    "Measure JJJ (2016): Voter-approved TOC program",
                    "SB 330 Housing Crisis Act: RSO replacement requirements" if existing.is_rso else None
                ],
                regulatory_pathway_explanation=f"Submit TOC application to City Planning with affordable housing commitment ({affordability_req}). Administrative approval - no public hearing or conditional use permit required. Record affordable housing covenant. Building permits through LADBS with expedited plan check. Must comply with prevailing wage requirements. Timeline: 2-4 months for entitlements, 4-6 months for permits, expedited processing for TOC projects."
            ))
        
        # Scenario 3: State Density Bonus (2024 Rules)
        if incentives.state_density_bonus:
            # CORRECTED: 50% max bonus for 15% very low income (as of 2020)
            # 5% VLI = 20% bonus, 15% VLI = 50% bonus
            sdb_units = base.baseline_units * 1.50  # Using 50% max bonus
            sdb_total = max(sdb_units, existing.units)
            
            # State DB feasibility logic
            if existing.is_rso and existing.units > base.baseline_units:
                sdb_feasibility = "Medium - Complex due to over-built RSO property"
            elif base.zone.startswith('R') and base.zone not in ['R1', 'RS']:
                sdb_feasibility = "High - Multi-family zones have established SDB precedent"
            else:
                sdb_feasibility = "High - Straightforward application"
            
            scenarios.append(DevelopmentScenario(
                name="State Density Bonus",
                description=f"UNLOCK: Available to all multi-family zones ({base.zone}). Requires 15% Very Low Income affordable units to achieve maximum 50% bonus.",
                total_units=sdb_total,
                net_new_units=sdb_total - existing.units,
                affordability_required="15% Very Low Income units (50% bonus) or sliding scale from 5% VLI (20% bonus)",
                approval_path="By-right with density bonus application (Gov Code 65915)",
                key_benefits=["Up to 50% density bonus", "Up to 3 concessions (parking, setback, height)", "Reduced parking possible", "Cannot be denied if compliant"],
                constraints=["Affordability requirement"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility=sdb_feasibility,
                unit_calculation_justification=f"STEP 1: Calculate baseline density\n{lot_area:,.0f} sq ft lot ÷ {base.density_factor:,} sq ft/unit ({base.zone} requirement) = {base.baseline_units:.1f} units\n\nSTEP 2: Apply State Density Bonus\n{base.baseline_units:.1f} baseline units × 1.50 (50% bonus for 15% VLI units) = {sdb_units:.1f} units\n\nSTEP 3: Check minimums\nmax({sdb_units:.1f} density bonus units, {existing.units} existing units) = {sdb_total:.1f} units\n\nFINAL: {sdb_total:.0f} units total (requires 15% very low income affordable)",
                legal_citations=[
                    "Gov Code 65915: California State Density Bonus Law",
                    "Gov Code 65915(b)(1)(B): 15% VLI units = 50% density bonus",
                    "AB 2345 (2020): Increased maximum bonus from 35% to 50%",
                    "Gov Code 65915(d): Up to 3 regulatory concessions",
                    "SB 330 Housing Crisis Act: RSO replacement requirements" if existing.is_rso else None
                ],
                regulatory_pathway_explanation="Submit density bonus application to City Planning concurrent with building permit application. Cannot be denied if project meets objective standards. Negotiate up to 3 regulatory concessions (parking reduction, setback waivers, height increases). Record affordable housing covenant with 55-year term. Administrative approval - no public hearing required. Timeline: 60 days for density bonus determination, 4-8 months total permitting."
            ))
        
        # Scenario 4: SB-9 (for R1 zones)
        if incentives.sb9_eligible:
            # SB-9 allows duplex on existing lot
            sb9_duplex_units = 2.0
            sb9_duplex_total = max(sb9_duplex_units, existing.units)
            
            # SB-9 lot split scenario (if eligible)
            if incentives.sb9_lot_split_eligible:
                sb9_split_units = 4.0  # 2 units per lot after split
                sb9_split_total = max(sb9_split_units, existing.units)
                
                # Lot split feasibility
                if existing.units > 1:
                    split_feasibility = "Medium - Existing multi-unit may complicate lot split process"
                else:
                    split_feasibility = "High - Clear ministerial approval pathway for lot split"
                
                scenarios.append(DevelopmentScenario(
                    name="SB-9 Lot Split + Duplex",
                    description=f"UNLOCK: R1 zone with lot ≥2,400 sq ft. Split lot into two parcels, build duplex on each (4 total units). Ministerial approval required.",
                    total_units=sb9_split_total,
                    net_new_units=sb9_split_total - existing.units,
                    affordability_required="None",
                    approval_path="Ministerial approval (SB-9, Gov Code 66411.7)",
                    key_benefits=["No affordability requirement", "Ministerial approval (no discretionary review)", "No parking minimums", "Maximum 4 total units", "Can sell lots separately"],
                    constraints=["Minimum 1,200 sq ft per lot after split", "Owner-occupancy required for 3 years", "Cannot demolish existing home in some cases"],
                    feasibility=split_feasibility,
                    unit_calculation_justification=f"SB-9 lot split allows division of {lot_area:,.0f} sq ft R1 lot into two parcels (minimum 1,200 sq ft each), with duplex allowed on each parcel = 2 units × 2 lots = 4 total units maximum. Calculation: Lot split eligible (lot ≥ 2,400 sq ft) → 2 parcels × 2 units each = 4 units total.",
                    legal_citations=["Gov Code 66411.7 (SB-9 lot split)", "Gov Code 65852.21 (SB-9 duplex allowance)", "AB-2097 (no parking minimums)"],
                    regulatory_pathway_explanation="Submit ministerial SB-9 application to City Planning for lot split approval. Concurrent submittal of building permits for duplexes to LADBS. Owner-occupancy declaration required for 3+ years. No public hearing or discretionary review allowed. Must meet objective design standards. Timeline: 60 days maximum for lot split approval, 4-6 months for building permits, total 6-10 months."
                ))
            
            # Basic duplex scenario (no lot split)
            duplex_feasibility = "High - Simple ministerial conversion to duplex"
            if existing.units > 1:
                duplex_feasibility = "Medium - May need to reduce units to comply with duplex limit"
                
            scenarios.append(DevelopmentScenario(
                name="SB-9 Duplex",
                description=f"UNLOCK: R1 zone allows duplex conversion. Convert single-family home to duplex or build new duplex on existing lot.",
                total_units=sb9_duplex_total,
                net_new_units=sb9_duplex_total - existing.units,
                affordability_required="None",
                approval_path="Ministerial approval (SB-9, Gov Code 65852.21)",
                key_benefits=["No affordability requirement", "Ministerial approval", "No parking minimums if near transit", "Preserve neighborhood character"],
                constraints=["Owner-occupancy required for 3 years", "Cannot exceed duplex (2 units) on single lot"],
                feasibility=duplex_feasibility,
                unit_calculation_justification=f"SB-9 allows up to 2 units (duplex) on any R1-zoned lot regardless of size. Existing {existing.units} units → maximum 2 units allowed under SB-9 duplex provision. Calculation: max(2 units from SB-9, {existing.units} existing units) = {sb9_duplex_total} units total.",
                legal_citations=["Gov Code 65852.21 (SB-9 duplex allowance)", "AB-2097 (no parking minimums near transit)", "Gov Code 65852.21(f) (owner-occupancy requirement)"],
                regulatory_pathway_explanation="Submit ministerial SB-9 duplex application to City Planning and building permits to LADBS. Owner-occupancy declaration for 3+ years required. Administrative approval only - no public hearings allowed. Must comply with objective development standards and building codes. Timeline: 60 days maximum for SB-9 approval, 4-6 months for permits, total 5-8 months."
            ))
        
        # Scenario 5: 100% Affordable (ED-1)
        if incentives.ed1_eligible:
            # Assume maximum envelope for 100% affordable
            affordable_units = base.baseline_units * 2.0  # Conservative estimate
            affordable_total = max(affordable_units, existing.units)
            
            # ED-1 feasibility logic
            if existing.is_rso and existing.units >= 5:
                ed1_feasibility = "Medium - RSO replacement complex but ED-1 provides strong tools"
            elif len(constraints.environmental_hazards) >= 2:
                ed1_feasibility = "Medium - Environmental hazards require mitigation"
            elif base.zone.startswith('R') and int(base.zone[1:]) >= 3:
                ed1_feasibility = "High - Well-suited for higher density affordable housing"
            else:
                ed1_feasibility = "High - Strong policy support and streamlined process"
            
            scenarios.append(DevelopmentScenario(
                name="100% Affordable (ED-1)",
                description=f"UNLOCK: Available to all residential zones ({base.zone}). Requires 100% affordable housing commitment (can be mix of income levels).",
                total_units=affordable_total,
                net_new_units=affordable_total - existing.units,
                affordability_required="100% affordable housing (mix of VLI, LI, Moderate allowed)",
                approval_path="Ministerial approval (Executive Directive 1)",
                key_benefits=["No parking requirements", "Maximum height/FAR allowed", "Streamlined ministerial approval", "No EIR required", "Expedited permitting"],
                constraints=["100% affordability requirement"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility=ed1_feasibility,
                unit_calculation_justification=f"STEP 1: Calculate baseline density\n{lot_area:,.0f} sq ft lot ÷ {base.density_factor:,} sq ft/unit ({base.zone} requirement) = {base.baseline_units:.1f} units\n\nSTEP 2: Apply ED-1 envelope bonus\n{base.baseline_units:.1f} baseline units × 2.0 (ED-1 allows maximum envelope) = {affordable_units:.1f} units\n\nSTEP 3: Check minimums\nmax({affordable_units:.1f} ED-1 units, {existing.units} existing units) = {affordable_total:.1f} units\n\nFINAL: {affordable_total:.0f} units total (100% affordable housing required)",
                legal_citations=["Executive Directive No. 1 (Mayor's Directive)", "LAMC 12.22-A.25 (100% affordable housing)", "Gov Code 65915 (no parking requirements for affordable)", "SB-35 streamlining provisions"]
            ))
        
        # Scenario 6: SB-35 Streamlined Affordable Housing
        if incentives.sb35_eligible:
            sb35_units = base.baseline_units * 1.25  # 25% bonus typical for streamlined
            sb35_total = max(sb35_units, existing.units)
            
            scenarios.append(DevelopmentScenario(
                name="SB-35 Streamlined Affordable",
                description=f"UNLOCK: {incentives.sb35_description}. Requires 20% affordable units.",
                total_units=sb35_total,
                net_new_units=sb35_total - existing.units,
                affordability_required="20% affordable housing (varies by income mix)",
                approval_path="Ministerial approval (SB-35, Gov Code 65913.4)",
                key_benefits=["No CEQA review", "Ministerial approval", "Cannot be denied if compliant", "Expedited processing"],
                constraints=["Affordability requirement", "Jurisdiction must not have met RHNA goals"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility="High - Strong legal protection against denial",
                unit_calculation_justification=f"SB-35 streamlined approval allows 25% density bonus for affordable housing projects. Base density {base.baseline_units:.1f} units × 1.25 SB-35 bonus = {sb35_units:.1f} units. Requires jurisdiction to have failed RHNA goals and 20% affordable units. Calculation: {base.baseline_units:.1f} baseline units × 125% SB-35 bonus = {sb35_total:.1f} units total.",
                legal_citations=["Gov Code 65913.4 (SB-35 streamlined approval)", "Gov Code 65913.4(a)(5) (20% affordability)", "Gov Code 65913.4(c) (CEQA exemption)", "Gov Code 65913.4(b) (ministerial approval)"]
            ))
        
        # Scenario 7: AB-2011 Commercial to Housing
        if incentives.ab2011_eligible and base.zone.startswith('C'):
            ab2011_units = lot_area / 400  # Assume R4-level density on commercial land
            ab2011_total = max(ab2011_units, existing.units)
            
            scenarios.append(DevelopmentScenario(
                name="AB-2011 Commercial Conversion",
                description=f"UNLOCK: {incentives.ab2011_description}. Convert commercial property to housing.",
                total_units=ab2011_total,
                net_new_units=ab2011_total - existing.units,
                affordability_required="15% affordable housing or comparable fees",
                approval_path="Ministerial approval (AB-2011, Gov Code 65912.111)",
                key_benefits=["Ministerial approval", "Commercial to residential conversion", "Prevailing wage jobs", "CEQA streamlining"],
                constraints=["Affordability requirement", "Prevailing wage requirement", "Must meet objective standards"],
                feasibility="High - Clear conversion path for commercial properties",
                unit_calculation_justification=f"AB-2011 allows ministerial conversion of commercial land to housing at R4-equivalent density (1 unit per 400 sq ft). Lot area {lot_area:,.0f} sq ft ÷ 400 sq ft/unit = {ab2011_units:.1f} units maximum on commercial {base.zone} zone. Calculation: {lot_area:,.0f} sq ft lot ÷ 400 sq ft per unit = {ab2011_total:.1f} units total.",
                legal_citations=["Gov Code 65912.111 (AB-2011 commercial conversion)", "Gov Code 65912.111(h) (15% affordability)", "Gov Code 65912.111(f) (prevailing wage)", "Gov Code 65912.111(g) (CEQA streamlining)"]
            ))
        
        # Scenario 8: AB-1287 Enhanced Density Bonus (100%)
        if incentives.ab1287_eligible:
            ab1287_units = base.baseline_units * 2.0  # Up to 100% density bonus
            ab1287_total = max(ab1287_units, existing.units)
            
            scenarios.append(DevelopmentScenario(
                name="AB-1287 Enhanced Density Bonus",
                description=f"UNLOCK: {incentives.ab1287_description}. Up to 100% density bonus with moderate income units.",
                total_units=ab1287_total,
                net_new_units=ab1287_total - existing.units,
                affordability_required="Mix of moderate and very low income units for maximum bonus",
                approval_path="By-right with enhanced density bonus application",
                key_benefits=["Up to 100% density bonus", "Missing middle housing focus", "Additional concessions available", "Cannot be denied if compliant"],
                constraints=["Enhanced affordability requirement"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility="High - Enhanced version of proven density bonus law",
                unit_calculation_justification=f"AB-1287 enhanced density bonus allows up to 100% density bonus (double base density) for moderate and very low income units. Base density {base.baseline_units:.1f} units × 2.0 maximum AB-1287 bonus = {ab1287_units:.1f} units. Requires enhanced affordability mix. Calculation: {base.baseline_units:.1f} baseline units × 200% AB-1287 bonus = {ab1287_total:.1f} units total.",
                legal_citations=["Gov Code 65915(f)(4) (AB-1287 enhanced bonus)", "Gov Code 65915.7 (moderate income provisions)", "Gov Code 65915(d)(2)(C) (100% bonus)", "Gov Code 65915(k) (additional concessions)"]
            ))
        
        # Scenario 9: SB-330 Builder's Remedy 
        if incentives.sb330_eligible:
            sb330_units = base.baseline_units * 1.5  # Assumes significant upzoning potential
            sb330_total = max(sb330_units, existing.units)
            
            scenarios.append(DevelopmentScenario(
                name="SB-330 Builder's Remedy",
                description=f"UNLOCK: {incentives.sb330_description}. Available when local housing element not certified.",
                total_units=sb330_total,
                net_new_units=sb330_total - existing.units,
                affordability_required="20% affordable housing",
                approval_path="Ministerial approval with Builder's Remedy protections",
                key_benefits=["Overrides local zoning", "Ministerial approval", "Cannot be downzoned", "Strong legal protections"],
                constraints=["Only available during housing element non-compliance", "Affordability requirement", "Must meet objective standards"],
                feasibility="Medium - Depends on housing element certification status",
                unit_calculation_justification=f"SB-330 Builder's Remedy allows significant density increase when local housing element is not HCD-certified. Base density {base.baseline_units:.1f} units × 1.5 conservative upzoning multiplier = {sb330_units:.1f} units. Available only during housing element non-compliance. Calculation: {base.baseline_units:.1f} baseline units × 150% Builder's Remedy potential = {sb330_total:.1f} units total.",
                legal_citations=["Gov Code 65589.5 (SB-330 Builder's Remedy)", "Gov Code 65589.5(j)(2) (20% affordability)", "Gov Code 65589.5(j)(1) (override local zoning)", "Gov Code 65589.5(n) (ministerial approval)"]
            ))
        
        # Scenario 10: SB-684 Small Site Housing (up to 10 units) - CORRECTED
        if incentives.sb684_eligible:
            # SB-684 allows UP TO 10 units, regardless of zoning density
            # But must be reasonable for the lot size
            max_by_zoning = base.baseline_units
            sb684_units = min(10.0, max(max_by_zoning, 3.0))  # At least 3 units to be meaningful
            sb684_total = max(sb684_units, existing.units)
            
            scenarios.append(DevelopmentScenario(
                name="SB-684 Small Site Housing",
                description=f"UNLOCK: {incentives.sb684_description}. Ministerial approval in 60 days.",
                total_units=sb684_total,
                net_new_units=sb684_total - existing.units,
                affordability_required="None",
                approval_path="Ministerial approval (SB-684) - 60 day maximum",
                key_benefits=["No affordability requirement", "Ministerial approval", "CEQA-exempt", "60-day approval timeline", "No public hearings"],
                constraints=["Maximum 10 units", "Urban lots under 5 acres only", "Must meet objective standards"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility="High - Simple ministerial process for small projects",
                unit_calculation_justification=f"STEP 1: Check SB-684 eligibility\nLot size: {lot_area:,.0f} sq ft < 217,800 sq ft (5 acres) ✓\nZone: {base.zone} (multifamily) ✓\n\nSTEP 2: Calculate SB-684 allowance\nSB-684 maximum = 10 units (regardless of zoning density)\nBase zoning allows = {base.baseline_units:.1f} units\nMeaningful minimum = 3.0 units\n\nSTEP 3: Apply SB-684 formula\nmin(10 SB-684 max, max({base.baseline_units:.1f} zoning, 3.0 minimum)) = {sb684_units:.1f} units\n\nFINAL: {sb684_total:.0f} units total (no affordability required!)",
                legal_citations=["Gov Code 65913.5 (SB-684 small site housing)", "Gov Code 65913.5(a)(1) (10 unit maximum)", "Gov Code 65913.5(a)(2) (5 acre limitation)", "Gov Code 65913.5(b) (60-day approval)", "Gov Code 65913.5(c) (CEQA exemption)"]
            ))
        
        # Score scenarios for recommendations
        scenarios = self._score_scenarios(scenarios, base, existing, lot_area)
        
        return scenarios
    
    def _consolidate_scenarios(self, scenarios: List[DevelopmentScenario]) -> List[DevelopmentScenario]:
        """Consolidate scenarios with same unit count, keeping only the simplest path"""
        # Group scenarios by rounded unit count
        unit_groups = {}
        for scenario in scenarios:
            units_key = round(scenario.total_units)
            if units_key not in unit_groups:
                unit_groups[units_key] = []
            unit_groups[units_key].append(scenario)
        
        # For each unit count, pick the simplest scenario
        consolidated = []
        for units_key, group in unit_groups.items():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Score each scenario by simplicity (lower = simpler)
                for scenario in group:
                    simplicity_score = 0
                    
                    # Affordability requirement penalty
                    if "None" not in scenario.affordability_required:
                        if "100%" in scenario.affordability_required:
                            simplicity_score += 10  # High penalty for 100% affordable
                        else:
                            simplicity_score += 5   # Medium penalty for partial affordable
                    
                    # Approval path penalty
                    if "Ministerial" in scenario.approval_path:
                        simplicity_score += 0   # Best (simplest)
                    elif "Administrative" in scenario.approval_path:
                        simplicity_score += 2   # Medium
                    else:
                        simplicity_score += 5   # Worst (most complex)
                    
                    # Feasibility penalty
                    if "High" in scenario.feasibility:
                        simplicity_score += 0
                    elif "Medium" in scenario.feasibility:
                        simplicity_score += 3
                    else:
                        simplicity_score += 8
                    
                    scenario.simplicity_score = simplicity_score
                
                # Pick the scenario with lowest simplicity score (simplest)
                simplest = min(group, key=lambda s: s.simplicity_score)
                simplest.recommendation_reason = f"Simplest path to achieve {units_key} units"
                consolidated.append(simplest)
                
        
        return consolidated

    def _score_scenarios(self, scenarios: List[DevelopmentScenario], base: BaseZoning, 
                        existing: ExistingConditions, lot_area: float) -> List[DevelopmentScenario]:
        """Score scenarios prioritizing simplicity and ease of development"""
        
        for scenario in scenarios:
            score = 0.0
            reasons = []
            
            # Primary scoring: Ease/Simplicity (40% of total score)
            simplicity_score = getattr(scenario, 'simplicity_score', 0)
            if simplicity_score <= 2:
                score += 4.0
                reasons.append("very easy to build")
            elif simplicity_score <= 5:
                score += 3.0
                reasons.append("easy to build")
            elif simplicity_score <= 8:
                score += 2.0
                reasons.append("moderate complexity")
            else:
                score += 1.0
                reasons.append("complex process")
            
            # Unit yield scoring (30% of total score)
            if base.baseline_units > 0:
                unit_multiplier = scenario.total_units / base.baseline_units
                score += min(unit_multiplier * 1.5, 3.0)  # Cap at 3 points for unit yield
                if unit_multiplier >= 2.0:
                    reasons.append("excellent unit yield")
                elif unit_multiplier >= 1.5:
                    reasons.append("good unit yield")
                elif unit_multiplier >= 1.2:
                    reasons.append("modest unit yield")
            
            # Feasibility scoring (30% of total score)
            if "High" in scenario.feasibility:
                score += 3.0
                reasons.append("high feasibility")
            elif "Medium" in scenario.feasibility:
                score += 2.0
                reasons.append("medium feasibility")
            else:
                score += 1.0
                reasons.append("challenging feasibility")
            
            # Special bonuses based on property characteristics
            if lot_area < 3000:  # Small lot
                if "SB-9" in scenario.name or "SB-684" in scenario.name:
                    score += 1.0
                    reasons.append("perfect for small lots")
            
            if base.zone == "R1":  # R1 zone special case
                if "SB-9" in scenario.name:
                    score += 2.0
                    reasons.append("ideal for R1 properties")
            
            if existing.is_rso:  # RSO properties
                if "TOC" in scenario.name or "State Density" in scenario.name:
                    score += 0.5
                    reasons.append("handles RSO well")
            
            # Set the score and generate friendly reason
            scenario.recommendation_score = score
            scenario.recommendation_reason = f"Recommended because of {', '.join(reasons[:3])}"
            
        # Sort by recommendation score (highest first)
        scenarios.sort(key=lambda x: x.recommendation_score, reverse=True)
        
        return scenarios
    
    def _generate_bottom_line(self, base: BaseZoning, existing: ExistingConditions, 
                            scenarios: List[DevelopmentScenario]) -> str:
        """Generate bottom line assessment"""
        
        if existing.above_baseline:
            baseline_note = f"Site is already above base {base.zone} density ({existing.units} existing vs. {base.baseline_units:.0f} allowed by-right)."
        else:
            baseline_note = f"Site is under-built relative to base {base.zone} density ({existing.units} existing vs. {base.baseline_units:.0f} allowed)."
        
        if existing.is_rso:
            rso_note = f"RSO replacement requirement means any redevelopment must replace the {existing.units} existing rent-stabilized units first."
        else:
            rso_note = "No RSO replacement requirements."
        
        # Find best feasible scenario
        feasible_scenarios = [s for s in scenarios if s.feasibility in ["High", "Medium"]]
        if feasible_scenarios:
            best = max(feasible_scenarios, key=lambda x: x.total_units)
            unlock_note = f"The real unlock is {best.name} (up to {best.total_units:.0f} units)."
            net_note = f"Likely feasible outcome: {best.total_units:.0f} units total with +{best.net_new_units:.0f} net new units."
        else:
            unlock_note = "Limited development potential under current zoning."
            net_note = "Consider zoning changes or alternative strategies."
        
        return f"{baseline_note} {rso_note} {unlock_note} {net_note}"
    
    def _generate_next_steps(self, scenarios: List[DevelopmentScenario], 
                           constraints: Constraints) -> List[str]:
        """Generate recommended next steps"""
        steps = []
        
        # Feasibility steps
        high_feasibility = [s for s in scenarios if s.feasibility == "High"]
        if high_feasibility:
            best = max(high_feasibility, key=lambda x: x.total_units)
            steps.append(f"Pursue {best.name} for optimal unit yield")
            steps.append(f"Confirm {best.affordability_required} affordability strategy")
        
        # Due diligence steps
        if constraints.environmental_hazards:
            steps.append("Conduct environmental due diligence for hazard mitigation")
        
        if constraints.rso_replacement_units > 0:
            steps.append("Develop RSO tenant relocation and replacement unit plan")
        
        steps.append("Verify TOC tier designation and transit proximity")
        steps.append("Engage with planning consultant for entitlement strategy")
        
        return steps
    
    def _generate_property_summary(self, property_data: Dict, lot_area: float, 
                                 base: BaseZoning, existing: ExistingConditions) -> str:
        """Generate property summary with APN and all addresses"""
        apn = property_data.get('apn', '')
        address = property_data.get('address', '')
        all_addresses = property_data.get('all_addresses', [])
        
        # Format addresses display
        if len(all_addresses) > 1:
            addresses_text = f"{len(all_addresses)} addresses: {', '.join(all_addresses[:3])}"
            if len(all_addresses) > 3:
                addresses_text += f" (+{len(all_addresses) - 3} more)"
        elif all_addresses:
            addresses_text = all_addresses[0]
        else:
            addresses_text = address or "Address not available"
        
        year_text = f"({existing.year_built})" if existing.year_built else ""
        
        return f"APN {apn} • {addresses_text} • {lot_area:,.0f} sq ft lot • {base.complete_zone} zoning • {existing.units} existing units {year_text}".strip()