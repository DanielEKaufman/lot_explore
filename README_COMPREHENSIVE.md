# LA Comprehensive Zoning Analysis Platform

A professional-grade entitlement analysis tool for Los Angeles properties that provides comprehensive zoning, incentive, and development potential analysis.

## 🏗️ Features

### **Core Zoning Envelope**
- **Zone Classification** (e.g., "R4") 
- **Height District** (e.g., "2")
- **Complete Zone Code** (e.g., "R4-2")

### **Lot & Units Analysis** 
- **Lot Area** (from accurate parcel polygons)
- **Baseline Units** (lot area ÷ density factor)
- **Existing Units** (from assessor records)
- **Replacement Units** (accounts for RSO/SB 330 requirements)

### **Overlay Detection**
- Specific Plan / CPIO identification
- Q/D/T conditions and flags
- HPOZ (Historic Preservation Overlay Zone)
- Historic Resource designation

### **Incentive Program Eligibility**
- **TOC (Transit Oriented Communities)**
  - Eligibility assessment
  - Tier classification (1-4)
- **State Density Bonus**
  - Automatic eligibility for qualifying zones
  - Bonus percentage calculations
- **ED-1 (Executive Directive 1)**
  - 100% affordable housing pathway
  - Ministerial approval eligibility
- **SB-9 (California Duplex Law)**
  - R1 zone eligibility
  - Lot split and duplex potential

### **Transit & Parking Analysis**
- Distance to Major Transit Stops
- **AB 2097** parking reduction qualification
- Baseline parking requirements by zone

### **Hazards & Constraints**
- Alquist-Priolo Fault Zones
- Liquefaction risk areas
- Very High Fire Hazard Severity Zones
- Methane buffer zones
- Landslide and flood zones

### **Derived Development Envelopes**
- **Baseline Scenario**: By-right development potential
- **TOC Scenario**: Transit-oriented bonus calculations
- **State Density Bonus**: Affordable housing incentives
- **ED-1 Scenario**: 100% affordable development

### **Regulatory Citations**
- LAMC section references
- State law citations (SB 330, SB 9, AB 2097)
- Planning guideline sources
- Data layer attributions

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main_comprehensive.py
```

### Frontend Access
Open `frontend/comprehensive.html` in your browser.

## 📊 API Endpoints

### POST `/lookup`
Comprehensive analysis by address or APN
```json
{
  "address": "2910 Leeward Ave Los Angeles, CA 90005"
}
```

### GET `/apn/{apn}`
Direct lookup by Assessor Parcel Number
```
GET /apn/5077019011
```

### Sample Response Structure
```json
{
  "apn": "5077-019-011",
  "address": "2910 LEEWARD AVE",
  "core_zoning_envelope": {
    "zone": "R4",
    "height_district": "2", 
    "zone_complete": "R4-2"
  },
  "lot_units": {
    "lot_area_sqft": 11135.09,
    "baseline_units": 27.84,
    "existing_units": 30,
    "replacement_units": 27.84
  },
  "incentive_eligibility": {
    "toc": {"eligible": false},
    "state_density_bonus": {"eligible": true, "bonus_pct": 35},
    "ed1": {"eligible": true, "ministerial": true},
    "sb9": {"eligible": false}
  },
  "derived_envelopes": {
    "baseline": {
      "units": 27.84,
      "far": 1.0,
      "height_ft": 75,
      "parking": 27.84
    }
  },
  "citations": [
    {
      "code": "LAMC 12.03-R4",
      "description": "Density factor for R4 zone",
      "value": 400,
      "source": "LA Municipal Code"
    }
  ]
}
```

## 🎯 Use Cases

### **Developers & Investors**
- Pre-acquisition feasibility analysis
- Development program optimization
- Incentive program evaluation

### **Architects & Planners** 
- Massing studies and program validation
- Code compliance verification
- Entitlement strategy development

### **Real Estate Professionals**
- Investment underwriting support
- Market analysis enhancement
- Client advisory services

### **Policy Researchers**
- Housing production analysis
- Zoning impact assessment
- Incentive program effectiveness

## 🏗️ Architecture

### **Data Sources**
- **LA County GIS**: Parcel geometry, assessor data
- **ZIMAS**: Official zoning classifications
- **Built-in Engine**: LAMC calculations and interpretations

### **Analysis Engine**
- Modular zoning rule implementation
- Extensible incentive program logic  
- Comprehensive citation tracking
- Scenario modeling framework

### **Frontend**
- Responsive design for desktop/mobile
- Interactive scenario comparison
- Regulatory citation display
- Raw data inspection

## 🔮 Roadmap

### **Phase 2 Enhancements**
- Real-time TOC tier calculation via Metro GTFS
- Specific Plan overlay integration
- Advanced FAR and height modeling

### **Phase 3 Expansions**
- Interactive map interface
- Batch processing for portfolios
- CSV/PDF report generation

### **Phase 4 Ecosystem**
- Permitting timeline integration
- Cost estimation modules
- Lender-ready output formats

## 📈 Technical Details

### **Zoning Calculations**
- Density factors by zone (LAMC 12.03)
- Height districts and limitations
- Parking requirements (LAMC 12.21)
- Open space standards

### **Incentive Programs**
- TOC bonus tiers and requirements
- State Density Bonus calculations
- ED-1 ministerial pathways
- SB-9 duplex and lot split rules

### **Data Accuracy**
- Live LA County parcel data
- Current assessor valuations  
- Real-time geometric calculations
- Regulatory updates via citations

## 🎨 Example Analyses

### **Multi-Family Property**
- **Address**: 2910 Leeward Ave (30-unit apartment, 1924)
- **Zone**: R4-2 
- **Baseline**: 27.8 units (11,135 sq ft ÷ 400)
- **Existing**: 30 units (no replacement required)
- **Incentives**: State Density Bonus eligible (up to 35% bonus)

### **Single-Family Property** 
- **Zone**: R1-1
- **SB-9 Eligible**: Duplex conversion possible
- **Lot Split**: If >2,400 sq ft
- **Ministerial**: Streamlined approval process

This platform transforms complex LA zoning regulations into actionable development intelligence, supporting informed decision-making across the real estate and development ecosystem.