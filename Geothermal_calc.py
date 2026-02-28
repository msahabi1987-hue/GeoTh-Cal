import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
from pathlib import Path

import inputs
from Calculation import run_full_analysis, SolarEconomicsHybrid, DieselEconomics

# Page Config
# ===========
st.set_page_config(
    page_title="Geothermal Economic Comparison",
    page_icon="sudapet_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Logo Loader
# ===========
def get_base64_image(image_path):
    """Convert image file to base64 string for HTML embedding."""
    img_path = Path(image_path)
    if img_path.exists():
        with open(img_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

logo_base64 = get_base64_image("sudapet_logo.png")

# Custom CSS (Responsive)
# =======================
st.markdown("""
<style>
    /* Header Container */
    .main-header {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #43A047 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    
    .header-flex {
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    
    .header-logo {
        height: 150px;
        width: auto;
        border-radius: 10px;
        background: white;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .title-text { margin: 0; font-size: 2.5rem; color: white; line-height: 1.2;}
    .subtitle-text { margin: 0.5rem 0 0 0; font-size: 1.5rem; color: #E8F5E9; }
    .sub-subtitle-text { margin: 0.3rem 0 0 0; font-size: 1.3rem; color: #A5D6A7; }

    /* Metric cards */
    .metric-card {
        background: #FFFFFF;
        border-left: 4px solid #2E7D32;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 0.8rem;
    }
    .metric-card .label { color: #666; font-size: 1.2rem; margin-bottom: 0.2rem; }
    .metric-card .value { color: #1B5E20; font-size: 1.8rem; font-weight: 700; }

    /* Section headers */
    .section-header {
        background: #E8F5E9;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #2E7D32;
        margin: 1.5rem 0 1rem 0;
        font-size: 1.15rem;
        font-weight: 600;
        color: #1B5E20;
    }

    /* Table styling */
    .styled-table { width: 100%; border-collapse: collapse; font-size: 1.3rem; border-radius: 8px; overflow: hidden; }
    .styled-table thead tr { background-color: #1565C0; color: white; text-align: center; }
    .styled-table th, .styled-table td { padding: 10px 14px; text-align: center; border: 1px solid #ddd; }
    .highlight-green { background-color: #C8E6C9 !important; font-weight: 600; }
    .highlight-red { background-color: #FFCDD2 !important; font-weight: 600; }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* MOBILE RESPONSIVENESS (SMARTPHONES)                                 */
    /* =================================== */
    @media (max-width: 768px) {
        .header-flex {
            flex-direction: column; /* Stack logo above text */
            text-align: center;     /* Center everything */
            gap: 1rem;
        }
        .header-logo {
            height: 90px; /* Make logo smaller on phones */
        }
        .title-text {
            font-size: 1.6rem; /* Smaller title font */
        }
        .subtitle-text {
            font-size: 1.2rem;
        }
        .sub-subtitle-text {
            font-size: 1rem;
        }
        .main-header {
            padding: 1rem; /* Less padding around the edges on small screens */
        }
        .metric-card .value {
            font-size: 1.1rem; /* Slightly smaller numbers on phones */
        }
    }
</style>
""", unsafe_allow_html=True)
# Header with Logo
# ================
if logo_base64:
    st.markdown(f"""
    <div class="main-header">
        <div class="header-flex">
            <img src="data:image/png;base64,{logo_base64}" class="header-logo">
            <div>
                <h1 class="title-text">Geothermal Economic Comparison</h1>
                <p class="subtitle-text">Comparative analysis — Geothermal vs Diesel vs Solar (Hybrid+BESS)</p>
                <p class="sub-subtitle-text">25-Year Economic Outlook: Single-Well Geothermal Assessment vs. Diesel & Solar Parity.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>Geothermal Economic Calculation</h1>
        <p>Comparative analysis — Geothermal vs Diesel vs Solar (Hybrid+BESS)</p>
    </div>
    """, unsafe_allow_html=True)
# Sidebar Inputs
# ==============
D = inputs.DEFAULTS

st.sidebar.markdown("## ⚙️ Project Parameters")

st.sidebar.markdown("### 🌍 General")
hours_per_year = st.sidebar.number_input("Operating Hours/Year", value=D['hours_per_year'], step=100)
inflation_rate = st.sidebar.number_input("Inflation Rate", value=D['inflation_rate'], step=0.005, format="%.3f")
electricity_price = st.sidebar.number_input("Electricity Price ($/MWh)", value=float(D['electricity_price_usd_per_mwh']), step=5.0)
discount_rate = st.sidebar.number_input("Discount Rate", value=D['discount_rate'], step=0.005, format="%.3f")

st.sidebar.markdown("### 🌋 Geothermal")
geo_flow = st.sidebar.number_input("Flow Rate (bbl/day)", value=D['geothermal_flowrate_bpd'], step=100)
geo_prod_temp = st.sidebar.number_input("Production Temp (°C)", value=D['geothermal_production_temperature_c'], step=5.0)
geo_inj_temp = st.sidebar.number_input("Injection Temp (°C)", value=D['geothermal_injection_temperature_c'], step=5.0)
geo_efficiency = st.sidebar.number_input("Conversion Efficiency", value=D['geothermal_conversion_efficiency'], step=0.01, format="%.2f")
geo_aux = st.sidebar.number_input("Aux Consumption Fraction", value=D['geothermal_aux_consumption_fraction'], step=0.01, format="%.2f")
geo_cf = st.sidebar.number_input("Geo Capacity Factor", value=D['geothermal_capacity_factor'], step=0.05, format="%.2f")
geo_capex_per_mw = st.sidebar.number_input("Geo CAPEX ($/MW)", value=D['geothermal_capex_usd_per_mw'], step=100000)
geo_om = st.sidebar.number_input("Geo O&M (% of CAPEX)", value=D['geothermal_annual_om_percent_of_capex'], step=0.005, format="%.3f")
geo_lifetime = st.sidebar.number_input("Geo Lifetime (years)", value=D['geothermal_project_lifetime_years'], step=1)

st.sidebar.markdown("### ⛽ Diesel")
diesel_capex_mw = st.sidebar.number_input("Diesel CAPEX ($/MW)", value=D['diesel_capex_usd_per_mw'], step=50000)
diesel_om = st.sidebar.number_input("Diesel O&M (% of CAPEX)", value=D['diesel_annual_om_percent_of_capex'], step=0.01, format="%.2f")
diesel_fuel = st.sidebar.number_input("Diesel Fuel ($/liter)", value=D['diesel_fuel_cost_usd_per_liter'], step=0.1, format="%.2f")
diesel_sfc = st.sidebar.number_input("Diesel SFC (L/kWh)", value=D['diesel_sfc_l_per_kwh'], step=0.01, format="%.2f")
diesel_lifetime = st.sidebar.number_input("Diesel Lifetime (years)", value=D['diesel_project_lifetime_years'], step=1)

st.sidebar.markdown("### ☀️ Solar + Battery")
solar_capex_mw = st.sidebar.number_input("Solar CAPEX ($/MW)", value=D['solar_capex_usd_per_mw'], step=50000)
solar_om = st.sidebar.number_input("Solar O&M (% of CAPEX)", value=D['solar_annual_om_percent_of_capex'], step=0.005, format="%.3f")
solar_cf = st.sidebar.number_input("Solar Capacity Factor", value=D['solar_capacity_factor'], step=0.05, format="%.2f")
solar_lifetime = st.sidebar.number_input("Solar Lifetime (years)", value=D['solar_project_lifetime_years'], step=1)
panel_degrade = st.sidebar.number_input("Panel Degradation Rate", value=D['panel_degradation_rate'], step=0.001, format="%.3f")
inverter_life = st.sidebar.number_input("Inverter Life (years)", value=D['inverter_life_years'], step=1)
inverter_cost = st.sidebar.number_input("Inverter Replacement ($/MW)", value=D['inverter_replacement_cost_per_mw'], step=5000.0)
batt_capex_mwh = st.sidebar.number_input("Battery CAPEX ($/MWh)", value=D['battery_capex_per_mwh'], step=10000.0)
batt_mwh_per_mw = st.sidebar.number_input("Battery MWh per MW PV", value=D['battery_capacity_mwh_per_mw_pv'], step=0.1, format="%.1f")
batt_efficiency = st.sidebar.number_input("Battery Efficiency", value=D['battery_efficiency'], step=0.05, format="%.2f")
batt_life = st.sidebar.number_input("Battery Life (years)", value=D['battery_life_years'], step=1)
batt_cycles = st.sidebar.number_input("Battery Annual Cycles", value=D['battery_annual_cycles'], step=10)
batt_om = st.sidebar.number_input("Battery O&M ($/MWh/yr)", value=D['battery_o_and_m_cost_per_mwh_yr'], step=500.0)

# Assemble Parameters & Run
# =========================
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
    'battery_capacity_mwh_per_mw_pv': batt_mwh_per_mw,
    'battery_annual_cycles': batt_cycles,
    'battery_efficiency': batt_efficiency,
    'battery_life_years': batt_life,
    'battery_o_and_m_cost_per_mwh_yr': batt_om,
}

# Run the full analysis
R = run_full_analysis(PROJECT_PARAMETERS)

# Helper: Metric Card
# ===================
def metric_card(label, value):
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
    </div>"""

# Section 1: Geothermal Resource Assessment
# =========================================
st.markdown('<div class="section-header">🔥 Geothermal Resource Assessment</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(metric_card("Thermal Power", f"{R['thermal_power_mw']:.3f} MW"), unsafe_allow_html=True)
with c2:
    st.markdown(metric_card("Gross Electric", f"{R['gross_electric_mw']:.3f} MW"), unsafe_allow_html=True)
with c3:
    st.markdown(metric_card("Net Electric", f"{R['net_electric_mw']:.3f} MW"), unsafe_allow_html=True)
with c4:
    st.markdown(metric_card("Flow Rate", f"{R['flowrate_kgs']:.2f} kg/s"), unsafe_allow_html=True)

st.markdown(metric_card("Target Energy Output (25 yr)", f"{R['total_energy_gwh']:.2f} GWh"), unsafe_allow_html=True)

# Section 2: Comparative Performance Table
# ========================================
st.markdown('<div class="section-header">📊 25-Year Comparative Financial Metrics — Equal Energy Output</div>', unsafe_allow_html=True)


def fmt_money(v):
    return f"${v:,.2f}"


def fmt_f3(v):
    return f"{v:,.3f}"


def fmt_f2(v):
    return f"{v:,.2f}"


# Build comparison data
projects = ['Geothermal', 'Diesel', 'Solar (Hybrid)']
gross_mw = [R['geo_gross_mw'], R['diesel_gross_mw'], R['solar_gross_mw']]
capex_m = [R['geo_capex'] / 1e6, R['diesel_capex'] / 1e6, R['solar_capex'] / 1e6]
energy_gwh = [R['total_energy_gwh']] * 3
cum_cost_m = [R['geo_cum_cost'] / 1e6, R['diesel_cum_cost'] / 1e6, R['solar_cum_cost'] / 1e6]
cum_profit_m = [R['geo_cum_profit'] / 1e6, R['diesel_cum_profit'] / 1e6, R['solar_cum_profit'] / 1e6]


def highlight_col(values, best='min'):
    """Return list of CSS class for min/max highlighting."""
    arr = np.array(values)
    classes = [''] * len(values)
    if best == 'min':
        classes[int(np.argmin(arr))] = 'highlight-green'
        classes[int(np.argmax(arr))] = 'highlight-red'
    else:
        classes[int(np.argmax(arr))] = 'highlight-green'
        classes[int(np.argmin(arr))] = 'highlight-red'
    return classes


capex_cls = highlight_col(capex_m, 'min')
cost_cls = highlight_col(cum_cost_m, 'min')
profit_cls = highlight_col(cum_profit_m, 'max')

table_html = """<table class="styled-table">
<thead><tr>
    <th>Project</th><th>Gross Power (MW)</th><th>Upfront CAPEX ($M)</th>
    <th>Total Energy (GWh)</th><th>25-Yr Cumulative Cost ($M)</th><th>25-Yr Cumulative Net Profit ($M)</th>
</tr></thead><tbody>"""

for i in range(3):
    table_html += f"""<tr>
        <td><strong>{projects[i]}</strong></td>
        <td>{fmt_f3(gross_mw[i])}</td>
        <td class="{capex_cls[i]}">{fmt_money(capex_m[i])}</td>
        <td>{fmt_f2(energy_gwh[i])}</td>
        <td class="{cost_cls[i]}">{fmt_money(cum_cost_m[i])}</td>
        <td class="{profit_cls[i]}">{fmt_money(cum_profit_m[i])}</td>
    </tr>"""

table_html += "</tbody></table>"
st.markdown(table_html, unsafe_allow_html=True)

# Section 3: NPV & LCOE Table
# ===========================
st.markdown('<div class="section-header">💰 Net Present Value (NPV) & Levelized Cost of Electricity (LCOE)</div>', unsafe_allow_html=True)

npvs = [R['geo_npv'], R['diesel_npv'], R['solar_npv']]
lcoes = [R['geo_lcoe'], R['diesel_lcoe'], R['solar_lcoe']]

npv_cls = highlight_col(npvs, 'max')
lcoe_cls = highlight_col(lcoes, 'min')

table2 = """<table class="styled-table">
<thead><tr><th>Project</th><th>NPV (USD)</th><th>LCOE ($/MWh)</th></tr></thead><tbody>"""

for i in range(3):
    table2 += f"""<tr>
        <td><strong>{projects[i]}</strong></td>
        <td class="{npv_cls[i]}">{fmt_money(npvs[i])}</td>
        <td class="{lcoe_cls[i]}">{fmt_money(lcoes[i])}</td>
    </tr>"""

table2 += "</tbody></table>"
st.markdown(table2, unsafe_allow_html=True)

# Section 4: Charts
# =================
st.markdown('<div class="section-header">📈 Visual Comparison</div>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    # CAPEX Bar Chart
    fig_capex = go.Figure(data=[go.Bar(
        x=projects,
        y=capex_m,
        marker_color=['#2E7D32', '#37474F', '#FFC107'],
        text=[f"${v:,.2f}M" for v in capex_m],
        textposition='outside'
    )])
    fig_capex.update_layout(
        title="Upfront CAPEX ($M)",
        yaxis_title="Million USD",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig_capex, use_container_width=True)

with col_right:
    # LCOE Bar Chart
    fig_lcoe = go.Figure(data=[go.Bar(
        x=projects,
        y=lcoes,
        marker_color=['#2E7D32', '#37474F', '#FFC107'],
        text=[f"${v:,.2f}" for v in lcoes],
        textposition='outside'
    )])
    fig_lcoe.update_layout(
        title="LCOE ($/MWh)",
        yaxis_title="$/MWh",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig_lcoe, use_container_width=True)

# Cumulative Cost & Profit
col_left2, col_right2 = st.columns(2)

with col_left2:
    fig_cost = go.Figure(data=[go.Bar(
        x=projects,
        y=cum_cost_m,
        marker_color=['#2E7D32', '#37474F', '#FFC107'],
        text=[f"${v:,.2f}M" for v in cum_cost_m],
        textposition='outside'
    )])
    fig_cost.update_layout(
        title="25-Year Cumulative Cost ($M)",
        yaxis_title="Million USD",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig_cost, use_container_width=True)

with col_right2:
    fig_profit = go.Figure(data=[go.Bar(
        x=projects,
        y=cum_profit_m,
        marker_color=['#2E7D32', '#37474F', '#FFC107'],
        text=[f"${v:,.2f}M" for v in cum_profit_m],
        textposition='outside'
    )])
    fig_profit.update_layout(
        title="25-Year Cumulative Net Profit ($M)",
        yaxis_title="Million USD",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig_profit, use_container_width=True)

# Section 5: Yearly Cumulative Profit Chart
# =========================================
st.markdown('<div class="section-header">📉 Yearly Cumulative Net Profit Trajectory</div>', unsafe_allow_html=True)

lifetime = max(geo_lifetime, diesel_lifetime, solar_lifetime)
years_range = list(range(0, lifetime + 1))

def build_yearly_cumulative(proj, proj_type, lt, infl, params):
    """Build year-by-year cumulative net profit list starting from -CAPEX at year 0."""
    cum = [-proj.total_capex_usd]
    running = -proj.total_capex_usd
    for y in range(1, lt + 1):
        if isinstance(proj, SolarEconomicsHybrid):
            om = proj.annual_om_usd_year_1 * ((1 + infl) ** (y - 1))
            if y % proj.inverter_life_years == 0 and y < lt:
                om += proj.inverter_replacement_cost_per_mw * proj.installed_capacity_mw * ((1 + infl) ** (y - 1))
            if y % proj.battery_life_years == 0 and y < lt:
                om += proj.battery_capacity_mwh * proj.battery_capex_per_mwh * ((1 + infl) ** (y - 1))
            rev = (proj.calculate_energy_mwh_for_year(y) * proj.electricity_price_offpeak_usd_per_mwh
                   + proj.calculate_battery_revenue_usd_for_year(y))
        else:
            om = proj.annual_om_usd * ((1 + infl) ** (y - 1))
            rev = proj.annual_revenue_usd * ((1 + infl) ** (y - 1))

        fuel = 0
        if hasattr(proj, 'annual_fuel_cost_usd'):
            fuel = proj.annual_fuel_cost_usd * ((1 + infl) ** (y - 1))

        if isinstance(proj, DieselEconomics) and y > 0 and y % 10 == 0 and y < lt:
            repl = (params['diesel_capex_usd_per_mw'] * proj.gross_power_mw) * 1.10 * ((1 + infl) ** (y - 1))
            om += repl

        running += rev - om - fuel
        cum.append(running)
    return cum


geo_yearly = build_yearly_cumulative(R['geo_proj'], 'Geo', geo_lifetime, inflation_rate, PROJECT_PARAMETERS)
diesel_yearly = build_yearly_cumulative(R['diesel_proj'], 'Diesel', diesel_lifetime, inflation_rate, PROJECT_PARAMETERS)
solar_yearly = build_yearly_cumulative(R['solar_proj'], 'Solar', solar_lifetime, inflation_rate, PROJECT_PARAMETERS)

fig_traj = go.Figure()
fig_traj.add_trace(go.Scatter(
    x=list(range(len(geo_yearly))), y=[v / 1e6 for v in geo_yearly],
    name='Geothermal', mode='lines+markers', line=dict(color='#2E7D32', width=3)
))
fig_traj.add_trace(go.Scatter(
    x=list(range(len(diesel_yearly))), y=[v / 1e6 for v in diesel_yearly],
    name='Diesel', mode='lines+markers', line=dict(color='#D84315', width=3)
))
fig_traj.add_trace(go.Scatter(
    x=list(range(len(solar_yearly))), y=[v / 1e6 for v in solar_yearly],
    name='Solar (Hybrid)', mode='lines+markers', line=dict(color='#F9A825', width=3)
))
fig_traj.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
fig_traj.update_layout(
    title="Cumulative Net Profit Over Project Lifetime",
    xaxis_title="Year",
    yaxis_title="Cumulative Net Profit ($M)",
    template="plotly_white",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_traj, use_container_width=True)

# Section 6: Interpretation
# ========================
st.markdown('<div class="section-header">📝 Economic Interpretation</div>', unsafe_allow_html=True)

st.markdown(f"""
**This analysis compares Geothermal, Diesel, and Solar projects on an 'apple-to-apple' baseload perspective, ensuring each technology delivers the same total energy output of {R['total_energy_gwh']:.2f} GWh over a 25-year lifetime.**

---

**🌋 Geothermal vs ⛽ Diesel:**
Geothermal is overwhelmingly superior for baseload. To deliver the same {R['total_energy_gwh']:.2f} GWh, Diesel requires a {R['diesel_gross_mw']:.3f} MW plant vs Geothermal's {R['geo_gross_mw']:.3f} MW. Diesel's 25-year cumulative cost (${R['diesel_cum_cost']/1e6:,.2f}M) 
is drastically higher than Geothermal's (${R['geo_cum_cost']/1e6:,.2f}M), due to continuous fuel expenditure.

**🌋 Geothermal vs ☀️ Solar (Hybrid):**
To match Geothermal's total energy output, Solar requires a significantly larger installed capacity of {R['solar_gross_mw']:.3f} MW. Solar achieves a 25-year cumulative cost of ${R['solar_cum_cost']/1e6:,.2f}M 
vs Geothermal's ${R['geo_cum_cost']/1e6:,.2f}M. However, Geothermal's inherent continuous, dispatchable baseload nature remains a critical advantage for grid stability.

---

**Overall Conclusion:** For a truly 'apple-to-apple' baseload comparison delivering the same total energy over 25 years, **Geothermal emerges as the most balanced and strategically robust option**, offering strong economic performance relative to Diesel, and unmatched reliability compared to Solar.
""")

#Footer with Logo
st.markdown("---")
if logo_base64:
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0;">
        <img src="data:image/png;base64,{logo_base64}"
             style="height: 100px; width: auto; opacity: 0.7; margin-bottom: 0.8rem;"><br>
        <span style="color:#888; font-size:1.6rem;">
            Sudapet Company Ltd. - Development Department - Geothermal Project
        </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(
        "<div style='text-align:center; color:#888; font-size:3rem;'>"
        "Geothermal Economic Comparison • Based on single hot water producing well in oil field"
        "</div>",
        unsafe_allow_html=True
    )
