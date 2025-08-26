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

## 🏗️ Architecture

### **Data Pipeline**
1. **Address Input** → Geocoding → APN identification
2. **LA County GIS** → Property details, lot geometry
3. **Analysis Engine** → Zoning calculations, scenario modeling
4. **Frontend** → Clean presentation with drill-down details

### **Core Components**
- `development_analyzer.py` - Main analysis engine
- `main_development.py` - FastAPI backend  
- Live LA County parcel data integration
- LAMC density factors and regulations
- State incentive program rules

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

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This project was developed with Claude Code. Contributions welcome via issues and pull requests.

---

**Built with**: Python, FastAPI, LA County GIS APIs, Vanilla JS
**Generated with**: [Claude Code](https://claude.ai/code)