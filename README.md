# LA Zoning Lookup Interface

A bare-bones web interface for querying Los Angeles zoning and parcel data from the ZIMAS ArcGIS REST service.

## Features

- Address or APN lookup
- Geocoding to APN via ZIMAS
- Zoning information display (zone, height district, TOC tier)
- Overlay information (Specific Plans, HPOZ, etc.)
- Rent stabilization status
- Hazard zone flags
- Raw JSON data toggle

## Setup

### Backend

1. Install Python 3.8+
2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Run the server:
```bash
python main.py
```

The API will be available at http://localhost:8000

### Frontend

Simply open `frontend/index.html` in a web browser, or serve it with any static file server.

## Usage

1. Start the backend server
2. Open the frontend in your browser
3. Enter an LA address or APN
4. View the zoning data

## Example Addresses

- 200 N Spring St, Los Angeles (City Hall)
- 1 World Way, Los Angeles (LAX)
- 100 Universal City Plaza, Universal City

## API Endpoints

- `POST /lookup` - Lookup by address
- `GET /apn/{apn}` - Direct APN lookup

## Architecture

- **Backend**: FastAPI proxy to handle ZIMAS queries and CORS
- **Frontend**: Vanilla HTML/CSS/JS for simplicity
- **Data Source**: ZIMAS ArcGIS REST API

## Future Phases

- Phase 2: Entitlement math engine (unit calculations, FAR, parking)
- Phase 3: Bonus/incentive calculations (TOC, Density Bonus, ED-1)
- Phase 4: Multi-source integration (Metro GTFS, County Assessor)
- Phase 5: Developer tools (CSV export, entitlement memos)
- Phase 6: Interactive map and portfolio mode
- Phase 7: Ecosystem integrations