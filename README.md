# 🏠 LA Development Potential Analyzer

> **"What can be built here?"** - Comprehensive development analysis for Los Angeles properties

A professional-grade entitlement analysis platform that transforms complex LA zoning regulations into actionable development intelligence.

## ✨ Key Features

### 🎯 **Development Scenarios**
- **By-Right Development**: Baseline zoning analysis
- **TOC (Transit Oriented Communities)**: Tier-based density bonuses
- **State Density Bonus**: Affordable housing incentives
- **ED-1 (100% Affordable)**: Maximum development potential

### 🔓 **Clear Unlock Requirements** 
Each scenario shows exactly what triggers it:
- Proximity requirements (transit stops, specific areas)
- Affordability commitments (% of units, income levels)
- Zoning eligibility (residential zones, density factors)

### 📊 **Feasibility Analysis**
- **High/Medium/Low** ratings with detailed explanations
- RSO replacement unit calculations
- Environmental constraint assessment
- Regulatory pathway guidance

### 🏗️ **Core Zoning Intelligence**
- Complete zone analysis (R4-2, density factors, height limits)
- Baseline unit calculations (lot area ÷ density factor)
- Existing conditions assessment
- Constraint identification

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
**"What Can Be Built Here?"** - Focused development analysis
- Clean scenario comparison
- Clear unlock requirements  
- Feasibility ratings
- Expandable detailed analysis

### 🔬 **Technical Interface**: `comprehensive.html`
Advanced zoning analysis with complete regulatory breakdown

### 📋 **Basic Interface**: `index.html`
Simple property lookup and zoning information

## 📊 Sample Analysis: 2910 Leeward Ave

**Property**: 30-unit apartment building (1924) on 11,135 sq ft lot
**Zone**: R4-2 (High density residential)

**Development Scenarios**:
- **By-Right**: 30 units (existing) - *Medium feasibility*
- **State Density Bonus**: 38 units (+8 net) - *Medium feasibility*  
- **100% Affordable (ED-1)**: 56 units (+26 net) - *Medium feasibility*

**Key Unlock**: Property is over-built (30 units vs 28 baseline), RSO replacement required

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
  "property_summary": "Address • lot size • zoning • existing units",
  "base_zoning": {
    "zone": "R4",
    "height_district": "2", 
    "baseline_units": 27.84,
    "interpretation": "R4 allows ~1 unit per 400 sq ft..."
  },
  "development_scenarios": [
    {
      "name": "TOC Tier 3",
      "description": "UNLOCK: Property within ½ mile of major transit...",
      "total_units": 47,
      "net_new_units": 17,
      "feasibility": "High - Clear path with strong incentives"
    }
  ],
  "bottom_line": "Site is already above base R4 density..."
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

**AB 2097 (Parking Reduction)**:
- Properties within ½ mile of major transit: Parking minimums eliminated
- Currently using proximity logic (would integrate Metro GTFS data)

**State Density Bonus Law (Gov Code 65915)**:
- Available to multi-family zones (R2, R3, R4, R5)
- 35% density bonus for 11% Very Low Income units
- Up to 3 regulatory concessions allowed
- Cannot be denied if application complies

**SB 330 (Housing Crisis Act)**:
- Replacement unit requirements for rent-stabilized properties
- Applied when existing units > baseline zoning allows

**Executive Directive 1 (ED-1)**:
- 100% affordable projects get ministerial approval
- No parking requirements
- Maximum allowable height/FAR
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

- **Phase 2**: Real-time TOC tier calculation, transit integration
- **Phase 3**: Interactive map interface, batch processing
- **Phase 4**: Permitting timeline integration, cost estimation

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