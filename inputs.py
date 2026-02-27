DEFAULTS = {
    # General
    "hours_per_year": 8600,
    "inflation_rate": 0.02,
    "electricity_price_usd_per_mwh": 80,
    "discount_rate": 0.08,

    # Geothermal
    "geothermal_flowrate_bpd": 5500,
    "geothermal_production_temperature_c": 120.0,
    "geothermal_injection_temperature_c": 70.0,
    "geothermal_conversion_efficiency": 0.1,
    "geothermal_aux_consumption_fraction": 0.12,
    "geothermal_capacity_factor": 0.65,
    "geothermal_capex_usd_per_mw": 2500000,
    "geothermal_annual_om_percent_of_capex": 0.02,
    "geothermal_project_lifetime_years": 25,
    "geothermal_land_use_sqm_per_mw": 500,

    # Diesel
    "diesel_capex_usd_per_mw": 650000,
    "diesel_annual_om_percent_of_capex": 0.08,
    "diesel_fuel_cost_usd_per_liter": 0.9,
    "diesel_sfc_l_per_kwh": 0.25,
    "diesel_project_lifetime_years": 25,
    "diesel_land_use_sqm_per_mw": 100,

    # Solar
    "solar_capex_usd_per_mw": 850000,
    "solar_annual_om_percent_of_capex": 0.015,
    "solar_project_lifetime_years": 25,
    "solar_capacity_factor": 0.3,
    "solar_land_use_sqm_per_mw": 20000,
    "panel_degradation_rate": 0.005,
    "inverter_life_years": 12,
    "inverter_replacement_cost_per_mw": 75000.0,
    "battery_capex_per_mwh": 200000.0,
    "battery_capacity_mwh_per_mw_pv": 1.0,
    "battery_annual_cycles": 300,
    "battery_efficiency": 0.85,
    "battery_life_years": 10,
    "battery_o_and_m_cost_per_mwh_yr": 4000.0,
}