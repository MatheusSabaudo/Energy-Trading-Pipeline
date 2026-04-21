import os


def _get_env(name, default):
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _get_int_env(name, default):
    try:
        return int(_get_env(name, default))
    except (TypeError, ValueError):
        return default


# ============================================
# API CONFIGURATION
# ============================================
API_CONFIG = {
    'weatherstack': {
        'base_url': _get_env('WEATHERSTACK_BASE_URL', 'http://api.weatherstack.com'),
        'access_key': _get_env('WEATHERSTACK_ACCESS_KEY', ''),
        'endpoints': {
            'current': '/current',
            'historical': '/historical'
        }
    }
}

# ============================================
# DATABASE CONFIGURATION
# ============================================
POSTGRES_CONFIG = {
    'host': _get_env('POSTGRES_HOST', 'localhost'),
    'port': _get_int_env('POSTGRES_PORT', 5432),
    'database': _get_env('POSTGRES_DB', 'solar_data'),
    'user': _get_env('POSTGRES_USER', 'airflow'),
    'password': _get_env('POSTGRES_PASSWORD', 'airflow')
}

# ============================================
# KAFKA CONFIGURATION
# ============================================
KAFKA_CONFIG = {
    'bootstrap.servers': _get_env('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9093'),
    'topic': _get_env('KAFKA_TOPIC', 'solar-raw')
}

# ============================================
# API DATA TABLE SCHEMA
# ============================================
API_TABLE_SCHEMA = {
    'table_name': 'weather_data',
    'columns': {
        'id': 'SERIAL PRIMARY KEY',
        'city': 'VARCHAR(100)',
        'timestamp': 'TIMESTAMPTZ',
        'temperature': 'DECIMAL(5,2)',
        'humidity': 'INT',
        'wind_speed': 'DECIMAL(5,2)',
        'wind_direction': 'VARCHAR(10)',
        'pressure': 'DECIMAL(7,2)',
        'precipitation': 'DECIMAL(5,2)',
        'cloud_cover': 'INT',
        'uv_index': 'DECIMAL(3,1)',
        'weather_code': 'INT',
        'weather_description': 'VARCHAR(255)',
        'is_day': 'BOOLEAN',
        'observation_time': 'TIMESTAMPTZ',
        'ingestion_timestamp': 'TIMESTAMPTZ DEFAULT NOW()'
    }
}

# ============================================
# IOT TABLE SCHEMA
# ============================================
IOT_TABLE_SCHEMA = {
    'table_name': 'solar_panel_readings',
    'columns': {
        'id': 'SERIAL PRIMARY KEY',
        'event_id': 'UUID UNIQUE',
        'timestamp': 'TIMESTAMPTZ',
        'panel_id': 'VARCHAR(50)',
        'panel_type': 'VARCHAR(50)',
        'panel_power_kw': 'DECIMAL(5,2)',
        'production_kw': 'DECIMAL(8,3)',
        'temperature_c': 'DECIMAL(5,1)',
        'cloud_factor': 'DECIMAL(3,2)',
        'temp_efficiency': 'DECIMAL(4,3)',
        'status': 'VARCHAR(20)',
        'city': 'VARCHAR(50)',
        'ingestion_timestamp': 'TIMESTAMPTZ DEFAULT NOW()'
    }
}

CLOUD_CATEGORIES = {
    'clear_sky': {'min': 0, 'max': 20, 'description': 'Minimal clouds'},
    'partly_cloudy': {'min': 21, 'max': 60, 'description': 'Moderate clouds'},
    'cloudy': {'min': 61, 'max': 100, 'description': 'Heavy clouds'}
}

UV_CATEGORIES = {
    'low': {'min': 0, 'max': 2, 'description': 'Minimal radiation'},
    'moderate': {'min': 2, 'max': 5, 'description': 'Good radiation'},
    'high': {'min': 5, 'max': 15, 'description': 'Intense radiation'}
}

WIND_CATEGORIES = {
    'calm': {'min': 0, 'max': 5, 'description': 'Minimal wind'},
    'light': {'min': 5, 'max': 20, 'description': 'Good cooling'},
    'moderate': {'min': 20, 'max': 40, 'description': 'Strong cooling'},
    'strong': {'min': 40, 'max': 200, 'description': 'Structural concern'}
}

BATTERY_PARAMS = {
    'include_battery': True,
    'battery_capacity_kwh': 5.0,
    'battery_efficiency': 0.90,
    'battery_cost_per_kwh': 450,
    'battery_lifetime_years': 10,
    'min_days_autonomy': 1,
}

PANEL_PARAMS = {
    'panels': 10,
    'panel_power_kw': 3.0,
    'panel_efficiency': 0.19,
    'panel_type': 'Monocrystalline',
    'temp_loss_coeff': 0.004,
    'panel_width_m': 1.0,
    'panel_height_m': 1.7,
    'panel_area_m2': 1.7,
    'optimal_angle': 35,
    'orientation': 'South',
    'available_roof_area_m2': 20,
    'max_panels_by_area': None,
    'max_power_by_area_kw': None,
}

PANEL_PARAMS['max_panels_by_area'] = int(
    PANEL_PARAMS['available_roof_area_m2'] // PANEL_PARAMS['panel_area_m2']
)
PANEL_PARAMS['max_power_by_area_kw'] = round(
    PANEL_PARAMS['max_panels_by_area'] * PANEL_PARAMS['panel_power_kw'], 2
)

LOSS_PARAMS = {
    'system_losses': 0.14,
    'temp_loss_coeff': 0.004,
    'derating_factor': 0.85,
    'soiling_loss': 0.02,
    'degradation_rate': 0.005,
    'availability_loss': 0.01,
    'inverter_efficiency': 0.96,
    'inverter_replacement_year': 12,
    'inverter_replacement_cost': 1200,
}

ECON_PARAMS = {
    'installation_cost_per_kw': 1800,
    'annual_maintenance': 150,
    'electricity_rate': 0.30,
    'sell_back_rate': 0.10,
    'incentive_rate': 0.12,
    'annual_rate_increase': 0.03,
    'household_consumption': 2700,
    'analysis_years': 25,
    'discount_rate': 0.02,
}

SELF_CONSUMPTION_PERC = {
    'ten': 0.1,
    'twenty': 0.2,
    'thirty': 0.3,
    'forty': 0.4,
    'fifty': 0.5,
    'sixty': 0.6,
    'seventy': 0.7,
    'eighty': 0.8,
    'ninety': 0.9,
    'hundred': 1.0
}

self_consumption = 'thirty'

SEASONAL_FACTORS = {
    'January': 0.7,
    'February': 1.0,
    'March': 1.4,
    'April': 1.8,
    'May': 2.1,
    'June': 2.3,
    'July': 2.4,
    'August': 2.2,
    'September': 1.9,
    'October': 1.3,
    'November': 0.8,
    'December': 0.6,
}

LOCATION_PARAMS = {
    'city': 'Turin',
    'country': 'Italy',
    'latitude': 45.0703,
    'longitude': 7.6869,
    'timezone': 'Europe/Rome',
    'elevation_m': 239,
}

SIMULATION_PARAMS = {
    'analysis_year': 2026,
    'seed': 2602,
    'panel_tilt_deg': 35,
    'panel_azimuth_deg': 0,
    'albedo': 0.20,
    'nominal_operating_cell_temp_c': 45.0,
    'site_calibration_factor': 0.84,
}

LOAD_PROFILE_PARAMS = {
    'base_load_kw': 0.18,
    'morning_peak_kw': 0.55,
    'evening_peak_kw': 0.85,
    'winter_bias': 0.10,
    'weekend_bias': 0.06,
}
