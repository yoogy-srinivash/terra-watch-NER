"""
LandSafe Connect - Station Terrain & Geospatial Grounding Service
Provides grounded topographic, lithological, and geotechnical parameters
for all 32 monitored NER stations across the 8 North Eastern states.
Eliminates hardcoded static defaults in spatial risk inference.
"""

from typing import Dict, Any, Optional
import math

# Grounded terrain characteristics for all 32 NER monitored stations
NER_STATION_TERRAIN: Dict[str, Dict[str, Any]] = {
    # Arunachal Pradesh
    "AR-ITANAGAR": {
        "elevation_m": 440.0,
        "slope_angle_deg": 22.0,
        "aspect_deg": 195.0,
        "plan_curvature": -0.02,
        "profile_curvature": 0.03,
        "soil_depth_m": 2.2,
        "ndvi": 0.58,
        "distance_to_road_m": 35.0,
        "distance_to_fault_m": 1800.0,
        "distance_to_stream_m": 220.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Settlement/Infrastructure"
    },
    "AR-TAWANG": {
        "elevation_m": 3048.0,
        "slope_angle_deg": 42.0,
        "aspect_deg": 175.0,
        "plan_curvature": 0.05,
        "profile_curvature": -0.04,
        "soil_depth_m": 1.4,
        "ndvi": 0.38,
        "distance_to_road_m": 15.0,
        "distance_to_fault_m": 450.0,
        "distance_to_stream_m": 180.0,
        "lithology": "Hard Quartzite",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "AR-PASIGHAT": {
        "elevation_m": 155.0,
        "slope_angle_deg": 14.0,
        "aspect_deg": 140.0,
        "plan_curvature": -0.01,
        "profile_curvature": 0.01,
        "soil_depth_m": 3.0,
        "ndvi": 0.76,
        "distance_to_road_m": 120.0,
        "distance_to_fault_m": 2200.0,
        "distance_to_stream_m": 120.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Dense Mountain Forest"
    },
    "AR-BOMDILA": {
        "elevation_m": 2217.0,
        "slope_angle_deg": 38.0,
        "aspect_deg": 210.0,
        "plan_curvature": 0.04,
        "profile_curvature": -0.03,
        "soil_depth_m": 1.8,
        "ndvi": 0.45,
        "distance_to_road_m": 20.0,
        "distance_to_fault_m": 800.0,
        "distance_to_stream_m": 250.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },

    # Assam
    "AS-GUWAHATI": {
        "elevation_m": 55.0,
        "slope_angle_deg": 16.0,
        "aspect_deg": 160.0,
        "plan_curvature": 0.01,
        "profile_curvature": -0.01,
        "soil_depth_m": 2.8,
        "ndvi": 0.42,
        "distance_to_road_m": 25.0,
        "distance_to_fault_m": 3500.0,
        "distance_to_stream_m": 150.0,
        "lithology": "Granite/Gneiss Complex",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    },
    "AS-SILCHAR": {
        "elevation_m": 25.0,
        "slope_angle_deg": 8.0,
        "aspect_deg": 130.0,
        "plan_curvature": 0.0,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.5,
        "ndvi": 0.48,
        "distance_to_road_m": 80.0,
        "distance_to_fault_m": 4000.0,
        "distance_to_stream_m": 80.0,
        "lithology": "Soft Shale/Mudstone",
        "soil_type": "Silty Loam",
        "land_use": "Settlement/Infrastructure"
    },
    "AS-DIPHU": {
        "elevation_m": 186.0,
        "slope_angle_deg": 22.0,
        "aspect_deg": 170.0,
        "plan_curvature": 0.02,
        "profile_curvature": 0.01,
        "soil_depth_m": 2.4,
        "ndvi": 0.52,
        "distance_to_road_m": 60.0,
        "distance_to_fault_m": 2800.0,
        "distance_to_stream_m": 300.0,
        "lithology": "Granite/Gneiss Complex",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Degraded Forest"
    },
    "AS-GOALPARA": {
        "elevation_m": 35.0,
        "slope_angle_deg": 6.0,
        "aspect_deg": 110.0,
        "plan_curvature": 0.0,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.2,
        "ndvi": 0.50,
        "distance_to_road_m": 90.0,
        "distance_to_fault_m": 4500.0,
        "distance_to_stream_m": 100.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    },

    # Manipur
    "MN-IMPHAL": {
        "elevation_m": 786.0,
        "slope_angle_deg": 12.0,
        "aspect_deg": 150.0,
        "plan_curvature": -0.01,
        "profile_curvature": 0.01,
        "soil_depth_m": 2.9,
        "ndvi": 0.46,
        "distance_to_road_m": 40.0,
        "distance_to_fault_m": 2600.0,
        "distance_to_stream_m": 200.0,
        "lithology": "Soft Shale/Mudstone",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    },
    "MN-CHURACHANDPUR": {
        "elevation_m": 922.0,
        "slope_angle_deg": 26.0,
        "aspect_deg": 190.0,
        "plan_curvature": 0.02,
        "profile_curvature": 0.02,
        "soil_depth_m": 2.2,
        "ndvi": 0.55,
        "distance_to_road_m": 45.0,
        "distance_to_fault_m": 1400.0,
        "distance_to_stream_m": 350.0,
        "lithology": "Soft Shale/Mudstone",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Shifting Cultivation (Jhum)"
    },
    "MN-UKHRUL": {
        "elevation_m": 1660.0,
        "slope_angle_deg": 35.0,
        "aspect_deg": 185.0,
        "plan_curvature": 0.04,
        "profile_curvature": -0.03,
        "soil_depth_m": 1.7,
        "ndvi": 0.59,
        "distance_to_road_m": 25.0,
        "distance_to_fault_m": 750.0,
        "distance_to_stream_m": 280.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "MN-SENAPATI": {
        "elevation_m": 1200.0,
        "slope_angle_deg": 31.0,
        "aspect_deg": 200.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 1.9,
        "ndvi": 0.53,
        "distance_to_road_m": 20.0,
        "distance_to_fault_m": 1100.0,
        "distance_to_stream_m": 190.0,
        "lithology": "Soft Shale/Mudstone",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },

    # Meghalaya
    "ML-SHILLONG": {
        "elevation_m": 1525.0,
        "slope_angle_deg": 32.0,
        "aspect_deg": 190.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 1.9,
        "ndvi": 0.62,
        "distance_to_road_m": 18.0,
        "distance_to_fault_m": 1200.0,
        "distance_to_stream_m": 210.0,
        "lithology": "Hard Quartzite",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Roadside Cut Slope"
    },
    "ML-TURA": {
        "elevation_m": 657.0,
        "slope_angle_deg": 29.0,
        "aspect_deg": 220.0,
        "plan_curvature": 0.03,
        "profile_curvature": 0.01,
        "soil_depth_m": 2.1,
        "ndvi": 0.65,
        "distance_to_road_m": 35.0,
        "distance_to_fault_m": 1600.0,
        "distance_to_stream_m": 180.0,
        "lithology": "Granite/Gneiss Complex",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Degraded Forest"
    },
    "ML-JOWAI": {
        "elevation_m": 1380.0,
        "slope_angle_deg": 27.0,
        "aspect_deg": 175.0,
        "plan_curvature": 0.02,
        "profile_curvature": -0.01,
        "soil_depth_m": 2.0,
        "ndvi": 0.58,
        "distance_to_road_m": 25.0,
        "distance_to_fault_m": 1400.0,
        "distance_to_stream_m": 240.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Roadside Cut Slope"
    },
    "ML-NONGPOH": {
        "elevation_m": 485.0,
        "slope_angle_deg": 25.0,
        "aspect_deg": 350.0,
        "plan_curvature": 0.01,
        "profile_curvature": 0.02,
        "soil_depth_m": 2.3,
        "ndvi": 0.60,
        "distance_to_road_m": 22.0,
        "distance_to_fault_m": 2100.0,
        "distance_to_stream_m": 260.0,
        "lithology": "Granite/Gneiss Complex",
        "soil_type": "Residual Clay",
        "land_use": "Roadside Cut Slope"
    },

    # Mizoram
    "MZ-AIZAWL": {
        "elevation_m": 1132.0,
        "slope_angle_deg": 37.0,
        "aspect_deg": 195.0,
        "plan_curvature": 0.05,
        "profile_curvature": -0.04,
        "soil_depth_m": 1.6,
        "ndvi": 0.44,
        "distance_to_road_m": 12.0,
        "distance_to_fault_m": 600.0,
        "distance_to_stream_m": 220.0,
        "lithology": "Soft Shale/Mudstone",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "MZ-LUNGLEI": {
        "elevation_m": 1222.0,
        "slope_angle_deg": 36.0,
        "aspect_deg": 180.0,
        "plan_curvature": 0.04,
        "profile_curvature": -0.03,
        "soil_depth_m": 1.7,
        "ndvi": 0.50,
        "distance_to_road_m": 18.0,
        "distance_to_fault_m": 850.0,
        "distance_to_stream_m": 300.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "MZ-LAWNGTLAI": {
        "elevation_m": 810.0,
        "slope_angle_deg": 34.0,
        "aspect_deg": 215.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 1.8,
        "ndvi": 0.55,
        "distance_to_road_m": 30.0,
        "distance_to_fault_m": 950.0,
        "distance_to_stream_m": 270.0,
        "lithology": "Soft Shale/Mudstone",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Shifting Cultivation (Jhum)"
    },
    "MZ-KOLASIB": {
        "elevation_m": 620.0,
        "slope_angle_deg": 31.0,
        "aspect_deg": 170.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 2.0,
        "ndvi": 0.52,
        "distance_to_road_m": 20.0,
        "distance_to_fault_m": 1100.0,
        "distance_to_stream_m": 240.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Roadside Cut Slope"
    },

    # Nagaland
    "NL-KOHIMA": {
        "elevation_m": 1444.0,
        "slope_angle_deg": 36.0,
        "aspect_deg": 185.0,
        "plan_curvature": 0.04,
        "profile_curvature": -0.03,
        "soil_depth_m": 1.8,
        "ndvi": 0.48,
        "distance_to_road_m": 15.0,
        "distance_to_fault_m": 500.0,
        "distance_to_stream_m": 200.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "NL-DIMAPUR": {
        "elevation_m": 145.0,
        "slope_angle_deg": 8.0,
        "aspect_deg": 120.0,
        "plan_curvature": 0.0,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.1,
        "ndvi": 0.44,
        "distance_to_road_m": 50.0,
        "distance_to_fault_m": 3200.0,
        "distance_to_stream_m": 160.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    },
    "NL-MOKOKCHUNG": {
        "elevation_m": 1325.0,
        "slope_angle_deg": 33.0,
        "aspect_deg": 190.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 1.9,
        "ndvi": 0.54,
        "distance_to_road_m": 22.0,
        "distance_to_fault_m": 900.0,
        "distance_to_stream_m": 280.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "NL-MON": {
        "elevation_m": 897.0,
        "slope_angle_deg": 32.0,
        "aspect_deg": 205.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 2.0,
        "ndvi": 0.58,
        "distance_to_road_m": 28.0,
        "distance_to_fault_m": 1200.0,
        "distance_to_stream_m": 310.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Red Sandy-Clay Loam",
        "land_use": "Shifting Cultivation (Jhum)"
    },

    # Sikkim
    "SK-GANGTOK": {
        "elevation_m": 1650.0,
        "slope_angle_deg": 39.0,
        "aspect_deg": 180.0,
        "plan_curvature": 0.05,
        "profile_curvature": -0.04,
        "soil_depth_m": 1.5,
        "ndvi": 0.46,
        "distance_to_road_m": 14.0,
        "distance_to_fault_m": 400.0,
        "distance_to_stream_m": 150.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },
    "SK-NAMCHI": {
        "elevation_m": 1315.0,
        "slope_angle_deg": 33.0,
        "aspect_deg": 165.0,
        "plan_curvature": 0.03,
        "profile_curvature": -0.02,
        "soil_depth_m": 1.8,
        "ndvi": 0.68,
        "distance_to_road_m": 35.0,
        "distance_to_fault_m": 800.0,
        "distance_to_stream_m": 230.0,
        "lithology": "Hard Quartzite",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Dense Mountain Forest"
    },
    "SK-GEYZING": {
        "elevation_m": 1420.0,
        "slope_angle_deg": 35.0,
        "aspect_deg": 195.0,
        "plan_curvature": 0.04,
        "profile_curvature": -0.03,
        "soil_depth_m": 1.7,
        "ndvi": 0.61,
        "distance_to_road_m": 30.0,
        "distance_to_fault_m": 700.0,
        "distance_to_stream_m": 210.0,
        "lithology": "Granite/Gneiss Complex",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Degraded Forest"
    },
    "SK-MANGAN": {
        "elevation_m": 1820.0,
        "slope_angle_deg": 44.0,
        "aspect_deg": 170.0,
        "plan_curvature": 0.06,
        "profile_curvature": -0.05,
        "soil_depth_m": 1.3,
        "ndvi": 0.42,
        "distance_to_road_m": 10.0,
        "distance_to_fault_m": 300.0,
        "distance_to_stream_m": 110.0,
        "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus",
        "land_use": "Roadside Cut Slope"
    },

    # Tripura
    "TR-AGARTALA": {
        "elevation_m": 15.0,
        "slope_angle_deg": 5.0,
        "aspect_deg": 90.0,
        "plan_curvature": 0.0,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.4,
        "ndvi": 0.45,
        "distance_to_road_m": 60.0,
        "distance_to_fault_m": 4800.0,
        "distance_to_stream_m": 90.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    },
    "TR-DHARMANAGAR": {
        "elevation_m": 21.0,
        "slope_angle_deg": 7.0,
        "aspect_deg": 105.0,
        "plan_curvature": 0.0,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.2,
        "ndvi": 0.49,
        "distance_to_road_m": 75.0,
        "distance_to_fault_m": 3900.0,
        "distance_to_stream_m": 140.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Silty Loam",
        "land_use": "Settlement/Infrastructure"
    },
    "TR-KAILASHAHAR": {
        "elevation_m": 28.0,
        "slope_angle_deg": 9.0,
        "aspect_deg": 115.0,
        "plan_curvature": 0.01,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.0,
        "ndvi": 0.52,
        "distance_to_road_m": 70.0,
        "distance_to_fault_m": 3700.0,
        "distance_to_stream_m": 130.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    },
    "TR-DHAKSHINTRIPURA": {
        "elevation_m": 23.0,
        "slope_angle_deg": 6.0,
        "aspect_deg": 100.0,
        "plan_curvature": 0.0,
        "profile_curvature": 0.0,
        "soil_depth_m": 3.3,
        "ndvi": 0.48,
        "distance_to_road_m": 85.0,
        "distance_to_fault_m": 4200.0,
        "distance_to_stream_m": 110.0,
        "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Residual Clay",
        "land_use": "Settlement/Infrastructure"
    }
}

# State-level default terrain fallback if coordinate lookup is outside stations
STATE_TERRAIN_FALLBACKS: Dict[str, Dict[str, Any]] = {
    "Arunachal Pradesh": {
        "elevation_m": 1800.0, "slope_angle_deg": 35.0, "aspect_deg": 180.0,
        "plan_curvature": 0.02, "profile_curvature": -0.02, "soil_depth_m": 1.8,
        "ndvi": 0.60, "distance_to_road_m": 40.0, "distance_to_fault_m": 1200.0,
        "distance_to_stream_m": 200.0, "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus", "land_use": "Roadside Cut Slope"
    },
    "Assam": {
        "elevation_m": 120.0, "slope_angle_deg": 14.0, "aspect_deg": 150.0,
        "plan_curvature": 0.0, "profile_curvature": 0.0, "soil_depth_m": 3.0,
        "ndvi": 0.48, "distance_to_road_m": 50.0, "distance_to_fault_m": 3500.0,
        "distance_to_stream_m": 150.0, "lithology": "Granite/Gneiss Complex",
        "soil_type": "Residual Clay", "land_use": "Settlement/Infrastructure"
    },
    "Manipur": {
        "elevation_m": 1100.0, "slope_angle_deg": 28.0, "aspect_deg": 180.0,
        "plan_curvature": 0.02, "profile_curvature": -0.01, "soil_depth_m": 2.1,
        "ndvi": 0.54, "distance_to_road_m": 35.0, "distance_to_fault_m": 1500.0,
        "distance_to_stream_m": 250.0, "lithology": "Soft Shale/Mudstone",
        "soil_type": "Weathered Debris/Talus", "land_use": "Roadside Cut Slope"
    },
    "Meghalaya": {
        "elevation_m": 1300.0, "slope_angle_deg": 30.0, "aspect_deg": 190.0,
        "plan_curvature": 0.02, "profile_curvature": -0.02, "soil_depth_m": 2.0,
        "ndvi": 0.62, "distance_to_road_m": 25.0, "distance_to_fault_m": 1400.0,
        "distance_to_stream_m": 200.0, "lithology": "Hard Quartzite",
        "soil_type": "Red Sandy-Clay Loam", "land_use": "Roadside Cut Slope"
    },
    "Mizoram": {
        "elevation_m": 1050.0, "slope_angle_deg": 35.0, "aspect_deg": 190.0,
        "plan_curvature": 0.04, "profile_curvature": -0.03, "soil_depth_m": 1.7,
        "ndvi": 0.50, "distance_to_road_m": 20.0, "distance_to_fault_m": 850.0,
        "distance_to_stream_m": 250.0, "lithology": "Soft Shale/Mudstone",
        "soil_type": "Weathered Debris/Talus", "land_use": "Roadside Cut Slope"
    },
    "Nagaland": {
        "elevation_m": 1250.0, "slope_angle_deg": 33.0, "aspect_deg": 185.0,
        "plan_curvature": 0.03, "profile_curvature": -0.02, "soil_depth_m": 1.9,
        "ndvi": 0.52, "distance_to_road_m": 25.0, "distance_to_fault_m": 900.0,
        "distance_to_stream_m": 240.0, "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus", "land_use": "Roadside Cut Slope"
    },
    "Sikkim": {
        "elevation_m": 1550.0, "slope_angle_deg": 38.0, "aspect_deg": 180.0,
        "plan_curvature": 0.04, "profile_curvature": -0.03, "soil_depth_m": 1.6,
        "ndvi": 0.58, "distance_to_road_m": 20.0, "distance_to_fault_m": 550.0,
        "distance_to_stream_m": 180.0, "lithology": "Weathered Phyllite/Schist",
        "soil_type": "Weathered Debris/Talus", "land_use": "Roadside Cut Slope"
    },
    "Tripura": {
        "elevation_m": 35.0, "slope_angle_deg": 7.0, "aspect_deg": 100.0,
        "plan_curvature": 0.0, "profile_curvature": 0.0, "soil_depth_m": 3.2,
        "ndvi": 0.48, "distance_to_road_m": 70.0, "distance_to_fault_m": 4200.0,
        "distance_to_stream_m": 120.0, "lithology": "Sandstone with Silt Interbeds",
        "soil_type": "Residual Clay", "land_use": "Settlement/Infrastructure"
    }
}

# Mapping of location names/cities to station IDs
LOCATION_NAME_TO_ID = {
    "itanagar": "AR-ITANAGAR", "tawang": "AR-TAWANG", "pasighat": "AR-PASIGHAT", "bomdila": "AR-BOMDILA",
    "guwahati": "AS-GUWAHATI", "silchar": "AS-SILCHAR", "diphu": "AS-DIPHU", "goalpara": "AS-GOALPARA",
    "imphal": "MN-IMPHAL", "churachandpur": "MN-CHURACHANDPUR", "ukhrul": "MN-UKHRUL", "senapati": "MN-SENAPATI",
    "shillong": "ML-SHILLONG", "tura": "ML-TURA", "jowai": "ML-JOWAI", "nongpoh": "ML-NONGPOH",
    "aizawl": "MZ-AIZAWL", "lunglei": "MZ-LUNGLEI", "lawngtlai": "MZ-LAWNGTLAI", "kolasib": "MZ-KOLASIB",
    "kohima": "NL-KOHIMA", "dimapur": "NL-DIMAPUR", "mokokchung": "NL-MOKOKCHUNG", "mon": "NL-MON",
    "gangtok": "SK-GANGTOK", "namchi": "SK-NAMCHI", "geysing": "SK-GEYZING", "gyalshing": "SK-GEYZING", "mangan": "SK-MANGAN",
    "agartala": "TR-AGARTALA", "dharmanagar": "TR-DHARMANAGAR", "kailashahar": "TR-KAILASHAHAR", "belonia": "TR-DHAKSHINTRIPURA"
}

def get_station_terrain(
    location_id: Optional[str] = None,
    name: Optional[str] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Resolve grounded terrain characteristics for a station or spatial point.
    Attempts resolution by ID, name, nearest coordinate, or regional state fallback.
    """
    # 1. Exact station ID match
    if location_id and location_id in NER_STATION_TERRAIN:
        return dict(NER_STATION_TERRAIN[location_id])

    # 2. Match by location/city name
    if name:
        clean_name = name.lower().split(",")[0].strip()
        matched_id = LOCATION_NAME_TO_ID.get(clean_name)
        if matched_id and matched_id in NER_STATION_TERRAIN:
            return dict(NER_STATION_TERRAIN[matched_id])

    # 3. Coordinate proximity matching (nearest station in NER within 1.5 degrees)
    if latitude is not None and longitude is not None:
        best_dist = float("inf")
        best_id = None
        # Approximate coordinate mapping for known station centers
        station_coords = {
            "AR-ITANAGAR": (27.0844, 93.6053), "AR-TAWANG": (27.5861, 91.8594),
            "AR-PASIGHAT": (28.0669, 95.3268), "AR-BOMDILA": (27.2647, 92.4247),
            "AS-GUWAHATI": (26.1445, 91.7362), "AS-SILCHAR": (24.8333, 92.7789),
            "AS-DIPHU": (25.843, 93.431), "AS-GOALPARA": (26.1667, 90.6167),
            "MN-IMPHAL": (24.817, 93.9368), "MN-CHURACHANDPUR": (24.3333, 93.6833),
            "MN-UKHRUL": (25.0967, 94.3614), "MN-SENAPATI": (25.267, 94.02),
            "ML-SHILLONG": (25.5788, 91.8933), "ML-TURA": (25.5144, 90.2032),
            "ML-JOWAI": (25.45, 92.2), "ML-NONGPOH": (25.9, 91.8833),
            "MZ-AIZAWL": (23.7271, 92.7176), "MZ-LUNGLEI": (22.887, 92.733),
            "MZ-LAWNGTLAI": (22.53, 92.9), "MZ-KOLASIB": (24.224, 92.678),
            "NL-KOHIMA": (25.6751, 94.1086), "NL-DIMAPUR": (25.9044, 93.7266),
            "NL-MOKOKCHUNG": (26.322, 94.518), "NL-MON": (26.7167, 95.0333),
            "SK-GANGTOK": (27.3389, 88.6065), "SK-NAMCHI": (27.1667, 88.35),
            "SK-GEYZING": (27.2833, 88.2667), "SK-MANGAN": (27.5, 88.5333),
            "TR-AGARTALA": (23.8315, 91.2868), "TR-DHARMANAGAR": (24.3667, 92.1667),
            "TR-KAILASHAHAR": (24.3333, 92.0), "TR-DHAKSHINTRIPURA": (23.25, 91.45)
        }
        for sid, (s_lat, s_lon) in station_coords.items():
            dist = math.hypot(latitude - s_lat, longitude - s_lon)
            if dist < best_dist:
                best_dist = dist
                best_id = sid

        if best_id and best_dist <= 0.85:  # within ~90 km of a monitored station
            return dict(NER_STATION_TERRAIN[best_id])

    # 4. Regional State Fallback
    if state and state in STATE_TERRAIN_FALLBACKS:
        return dict(STATE_TERRAIN_FALLBACKS[state])

    # 5. General NER mountain baseline
    return dict(STATE_TERRAIN_FALLBACKS["Assam"])
