import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from pathlib import Path

import inputs
from Calculation import run_full_analysis, SolarEconomicsHybrid, DieselEconomics

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Geothermal Economic Simulator | Sudapet",
    page_icon="sudapet_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== CUSTOM CSS & THEMING ====================
# Professional Dark Theme
st.markdown("""
<style>
    /* Main Background & Text */
    .main { background-color: #0E1117; color: #FAFAFA; }
    .stApp { background-color: #0E1117; }
    h1, h2, h3, h4, h5, h6, p, div, span, label { color: #FAFAFA !important; }
    
    /* Header Container */
    .main-header {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    
    .header-flex {
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    
    .header-logo {
        height: 120px;
        width: auto;
        border-radius: 8px;
        background: white;
        padding: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .title-text { margin: 0; font-size: 2.8rem; font-weight: 700; line-height: 1.2;}
    .subtitle-text { margin: 0.5rem 0 0 0; font-size: 1.4rem; color: #e3f2fd !important; opacity: 0.9; }
    .sub-subtitle-text { margin: 0.3rem 0 0 0; font-size: 1.2rem; color: #bbdefb !important; opacity: 0.8; }

    /* Metric Cards - Dark Theme */
    .metric-card {
        background: #1E293B;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        border-left: 4px solid #1976d2;
    }
    .metric-card .label { color: #94a3b8 !important; font-size: 0.95rem; margin-bottom: 0.4rem; font-weight: 500; }
    .metric-card .value { color: #FFFFFF; font-size: 1.6rem; font-weight: 700; }

    /* Section Headers */
    .section-header {
        background: linear-gradient(90deg, rgba(25,118,210,0.2) 0%, rgba(25,118,210,0) 100%);
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        margin: 2.5rem 0 1.5rem 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #90caf9 !important;
        border-left: 4px solid #1976d2;
    }

    /* Table Styling - Dark */
    .styled-table { 
        width: 100%; 
        border-collapse: collapse; 
        font-size: 0.95rem; 
        border-radius: 10px; 
        overflow: hidden; 
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        background-color: #1E293B;
    }
    .styled-table thead tr { 
        background-color: #1565C0; 
        color: white; 
        text-align: center; 
        font-weight: 600;
    }
    .styled-table th, .styled-table td { 
        padding: 12px 16px; 
        text-align: center; 
        border: 1px solid #334155; 
        color: #e2e8f0;
    }
    .styled-table tbody tr { transition: background-color 0.2s ease; }
    .styled-table tbody tr:hover { background-color: #2d3748; }
    .highlight-green { background-color: rgba(76,175,80,0.2) !important; font-weight: 600; color: #4caf50 !important; }
    .highlight-red { background-color: rgba(244,67,54,0.2) !important; font-weight: 600; color: #f44336 !important; }

    /* Sidebar Styling */
    .css-1d391kg, .css-1oe5cao { background-color: #1E293B; }
    .sidebar .sidebar-content { background-color: #1E293B; }

    /* Input Fields & Sliders */
    .stNumberInput, .stSlider { background-color: #1E293B; }
    .st-bb { background-color: #1E293B; }
    .st-at { background-color: #1976d2; }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* MOBILE RESPONSIVENESS */
    @media (max-width: 768px) {
        .header-flex {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
        }
        .header-logo {
            height: 80px;
        }
        .title-text {
            font-size: 2.2rem;
        }
        .subtitle-text {
            font-size: 1.1rem;
        }
        .sub-subtitle-text {
            font-size: 1rem;
        }
        .main-header {
            padding: 1.2rem;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            padding: 1rem;
        }
        .metric-card .value {
            font-size: 1.4rem;
        }
        /* Improve touch targets for sliders on mobile */
        .stSlider > div { height: 28px; }
        .stSlider thumb { height: 24px; width: 24px; }
    }
</style>
""", unsafe_allow_html=True)

# ==================== LOGO & HEADER ====================
def get_base64_image(image_path):
    """Convert image file to base64 string for HTML embedding."""
    img_path = Path(image_path)
    if img_path.exists():
        with open(img_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

logo_base64 = get_base64_image("sudapet_logo.png")

# Header with Logo
if logo_base64:
    st.markdown(f"""
    <div class="main-header">
        <div class="header-flex">
            <img src="data:image/png;base64,{logo_base64}" class="header-logo">
            <div>
                <h1 class="title-text">Geothermal Economic Simulator</h1>
                <p class="subtitle-text">Comparative Analysis: Geothermal • Diesel • Solar Hybrid</p>
                <p class="sub-subtitle-text">Modeling equal energy output from a single hot water well resource</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1 class="title-text">Geothermal Economic Simulator</h1>
        <p class="subtitle-text">Comparative Analysis: Geothermal • Diesel • Solar Hybrid</p>
    </div>
    """, unsafe_allow_html=True)

# ==================== SIDEBAR INPUTS ====================
D = inputs.DEFAULTS

# Use columns inside sidebar for a more compact layout on mobile
st.sidebar.markdown("## ⚙️ Project Parameters")

with st.sidebar.expander("🌍 General Parameters", expanded=True):
    hours_per_year = st.number_input("Operating Hours/Year", value=D['hours_per_year'], step=100, help="Total hours the plant operates annually.")
    inflation_rate = st.number_input("Inflation Rate (%)", value=D['inflation_rate']*100, step=0.1, format="%.1f", help="Annual inflation rate for cost escalation.") / 100
    electricity_price = st.number_input("Electricity Price ($/MWh)", value=float(D['electricity_price_usd_per_mwh']), step=5.0, help="Selling price of generated electricity.")
    discount_rate = st.number_input("Discount Rate (%)", value=D['discount_rate']*100, step=0.1, format="%.1f", help="Rate used to calculate Net Present Value (NPV).") / 100

with st.sidebar.expander("🌋 Geothermal Parameters", expanded=False):
    geo_flow = st.number_input("Flow Rate (bbl/day)", value=D['geothermal_flowrate_bpd'], step=100, help="Geothermal fluid flow rate from the well.")
    geo_prod_temp = st.number_input("Production Temp (°C)", value=D['geothermal_production_temperature_c'], step=5.0, help="Temperature of the produced geothermal fluid.")
    geo_inj_temp = st.number_input("Injection Temp (°C)", value=D['geothermal_injection_temperature_c'], step=5.0, help="Temperature of the fluid after heat extraction, for reinjection.")
    geo_efficiency = st.number_input("Conversion Efficiency", value=D['geothermal_conversion_efficiency'], step=0.01, format="%.2f", help="Efficiency of converting thermal energy to electrical energy.")
    geo_aux = st.number_input("Aux Consumption Fraction", value=D['geothermal_aux_consumption_fraction'], step=0.01, format="%.2f", help="Fraction of generated power used to run the plant itself.")
    geo_cf = st.slider("Geo Capacity Factor", 0.0, 1.0, value=D['geothermal_capacity_factor'], step=0.05, help="Ratio of actual output to maximum possible output over a period.")
    geo_capex_per_mw = st.number_input("Geo CAPEX ($/MW)", value=D['geothermal_capex_usd_per_mw'], step=100000, help="Capital expenditure per megawatt of installed capacity.")
    geo_om = st.number_input("Geo O&M (% of CAPEX)", value=D['geothermal_annual_om_percent_of_capex']*100, step=0.1, format="%.1f", help="Annual operation & maintenance cost as a percentage of CAPEX.") / 100
    geo_lifetime = st.number_input("Geo Lifetime (years)", value=D['geothermal_project_lifetime_years'], step=1, help="Expected economic lifetime of the geothermal plant.")

with st.sidebar.expander("⛽ Diesel Parameters", expanded=False):
    diesel_capex_mw = st.number_input("Diesel CAPEX ($/MW)", value=D['diesel_capex_usd_per_mw'], step=50000, help="Capital expenditure per megawatt of installed diesel capacity.")
    diesel_om = st.number_input("Diesel O&M (% of CAPEX)", value=D['diesel_annual_om_percent_of_capex']*100, step=0.1, format="%.1f", help="Annual O&M cost as a percentage of diesel CAPEX.") / 100
    diesel_fuel = st.number_input("Diesel Fuel ($/liter)", value=D['diesel_fuel_cost_usd_per_liter'], step=0.1, format="%.2f", help="Cost of diesel fuel per liter.")
    diesel_sfc = st.number_input("Diesel SFC (L/kWh)", value=D['diesel_sfc_l_per_kwh'], step=0.01, format="%.2f", help="Specific fuel consumption: liters of fuel per kWh generated.")
    diesel_lifetime = st.number_input("Diesel Lifetime (years)", value=D['diesel_project_lifetime_years'], step=1, help="Expected economic lifetime of the diesel plant.")

with st.sidebar.expander("☀️ Solar + Battery Parameters", expanded=False):
    solar_capex_mw = st.number_input("Solar CAPEX ($/MW)", value=D['solar_capex_usd_per_mw'], step=50000, help="Capital expenditure per megawatt of installed solar PV capacity.")
    solar_om = st.number_input("Solar O&M (% of CAPEX)", value=D['solar_annual_om_percent_of_capex']*100, step=0.1, format="%.1f", help="Annual O&M cost as a percentage of solar CAPEX.") / 100
    solar_cf = st.slider("Solar Capacity Factor", 0.0, 1.0, value=D['solar_capacity_factor'], step=0.05, help="Average capacity factor for the solar PV plant.")
    solar_lifetime = st.number_input("Solar Lifetime (years)", value=D['solar_project_lifetime_years'], step=1, help="Expected economic lifetime of the solar plant.")
    panel_degrade = st.number_input("Panel Degradation Rate (%/yr)", value=D['panel_degradation_rate']*100, step=0.1, format="%.1f", help="Annual rate of solar panel efficiency degradation.") / 100
    inverter_life = st.number_input("Inverter Life (years)", value=D['inverter_life_years'], step=1, help="Lifespan of inverters before replacement is needed.")
    inverter_cost = st.number_input("Inverter Replacement ($/MW)", value=D['inverter_replacement_cost_per_mw'], step=5000.0, help="Cost to replace inverters per megawatt of capacity.")
    batt_capex_mwh = st.number_input("Battery CAPEX ($/MWh)", value=D['battery_capex_per_mwh'], step=10000.0, help="Capital expenditure per megawatt-hour of battery storage.")
    batt_mwh_per_mw = st.number_input("Battery MWh per MW PV", value=D['battery_capacity_mwh_per_mw_pv'], step=0.1, format="%.1f", help="Storage capacity (MWh) installed per megawatt of solar PV.")
    batt_efficiency = st.slider("Battery Efficiency", 0.0, 1.0, value=D['battery_efficiency'], step=0.05, help="Round-trip efficiency of the battery storage system.")
    batt_life = st.number_input("Battery Life (years)", value=D['battery_life_years'], step=1, help="Expected lifespan of the battery system before replacement.")
    batt_cycles = st.number_input("Battery Annual Cycles", value=D['battery_annual_cycles'], step=10, help="Number of full charge-discharge cycles per year.")
    batt_om = st.number_input("Battery O&M ($/MWh/yr)", value=D['battery_o_and_m_cost_per_mwh_yr'], step=500.0, help="Annual operation & maintenance cost per MWh of battery capacity.")

# ==================== ASSEMBLE PARAMETERS & RUN ANALYSIS ====================
PROJECT_PARAMETERS = {
    'hours_per_year': hours_per_year,
    'inflation_rate': inflation_rate,
    'electricity_price_usd_per_mwh': electricity_price,
    'discount_rate': discount_rate,

    'geothermal_flowrate_bpd': geo_flow,
    'geothermal_production_temperature_c': geo_prod_temp,
    'geothermal_injection_temperature_c': geo_inj_temp,
    'geothermal_conversion_efficiency': geo_efficiency,
    'geothermal_aux_consumption_fraction': geo_aux,
    'geothermal_capacity_factor': geo_cf,
    'geothermal_capex_usd_per_mw': geo_capex_per_mw,
    'geothermal_annual_om_percent_of_capex': geo_om,
    'geothermal_project_lifetime_years': geo_lifetime,
    'geothermal_land_use_sqm_per_mw': 500,

    'diesel_capex_usd_per_mw': diesel_capex_mw,
    'diesel_annual_om_percent_of_capex': diesel_om,
    'diesel_fuel_cost_usd_per_liter': diesel_fuel,
    'diesel_sfc_l_per_kwh': diesel_sfc,
    'diesel_project_lifetime_years': diesel_lifetime,
    'diesel_land_use_sqm_per_mw': 100,

    'solar_capex_usd_per_mw': solar_capex_mw,
    'solar_annual_om_percent_of_capex': solar_om,
    'solar_project_lifetime_years': solar_lifetime,
    'solar_capacity_factor': solar_cf,
    'solar_land_use_sqm_per_mw': 20000,
    'panel_degradation_rate': panel_degrade,
    'inverter_life_years': inverter_life,
    'inverter_replacement_cost_per_mw': inverter_cost,
    'battery_capex_per_mwh': batt_capex_mwh,
    'battery_capacity_mwh_per_mw
\<Streaming stoppped because the conversation grew too long for this model\>
