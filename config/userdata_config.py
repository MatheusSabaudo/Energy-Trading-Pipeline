# config.py - Central configuration for Solar PV Analysis

# ============================================
# 1. WEATHER CATEGORIES (Q1)
# ============================================

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

# ============================================
# 2. BATTERY CONFIGURATION (Q1 Research)
# ============================================

BATTERY_PARAMS = {
    'include_battery': True,                # Enable/disable battery analysis
    'battery_capacity_kwh': 5.0,            # kWh storage
    'battery_efficiency': 0.90,             # 90% round-trip efficiency
    'battery_cost_per_kwh': 450,            # € per kWh
    'battery_lifetime_years': 10,           # years until replacement
    'min_days_autonomy': 1,                 # days of backup without sun
}

# ============================================
# 3. PANEL CONFIGURATION (Q2)
# ============================================

PANEL_PARAMS = {

    # Panel specifications
    'panel_power_kw': 3.0,                  # kWp - nominal power under STC
    'panel_efficiency': 0.19,               # 19% - percentage of sunlight converted
    'panel_type': 'Monocrystalline',        # Polycrystalline, Monocrystalline, PERC, Experimental
    
    # Physical dimensions
    'panel_width_m': 1.0,                   # meters
    'panel_height_m': 1.7,                  # meters
    'panel_area_m2': 1.7,                   # square meters per panel
    
    # Installation
    'optimal_angle': 35,                    # degrees from horizontal
    'orientation': 'South',                 # South, Southeast, Southwest
    'available_roof_area_m2': 20,           # total available space
    
    # Calculated values (will be computed)
    'max_panels_by_area': None,             # floor(available_area / panel_area)
    'max_power_by_area_kw': None,           # max_panels * panel_power_kw / 1000
}

# ============================================
# 4. LOSS PARAMETERS (Q2)
# ============================================

LOSS_PARAMS = {

    # Core losses
    'system_losses': 0.14,                  # 14% - wiring, inverter, connections
    'temp_loss_coeff': 0.004,               # 0.4% per °C above 25°C
    'derating_factor': 0.85,                # 15% catch-all for real conditions
    
    # Additional losses
    'soiling_loss': 0.02,                   # 2% - dirt on panels
    'degradation_rate': 0.005,              # 0.5% per year
    'availability_loss': 0.01,              # 1% - downtime for maintenance
    
    # Inverter
    'inverter_efficiency': 0.96,            # 96% conversion efficiency
    'inverter_replacement_year': 12,        # years until replacement
    'inverter_replacement_cost': 1200,      # €
}

# ============================================
# 5. ECONOMIC PARAMETERS (Q3)
# ============================================
ECON_PARAMS = {

    # Installation costs
    'installation_cost_per_kw': 1800,       # € per kWp installed
    'annual_maintenance': 150,              # € per year
    
    # Energy costs
    'electricity_rate': 0.30,               # €/kWh (purchase price)
    'sell_back_rate': 0.10,                 # €/kWh (sale to grid)
    'incentive_rate': 0.12,                 # €/kWh (Scambio Sul Posto)
    'annual_rate_increase': 0.03,           # 3% annual inflation
    
    # Consumption
    'household_consumption': 2700,          # kWh per year
    
    # Analysis period
    'analysis_years': 25,                   # years for ROI
    'discount_rate': 0.02,                  # 2% for NPV
}

# ============================================
# 6. SELF CONSUMPTION PERCENTILE (Q3)
# ============================================

SELF_CONSUMPTION_PERC = {
    'ten': 0.1,                             # 10% self-consumption
    'twenty': 0.2,                          # 20% self-consumption
    'thirty': 0.3,                          # 30% self-consumption
    'forty': 0.4,                           # 40% self-consumption
    'fifty': 0.5,                           # 50% self-consumption
    'sixty': 0.6,                           # 60% self-consumption
    'seventy': 0.7,                         # 70% self-consumption
    'eighty': 0.8,                          # 80% self-consumption
    'ninety': 0.9,                          # 90% self-consumption
    'hundred': 1.0                          # 100% self-consumption
}

# CHOOSE THE VALUE TO USE IN CALCULATIONS HERE
self_consumption = 'thirty'

# ============================================
# 7. SEASONAL FACTORS (Q3 - Turin specific)
# ============================================

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
    'October': 1.5,
    'November': 1.0,
    'December': 0.6
}


# ============================================
# 8. SIMULATION SCENARIOS (Q3)
# ============================================

SIMULATION_PARAMS = {
    'self_consumption_pcts': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],  # 20% to 70%
    'panel_sizes_to_test': [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0],  # kWp
    'analysis_years_to_report': [1, 3, 5, 10, 20, 25],  # Multi-year simulation
}

# ============================================
# 9. OUTPUT SETTINGS
# ============================================

OUTPUT_CONFIG = {
    'output_dir': 'notebooks_output',
    'save_intermediate': True,
    'save_final_report': True,
    'verbose': True,        # Print detailed output
}

# ============================================
# 10. HELPER FUNCTIONS
# ============================================

# def calculate_max_panels():

#     """Calculate maximum panels based on available area"""

#     area_per_panel = PANEL_PARAMS['panel_area_m2']
#     available_area = PANEL_PARAMS['available_roof_area_m2']
#     max_panels = int(available_area / area_per_panel)
#     PANEL_PARAMS['max_panels_by_area'] = max_panels
#     PANEL_PARAMS['max_power_by_area_kw'] = max_panels * PANEL_PARAMS['panel_power_kw']
#     return max_panels

# def get_seasonal_factor(month):
#     """Get seasonal factor for a given month"""
#     return SEASONAL_FACTORS.get(month, 1.0)

# def get_cloud_category(cloud_percent):
#     """Classify cloud cover percentage"""
#     for category, ranges in CLOUD_CATEGORIES.items():
#         if ranges['min'] <= cloud_percent <= ranges['max']:
#             return category
#     return 'unknown'

# # Auto-calculate derived values when imported
# calculate_max_panels()