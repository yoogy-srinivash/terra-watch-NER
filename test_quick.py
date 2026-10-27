from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# 1. Test Health
r = client.get('/api/health')
print('Health:', r.status_code, r.json())

# 2. Test Active Alerts
r = client.get('/api/alerts/active')
print('Active Alerts:', r.status_code, len(r.json()), 'alerts returned')

# 3. Test GIS locations
r = client.get('/api/gis/locations')
data = r.json()
print('GIS Locations:', r.status_code, len(data.get('features', [])), 'stations returned')

# 4. Test Admin Dashboard
r = client.get('/api/admin/dashboard')
print('Admin Dashboard:', r.status_code, r.json())

# 5. Test ML Prediction
r = client.post('/api/risk/predict', json={
    'latitude': 25.5788,
    'longitude': 91.8933,
    'state': 'Meghalaya',
    'district': 'East Khasi Hills',
    'rainfall_24h_mm': 110.0,
    'rainfall_72h_mm': 260.0,
    'soil_moisture_pct': 82.5,
    'slope_angle_deg': 34.0,
    'elevation_m': 1496.0,
    'distance_to_road_m': 25.0
})
print('ML Prediction Status:', r.status_code)
pred = r.json()
p = pred.get('prediction', {})
print('Risk Score:', p.get('risk_score'), '| Level:', p.get('risk_level'), '| Factors:', p.get('contributing_factors'))
