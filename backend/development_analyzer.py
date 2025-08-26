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
    feasibility: str  # "High", "Medium", "Low"
    
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
        if not zone:
            # Infer from use code
            use_code = data.get('use_code', '')
            if use_code == '0500':
                return 'R4'  # Multi-family
            elif use_code.startswith('1'):
                return 'R1'  # Single family
        return zone.split('-')[0] if '-' in zone else zone
    
    def _extract_height_district(self, data: Dict) -> str:
        """Extract height district"""
        hd = data.get('height_district', '')
        zone = data.get('zone', '')
        if not hd and '-' in zone:
            return zone.split('-')[1]
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
        
        # Mock TOC analysis - would use real transit data
        toc_tier = None
        toc_description = "TOC eligibility requires proximity analysis to major transit"
        
        # Check if we can infer TOC from data
        if data.get('toc_tier'):
            toc_tier = int(data['toc_tier'])
            toc_description = f"Property is within TOC Tier {toc_tier} area"
        
        # SB-9 (duplex/lot split) - only for R1 zones
        lot_area = data.get('lot_area_sqft', 0) or data.get('Shape.STArea()', 0) or 0
        sb9_eligible = zone == 'R1'
        sb9_lot_split_eligible = sb9_eligible and lot_area >= 2400  # Min lot size for split
        
        return IncentiveOpportunities(
            toc_tier=toc_tier,
            toc_distance_description=toc_description,
            state_density_bonus=zone.startswith('R') and zone not in ['R1', 'RS'],
            ab2097_eligible=True,  # Would check transit proximity
            opportunity_zone=False,  # Would check OZ designation
            adaptive_reuse=False,   # Would check ARIA designation
            ed1_eligible=zone.startswith('R'),
            sb9_eligible=sb9_eligible,
            sb9_lot_split_eligible=sb9_lot_split_eligible
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
            feasibility=f"{feasibility} - {feasibility_reason}"
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
                feasibility=toc_feasibility
            ))
        
        # Scenario 3: State Density Bonus
        if incentives.state_density_bonus:
            # 35% max bonus for very low income
            sdb_units = base.baseline_units * 1.35
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
                description=f"UNLOCK: Available to all multi-family zones ({base.zone}). Requires 11% Very Low Income affordable units to achieve 35% bonus.",
                total_units=sdb_total,
                net_new_units=sdb_total - existing.units,
                affordability_required="11% Very Low Income units (35% bonus) or sliding scale",
                approval_path="By-right with density bonus application (Gov Code 65915)",
                key_benefits=["35% density bonus", "Up to 3 concessions (parking, setback, height)", "Reduced parking possible", "Cannot be denied if compliant"],
                constraints=["Affordability requirement"] + (["RSO replacement required"] if existing.is_rso else []),
                feasibility=sdb_feasibility
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
                    feasibility=split_feasibility
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
                feasibility=duplex_feasibility
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
                feasibility=ed1_feasibility
            ))
        
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