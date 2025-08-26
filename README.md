# 🏠 LA Development Potential Analyzer

> **"What can be built here?"** - Comprehensive development analysis for Los Angeles properties

A professional-grade entitlement analysis platform that transforms complex LA zoning regulations into actionable development intelligence with Netflix-style recommendations and comprehensive regulatory audit.

## ✨ Key Features

### 🏆 **Netflix-Style Good/Better/Best Recommendations**
- **Smart Ranking**: Scenarios prioritized by units + revenue potential, not arbitrary order
- **Practical Middle Options**: State Density Bonus (10 units, 15% VLI) as the sweet spot between baseline and maximum
- **Revenue Integration**: GPR, NOI, and property value calculations for each scenario
- **Jurisdiction-Aware**: Builder's Remedy only shows when housing element non-compliant

### 📋 **Complete Rules Audit**
Comprehensive table showing **every regulation** that applies to the property:
- **Rule**: Regulation name and legal citation
- **Status**: Eligible/Not Eligible/Applies
- **Effect**: Technical impact (density bonus, height limits, etc.)
- **What It Enables**: Human-readable benefits:
  - 🏃 **Faster**: Ministerial vs. discretionary approval 
  - 🏢 **Denser**: Percentage unit increases
  - 📏 **Taller/FAR**: Bulk and massing allowances
  - 🚗 **Less Parking**: Reduction or elimination requirements

### 🎯 **Development Scenarios**
- **By-Right Development**: Baseline zoning analysis
- **State Density Bonus**: 15% VLI units → +50% density + concessions
- **AB-1287 Enhanced**: Up to 100% density bonus for mixed-income projects
- **TOC (Transit Oriented Communities)**: Tier-based density bonuses (50%-80%)
- **ED-1 (100% Affordable)**: Maximum development with ministerial approval
- **SB-35 Streamlined**: Fast-track for affordable housing
- **SB-684 Small Site**: 60-day ministerial approval for small projects
- **SB-9 (Duplex/Lot Split)**: R1 zone duplex conversion and lot splitting

### 🔓 **Clear Unlock Requirements** 
Each scenario shows exactly what triggers it:
- Proximity requirements (transit stops, specific areas)
- Affordability commitments (% of units, income levels)
- Zoning eligibility (residential zones, density factors)
- Jurisdiction compliance status (housing element certification)

### 🧮 **Detailed Unit Calculations**
- Step-by-step math for each scenario showing how units are calculated
- Massing constraints and FAR limitations factored in
- RSO replacement unit requirements
- Legal citations for each calculation method

### 🏗️ **Core Zoning Intelligence**
- Complete zone analysis (R4-2, density factors, height limits)
- Baseline unit calculations (lot area ÷ density factor)
- Existing conditions assessment
- Environmental and regulatory constraint identification

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main_development.py
```

### Frontend Access
Open `frontend/development.html` in your browser for the main interface.

## 💻 Interface Options

### 🎯 **Primary Interface**: `development.html`
**"What Can Be Built Here?"** - Netflix-style development analysis
- **Good/Better/Best Cards**: Top 3 scenarios with unit counts and revenue potential
- **Complete Rules Audit**: Every applicable regulation with "What It Enables" breakdown
- **Detailed Math**: Expandable unit calculations with step-by-step justification
- **Smart Ranking**: Scenarios prioritized by practical value, not arbitrary order

### 🔬 **Technical Interface**: `comprehensive.html`
Advanced zoning analysis with complete regulatory breakdown

### 📋 **Basic Interface**: `index.html`
Simple property lookup and zoning information

## 📊 Sample Analysis: 603 N Windsor Blvd

**Property**: 2-unit building (1923) on 5,085 sq ft lot in Wilshire  
**Zone**: R3-1 (Medium density residential)

**Good/Better/Best Recommendations**:
- **🥇 BEST**: AB-1287 Enhanced (13 units) - Mixed affordability for maximum density
- **🥈 BETTER**: State Density Bonus (10 units) - 15% VLI, practical middle choice  
- **🥉 GOOD**: SB-35 Streamlined (8 units) - 20% affordable, fast ministerial approval

**Key Insights**:
- Property under-built: 2 existing vs 6 baseline units allowed
- No RSO replacement requirements (pre-1978 but under RSO threshold)
- Builder's Remedy not available (LA housing element certified through 2029)
- Revenue potential: $173k-$347k GPR depending on scenario

**Complete Rules Audit**: 12 regulations analyzed, 8 eligible programs identified

## 🛠️ API Endpoints

### `POST /analyze`
Comprehensive development analysis
```json
{
  "address": "2910 Leeward Ave Los Angeles, CA 90005"
}
```

### `GET /apn/{apn}`
Direct lookup by Assessor Parcel Number
```
GET /apn/5077019011
```

### Response Structure
```json
{
  "property_summary": "APN 5523-024-013 • 2 addresses • 5,085 sq ft lot • R3-1 zoning • 2 existing units (1923)",
  "base_zoning": {
    "zone": "R3",
    "height_district": "1", 
    "complete_zone": "R3-1",
    "density_factor": 800,
    "baseline_units": 6.3556389375,
    "height_limit_ft": 45,
    "far_limit": 1.5,
    "interpretation": "R3 allows ~1 unit per 800 sq ft of lot area."
  },
  "development_scenarios": [
    {
      "name": "AB-1287 Enhanced Density Bonus",
      "description": "UNLOCK: Up to 100% density bonus for moderate and very low income units.",
      "total_units": 12.711277875,
      "net_new_units": 10.711277875,
      "affordability_required": "Mix of moderate and very low income units for maximum bonus",
      "approval_path": "By-right with enhanced density bonus application",
      "recommendation_score": 82.0,
      "recommendation_reason": "Recommended because of excellent unit yield, high revenue potential",
      "gpr": 347017,
      "noi": 214283,
      "property_value": 3896064,
      "unit_calculation_justification": "AB-1287 enhanced density bonus allows up to 100% density bonus...",
      "legal_citations": ["Gov Code 65915(f)(4) (AB-1287 enhanced bonus)", "..."],
      "key_benefits": ["Up to 100% density bonus", "Missing middle housing focus", "..."],
      "constraints": ["Enhanced affordability requirement"],
      "feasibility": "High - Enhanced version of proven density bonus law"
    }
  ],
  "incentive_opportunities": {
    "state_density_bonus": true,
    "sb330_eligible": false,
    "sb330_description": "Builder's Remedy available if housing element not certified by HCD",
    "..."
  },
  "bottom_line": "Site is under-built relative to base R3 density (2 existing vs. 6 allowed)..."
}
```

## 🏗️ Architecture & Data Sources

### **Data Pipeline**
1. **Address Input** → Geocoding via LA County services → APN identification
2. **LA County GIS API** → Property details, lot geometry, assessor data
3. **Analysis Engine** → Apply deterministic zoning rules and calculations
4. **Frontend** → Clean presentation with expandable technical details

### **Live Data Sources**
- **LA County Parcel Service**: `https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query`
  - Property boundaries, lot area calculations
  - Existing building details (units, square footage, year built)
  - Assessor data (land value, improvement value)
  - Use codes and property classifications

- **Address Geocoding**: LA County GeocodeServer for address-to-APN conversion
- **Environmental Hazards**: Methane zones, fault zones, liquefaction risk from County GIS layers

### **Regulatory Framework Applied**

#### **Los Angeles Municipal Code (LAMC)**
Deterministic rules programmed into the analysis engine:

**Density Factors** (Units per lot area):
- R1: 5,000 sq ft per unit
- R2: 800 sq ft per unit  
- R3: 800 sq ft per unit
- R4: 400 sq ft per unit
- R5: 200 sq ft per unit

**Height Districts**:
- Height District 1: 45 feet maximum
- Height District 2: 75 feet maximum  
- Height District 3: 150 feet maximum
- Height District 4: 275 feet maximum

**Parking Requirements** (LAMC 12.21):
- R1: 2.0 spaces per unit
- R2-R5: 1.0 space per unit base requirement

#### **State Regulations**

**State Density Bonus Law (Gov Code 65915 + AB 2345)**:
- Available to multi-family zones (R2, R3, R4, R5)  
- Up to 50% density bonus (increased from 35% in 2020)
- 15% Very Low Income units → 50% density bonus
- Up to 3 regulatory concessions allowed
- Cannot be denied if application complies

**AB-1287 Enhanced Density Bonus**:
- Enhanced version allowing up to 100% density bonus
- Focus on moderate and very low income housing ("missing middle")
- Additional concessions available beyond standard density bonus
- By-right approval process

**SB-35 Streamlined Ministerial Approval**:
- Available when jurisdiction hasn't met RHNA goals
- 20% affordable housing requirement
- Ministerial approval (no CEQA review)
- Cannot be denied if compliant with objective standards

**SB-684 Small Site Housing**:
- Ministerial approval for up to 10 units on small sites
- 60-day maximum approval timeline
- CEQA-exempt process
- No affordability requirement
- Available on urban lots under 5 acres

**SB-330 Housing Crisis Act / Builder's Remedy**:
- Available ONLY when jurisdiction's housing element not HCD-certified
- Los Angeles currently compliant (certified through 2029)
- Would override local zoning if activated
- Replacement unit requirements for rent-stabilized properties

**SB-9 (Housing Opportunity and More Efficiency Act)**:
- Duplex conversion allowed on single-family lots (R1 zones)
- Lot splits creating two parcels from one (minimum 1,200 sq ft each)
- Up to 4 total units possible (2 units per split lot)
- Ministerial approval (no discretionary review)
- Owner-occupancy required for 3 years

**AB-2097 (Parking Reduction)**:
- Properties within ½ mile of major transit: Parking minimums eliminated
- Currently using proximity logic (would integrate Metro GTFS data)

**Executive Directive 1 (ED-1)**:
- 100% affordable projects get ministerial approval
- No parking requirements
- Maximum allowable height/FAR (up to +80% density)
- Applied to all residential zones

#### **Local Regulations**

**Rent Stabilization Ordinance (RSO)**:
- Multi-family properties with 2+ units built before 1978
- Requires 1:1 replacement of existing rent-stabilized units
- Detected via property age and unit count

**Transit Oriented Communities (TOC)**:
- Density bonuses based on tier (1: 50%, 2: 60%, 3: 70%, 4: 80%)
- Affordability requirements by tier (8-11% VLI)
- Parking reductions (0.5 spaces/unit or eliminated)
- *Note: Currently using sample data - production would integrate Metro transit stop locations*

## 🎯 Use Cases

### **Developers & Investors**
- Pre-acquisition feasibility analysis
- Development program optimization
- Unit yield comparisons

### **Architects & Planners**
- Massing studies and program validation
- Entitlement strategy development
- Code compliance verification

### **Real Estate Professionals**  
- Investment underwriting support
- Market analysis enhancement
- Client advisory services

## 🔮 Roadmap

- **Current**: Netflix-style UX with Good/Better/Best ranking system ✅
- **Phase 2**: Real-time TOC tier calculation via Metro GTFS integration
- **Phase 3**: Interactive map interface with batch property analysis
- **Phase 4**: Permitting timeline integration, construction cost estimation
- **Phase 5**: Pro-forma modeling with financing assumptions

## ⚠️ Data Accuracy & Limitations

### **Data Sources Accuracy**
- **Property Data**: Live from LA County GIS (updated regularly)
- **Zoning Classifications**: Inferred from use codes when ZIMAS unavailable
- **Environmental Hazards**: From County GIS hazard layers
- **TOC Tiers**: Currently sample data - production needs Metro GTFS integration

### **Regulatory Interpretation**
- **LAMC Rules**: Programmed based on published Municipal Code sections
- **State Laws**: Based on current statute language and standard interpretations
- **Feasibility Ratings**: Algorithmic assessment based on constraint analysis

### **Important Disclaimers**
- This tool provides preliminary analysis for informational purposes
- **Not a substitute for professional consultation** with planning experts
- Zoning regulations change - verify current rules with LA City Planning
- Site-specific conditions may affect actual development potential
- Environmental studies and community input can impact feasibility
- **Always consult qualified professionals** before making investment decisions

### **Verification Recommendations**
1. Confirm actual zoning designation with LA City Planning Department
2. Verify TOC tier status with official Metro/City maps
3. Check for recent zoning changes or pending legislation
4. Conduct professional environmental due diligence
5. Engage planning consultants for entitlement strategy

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This project was developed with Claude Code. Contributions welcome via issues and pull requests.

---

**Built with**: Python, FastAPI, LA County GIS APIs, Vanilla JS
**Generated with**: [Claude Code](https://claude.ai/code)