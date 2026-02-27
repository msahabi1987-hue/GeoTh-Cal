import numpy as np
import pandas as pd

# =============================================================================
# Geothermal Config — mirrors GeothermalEconomicsConfig from PDF
# =============================================================================

class GeothermalEconomicsConfig:
    def __init__(self, flowrate_bpd=None, production_temperature=None,
                 injection_temperature=None, conversion_efficiency=None, **kwargs):
        self.flowrate_bpd = flowrate_bpd
        self._flowrate_m3s = None
        if flowrate_bpd is not None:
            try:
                self._flowrate_m3s = (float(flowrate_bpd) * 0.158987) / 86400.0
            except Exception:
                self._flowrate_m3s = None
        self.production_temperature = production_temperature
        self.injection_temperature = injection_temperature
        if isinstance(conversion_efficiency, str) and '%' in conversion_efficiency:
            self.conversion_efficiency = float(conversion_efficiency.replace('%', '')) / 100.0
        else:
            self.conversion_efficiency = conversion_efficiency
        self.params = kwargs
        self.thermal_power_mw = None
        self.gross_electric_output_mw = None
        self.net_electric_output_mw = None
        self.annual_net_generation_mwh = None

    @property
    def flowrate_kgs(self):
        if self._flowrate_m3s is not None:
            return self._flowrate_m3s * 1000
        return None

    def calculate_thermal_power_mw(self):
        if None in [self.flowrate_kgs, self.production_temperature, self.injection_temperature]:
            return None
        delta_T = self.production_temperature - self.injection_temperature
        specific_heat_water = 4186
        thermal_power_watts = self.flowrate_kgs * specific_heat_water * delta_T
        self.thermal_power_mw = thermal_power_watts / 1_000_000
        return self.thermal_power_mw

    def calculate_gross_electric_output_mw(self):
        if None in [self.thermal_power_mw, self.conversion_efficiency]:
            return None
        self.gross_electric_output_mw = self.thermal_power_mw * self.conversion_efficiency
        return self.gross_electric_output_mw

    def calculate_net_electric_output_mw(self, aux_consumption_fraction=0.12):
        if self.gross_electric_output_mw is None:
            return None
        self.net_electric_output_mw = self.gross_electric_output_mw * (1 - aux_consumption_fraction)
        return self.net_electric_output_mw

    def calculate_annual_net_generation_mwh(self, capacity_factor=0.95, hours_per_year=8600):
        if self.net_electric_output_mw is None:
            return None
        self.annual_net_generation_mwh = self.net_electric_output_mw * hours_per_year * capacity_factor
        return self.annual_net_generation_mwh


# =============================================================================
# Geothermal Economics — mirrors GeothermalEconomics from PDF
# =============================================================================

class GeothermalEconomics:
    def __init__(self, parameters_dict, gross_power_mw, hours_per_year=8600):
        self.p = parameters_dict
        self.gross_power_mw = gross_power_mw
        self.net_power_mw = gross_power_mw * (1 - self.p.get('aux_consumption_fraction', 0.0))
        self.hours_per_year = hours_per_year
        self.total_capex_usd = 0.0
        self.annual_om_usd = 0.0
        self.npv = 0.0
        self.lcoe = 0.0
        self.annual_maintenance_usd = 0.0
        self.annual_revenue_usd = 0.0

    def calculate_capex_usd(self):
        capex_per_mw = self.p.get('power_plant_capex_usd_per_mw')
        if capex_per_mw is None:
            raise ValueError("power_plant_capex_usd_per_mw not provided")
        base_capex = capex_per_mw * self.gross_power_mw
        installation_cost = 0.20 * base_capex
        self.total_capex_usd = base_capex + installation_cost

    def calculate_annual_om_usd(self):
        maintenance_fraction = self.p.get('annual_om_percent_of_capex')
        if maintenance_fraction is None:
            raise ValueError("annual_om_percent_of_capex not provided")
        self.annual_maintenance_usd = self.total_capex_usd * maintenance_fraction
        self.annual_om_usd = self.annual_maintenance_usd

    def calculate_annual_revenue_usd(self):
        price_per_mwh = self.p.get('electricity_price_usd_per_mwh')
        if price_per_mwh is None:
            raise ValueError("electricity_price_usd_per_mwh not provided")
        annual_energy_mwh = self.net_power_mw * self.hours_per_year
        self.annual_revenue_usd = price_per_mwh * annual_energy_mwh

    def calculate_npv(self):
        years = int(self.p.get('project_lifetime_years'))
        discount_rate = self.p.get('discount_rate')
        inflation_rate = self.p.get('inflation_rate')
        if None in [years, discount_rate, inflation_rate]:
            raise ValueError("Missing NPV parameters")
        annual_net_year_1 = self.annual_revenue_usd - self.annual_om_usd
        years_array = np.arange(1, years + 1)
        nominal_cash_flows = annual_net_year_1 * (1 + inflation_rate) ** (years_array - 1)
        discount_factors = (1 + discount_rate) ** years_array
        pv_flows = nominal_cash_flows / discount_factors
        self.npv = -self.total_capex_usd + np.sum(pv_flows)

    def calculate_lcoe(self):
        years = int(self.p.get('project_lifetime_years'))
        r = self.p.get('discount_rate')
        if None in [years, r]:
            raise ValueError("Missing LCOE parameters")
        discounted_om = sum([self.annual_om_usd / ((1 + r) ** y) for y in range(1, years + 1)])
        discounted_energy = sum([
            (self.net_power_mw * self.hours_per_year * self.p.get('geothermal_capacity_factor', 1.0))
            / ((1 + r) ** y) for y in range(1, years + 1)
        ])
        self.lcoe = (self.total_capex_usd + discounted_om) / discounted_energy if discounted_energy > 0 else float('inf')

    def run_all(self):
        self.calculate_capex_usd()
        self.calculate_annual_om_usd()
        self.calculate_annual_revenue_usd()
        self.calculate_lcoe()
        self.calculate_npv()


# =============================================================================
# Diesel Economics — mirrors DieselEconomics from PDF
# =============================================================================

class DieselEconomics:
    def __init__(self, parameters_dict, gross_power_mw, hours_per_year=8600):
        self.p = parameters_dict
        self.gross_power_mw = gross_power_mw
        self.net_power_mw = gross_power_mw * (1 - self.p.get('aux_consumption_fraction', 0.0))
        self.hours_per_year = hours_per_year
        self.total_capex_usd = 0.0
        self.annual_fuel_cost_usd = 0.0
        self.annual_om_usd = 0.0
        self.annual_revenue_usd = 0.0
        self.npv = 0.0
        self.lcoe = 0.0
        self.annual_maintenance_usd = 0.0
        self.fuel_cost_per_mwh = 0.0

    def calculate_fuel_cost_per_mwh(self):
        sfc = self.p.get('diesel_sfc_l_per_kwh', 0.25)
        diesel_price = self.p.get('fuel_cost_usd_per_liter', 0.9)
        annual_energy_mwh = self.net_power_mw * self.hours_per_year * self.p.get('diesel_capacity_factor', 1.0)
        annual_energy_kwh = annual_energy_mwh * 1000
        annual_fuel_liters = annual_energy_kwh * sfc
        annual_fuel_cost = annual_fuel_liters * diesel_price
        self.fuel_cost_per_mwh = annual_fuel_cost / annual_energy_mwh if annual_energy_mwh > 0 else 0
        self.annual_fuel_cost_usd = annual_fuel_cost

    def calculate_capex_usd(self):
        capex_per_mw = self.p.get('capital_cost_usd_per_mw', 650_000)
        base_capex = capex_per_mw * self.gross_power_mw
        installation_cost = 0.10 * base_capex
        self.total_capex_usd = base_capex + installation_cost

    def calculate_annual_om_usd(self):
        maintenance_fraction = self.p.get('annual_om_percent_of_capex')
        if maintenance_fraction is None:
            raise ValueError("annual_om_percent_of_capex not provided")
        self.annual_maintenance_usd = self.total_capex_usd * maintenance_fraction
        self.annual_om_usd = self.annual_maintenance_usd

    def calculate_annual_revenue_usd(self):
        price_per_mwh = self.p.get('electricity_price_usd_per_mwh')
        if price_per_mwh is None:
            raise ValueError("electricity_price_usd_per_mwh not provided")
        annual_energy_mwh = self.net_power_mw * self.hours_per_year * self.p.get('diesel_capacity_factor', 1.0)
        self.annual_revenue_usd = price_per_mwh * annual_energy_mwh

    def calculate_npv(self):
        years = int(self.p.get('project_lifetime_years', 10))
        discount_rate = self.p.get('discount_rate')
        inflation_rate = self.p.get('inflation_rate')
        annual_net_year_1 = self.annual_revenue_usd - self.annual_om_usd - self.annual_fuel_cost_usd
        years_array = np.arange(1, years + 1)
        nominal_cash_flows = annual_net_year_1 * (1 + inflation_rate) ** (years_array - 1)
        discount_factors = (1 + discount_rate) ** years_array
        pv_flows = nominal_cash_flows / discount_factors
        self.npv = -self.total_capex_usd + np.sum(pv_flows)

    def calculate_lcoe(self):
        years = int(self.p.get('project_lifetime_years', 10))
        r = self.p.get('discount_rate')
        discounted_om = sum([
            (self.annual_om_usd + self.annual_fuel_cost_usd) / ((1 + r) ** y)
            for y in range(1, years + 1)
        ])
        discounted_energy = sum([
            (self.net_power_mw * self.hours_per_year) / ((1 + r) ** y)
            for y in range(1, years + 1)
        ])
        self.lcoe = (self.total_capex_usd + discounted_om) / discounted_energy if discounted_energy > 0 else float('inf')

    def run_all(self):
        self.calculate_capex_usd()
        self.calculate_fuel_cost_per_mwh()
        self.calculate_annual_om_usd()
        self.calculate_annual_revenue_usd()
        self.calculate_lcoe()
        self.calculate_npv()


# =============================================================================
# Solar Hybrid Economics — mirrors SolarEconomicsHybrid from PDF
# =============================================================================

class SolarEconomicsHybrid:
    """Hybrid Solar PV + Battery Energy Storage System (BESS) economic model."""

    def __init__(self, parameters_dict, gross_power_mw, hours_per_year=8600):
        self.p = parameters_dict
        self.gross_power_mw = gross_power_mw
        self.installed_capacity_mw = gross_power_mw
        self.hours_per_year = hours_per_year

        # PV Parameters
        self.solar_capex_usd_per_mw = self.p.get('solar_capex_usd_per_mw')
        self.inverter_life_years = self.p.get('inverter_life_years', 12)
        self.inverter_replacement_cost_per_mw = self.p.get('inverter_replacement_cost_per_mw', 75000.0)
        self.panel_degradation_rate = self.p.get('panel_degradation_rate', 0.005)
        self.solar_capacity_factor = self.p.get('solar_capacity_factor')

        # BESS Parameters
        self.battery_capacity_mwh = self.p.get('battery_capacity_mwh')
        self.battery_capex_per_mwh = self.p.get('battery_capex_per_mwh')
        self.battery_life_years = self.p.get('battery_life_years', 10)
        self.battery_o_and_m_cost_per_mwh_yr = self.p.get('battery_o_and_m_cost_per_mwh_yr')
        self.battery_efficiency = self.p.get('battery_efficiency', 0.85)
        self.battery_annual_cycles = 365 * self.solar_capacity_factor

        # Pricing
        self.electricity_price_peak_usd_per_mwh = self.p.get('electricity_price_peak_usd_per_mwh')
        self.electricity_price_offpeak_usd_per_mwh = self.p.get('electricity_price_offpeak_usd_per_mwh')

        # Economic
        self.project_life_years = int(self.p.get('solar_project_lifetime_years', 25))
        self.discount_rate = self.p.get('discount_rate')
        self.inflation_rate = self.p.get('inflation_rate', 0.0)
        self.solar_annual_om_percent_of_capex = self.p.get('solar_annual_om_percent_of_capex')

        # Outputs
        self.total_capex_usd = 0.0
        self.annual_om_usd_year_1 = 0.0
        self.annual_revenue_usd_year_1 = 0.0
        self.npv = 0.0
        self.lcoe = 0.0

    def calculate_capex_usd(self):
        if self.solar_capex_usd_per_mw is None or self.battery_capex_per_mwh is None or self.inverter_replacement_cost_per_mw is None:
            raise ValueError("Missing CAPEX parameters for PV, battery or initial inverter.")
        pv_capex = self.solar_capex_usd_per_mw * self.installed_capacity_mw
        battery_capex = self.battery_capacity_mwh * self.battery_capex_per_mwh
        initial_inverter_capex = self.inverter_replacement_cost_per_mw * self.installed_capacity_mw
        base_total_capex = pv_capex + battery_capex + initial_inverter_capex
        installation_cost = 0.15 * base_total_capex
        self.total_capex_usd = base_total_capex + installation_cost

    def calculate_annual_om_usd(self):
        om_percentage = self.p.get('solar_annual_om_percent_of_capex', 0.02)
        self.annual_om_usd_year_1 = self.total_capex_usd * om_percentage

    def calculate_energy_mwh_for_year(self, year=1):
        if self.solar_capacity_factor is None:
            raise ValueError("solar_capacity_factor not provided")
        base_annual_energy_mwh = self.installed_capacity_mw * self.hours_per_year * self.solar_capacity_factor
        annual_energy_mwh = base_annual_energy_mwh * ((1 - self.panel_degradation_rate) ** (year - 1))
        return annual_energy_mwh

    def calculate_battery_revenue_usd_for_year(self, year=1):
        price_peak = self.electricity_price_peak_usd_per_mwh
        price_offpeak = self.electricity_price_offpeak_usd_per_mwh
        if price_peak is None or price_offpeak is None:
            return 0.0
        if price_peak <= price_offpeak / self.battery_efficiency:
            return 0.0
        mwh_charged = self.battery_capacity_mwh * self.battery_annual_cycles
        mwh_discharged = mwh_charged * self.battery_efficiency
        revenue = (mwh_discharged * price_peak) - (mwh_charged * price_offpeak)
        return revenue

    def calculate_annual_revenue_usd(self):
        if self.electricity_price_offpeak_usd_per_mwh is None:
            raise ValueError("Off-peak price not provided")
        annual_energy_mwh_year_1 = self.calculate_energy_mwh_for_year(year=1)
        base_pv_revenue = annual_energy_mwh_year_1 * self.electricity_price_offpeak_usd_per_mwh
        battery_revenue = self.calculate_battery_revenue_usd_for_year(year=1)
        self.annual_revenue_usd_year_1 = base_pv_revenue + battery_revenue

    def calculate_npv(self):
        years = self.project_life_years
        discount_rate = self.p.get('discount_rate')
        inflation_rate = self.p.get('inflation_rate')
        if None in [years, discount_rate]:
            raise ValueError("Missing NPV parameters")
        cumulative_pv_flows = 0.0
        for year in range(1, years + 1):
            annual_revenue = (
                self.calculate_energy_mwh_for_year(year) * self.electricity_price_offpeak_usd_per_mwh
            ) + self.calculate_battery_revenue_usd_for_year(year)
            annual_om_cost = self.annual_om_usd_year_1 * ((1 + inflation_rate) ** (year - 1))
            if year % self.inverter_life_years == 0:
                annual_om_cost += self.inverter_replacement_cost_per_mw * self.installed_capacity_mw
            if year % self.battery_life_years == 0:
                annual_om_cost += self.battery_capacity_mwh * self.battery_capex_per_mwh
            annual_net_cash_flow = annual_revenue - annual_om_cost
            discount_factor = (1 + discount_rate) ** year
            cumulative_pv_flows += annual_net_cash_flow / discount_factor
        self.npv = -self.total_capex_usd + cumulative_pv_flows

    def calculate_lcoe(self):
        years = self.project_life_years
        r = self.p.get('discount_rate')
        inflation_rate = self.p.get('inflation_rate')
        if None in [years, r]:
            raise ValueError("Missing LCOE parameters")
        total_discounted_costs = self.total_capex_usd
        total_discounted_energy = 0.0
        for y in range(1, years + 1):
            annual_om_cost = self.annual_om_usd_year_1 * ((1 + inflation_rate) ** (y - 1))
            if y % self.inverter_life_years == 0:
                annual_om_cost += self.inverter_replacement_cost_per_mw * self.installed_capacity_mw
            if y % self.battery_life_years == 0:
                annual_om_cost += self.battery_capacity_mwh * self.battery_capex_per_mwh
            annual_energy_mwh = self.calculate_energy_mwh_for_year(y)
            discount_factor = (1 + r) ** y
            total_discounted_costs += annual_om_cost / discount_factor
            total_discounted_energy += annual_energy_mwh / discount_factor
        self.lcoe = total_discounted_costs / total_discounted_energy if total_discounted_energy > 0 else float('inf')

    def run_all(self):
        self.calculate_capex_usd()
        self.calculate_annual_om_usd()
        self.calculate_annual_revenue_usd()
        self.calculate_lcoe()
        self.calculate_npv()


# =============================================================================
# Cumulative Metrics — mirrors calculate_cumulative_metrics from PDF
# =============================================================================

def calculate_cumulative_metrics(proj_instance, project_type, lifetime_years, inflation_rate, project_parameters):
    cumulative_cost = 0.0
    cumulative_revenue = 0.0
    cumulative_net_profit = 0.0

    cumulative_cost += proj_instance.total_capex_usd

    for y in range(1, lifetime_years + 1):
        annual_om_cost = 0.0
        if isinstance(proj_instance, SolarEconomicsHybrid):
            annual_om_cost = proj_instance.annual_om_usd_year_1 * ((1 + inflation_rate) ** (y - 1))
            if y % proj_instance.inverter_life_years == 0 and y < lifetime_years:
                annual_om_cost += (
                    proj_instance.inverter_replacement_cost_per_mw
                    * proj_instance.installed_capacity_mw
                    * ((1 + inflation_rate) ** (y - 1))
                )
            if y % proj_instance.battery_life_years == 0 and y < lifetime_years:
                annual_om_cost += (
                    proj_instance.battery_capacity_mwh
                    * proj_instance.battery_capex_per_mwh
                    * ((1 + inflation_rate) ** (y - 1))
                )
        else:
            annual_om_cost = proj_instance.annual_om_usd * ((1 + inflation_rate) ** (y - 1))

        annual_fuel_cost = 0.0
        if hasattr(proj_instance, 'annual_fuel_cost_usd'):
            annual_fuel_cost = proj_instance.annual_fuel_cost_usd * ((1 + inflation_rate) ** (y - 1))

        if isinstance(proj_instance, DieselEconomics) and (y > 0 and (y % 10 == 0) and (y < lifetime_years)):
            base_diesel_capex_mw_param = project_parameters['diesel_capex_usd_per_mw']
            diesel_installation_cost_factor = 0.10
            replacement_cost_diesel = (
                base_diesel_capex_mw_param * proj_instance.gross_power_mw
            ) * (1 + diesel_installation_cost_factor) * ((1 + inflation_rate) ** (y - 1))
            annual_om_cost += replacement_cost_diesel

        current_annual_cost = annual_om_cost + annual_fuel_cost

        current_annual_revenue = 0.0
        if isinstance(proj_instance, SolarEconomicsHybrid):
            pv_energy_mwh = proj_instance.calculate_energy_mwh_for_year(y)
            pv_revenue = pv_energy_mwh * proj_instance.electricity_price_offpeak_usd_per_mwh
            battery_revenue = proj_instance.calculate_battery_revenue_usd_for_year(y)
            current_annual_revenue = pv_revenue + battery_revenue
        else:
            current_annual_revenue = proj_instance.annual_revenue_usd * ((1 + inflation_rate) ** (y - 1))

        current_annual_net_profit = current_annual_revenue - current_annual_cost

        cumulative_cost += current_annual_cost
        cumulative_revenue += current_annual_revenue
        cumulative_net_profit += current_annual_net_profit

    return cumulative_cost, cumulative_revenue, cumulative_net_profit


# =============================================================================
# Master Runner — runs the entire PDF pipeline and returns all results
# =============================================================================

def run_full_analysis(params):
    """
    Accepts a PROJECT_PARAMETERS dict, runs the full PDF pipeline,
    and returns a dict of all results needed for display.
    """

    # Step 1: Geothermal config
    temp_geo_config = GeothermalEconomicsConfig(
        flowrate_bpd=params['geothermal_flowrate_bpd'],
        production_temperature=params['geothermal_production_temperature_c'],
        injection_temperature=params['geothermal_injection_temperature_c'],
        conversion_efficiency=params['geothermal_conversion_efficiency']
    )
    temp_geo_config.calculate_thermal_power_mw()
    temp_geo_config.calculate_gross_electric_output_mw()
    temp_geo_config.calculate_net_electric_output_mw(params['geothermal_aux_consumption_fraction'])

    geothermal_params_base = {
        'power_plant_capex_usd_per_mw': params['geothermal_capex_usd_per_mw'],
        'annual_om_percent_of_capex': params['geothermal_annual_om_percent_of_capex'],
        'electricity_price_usd_per_mwh': params['electricity_price_usd_per_mwh'],
        'project_lifetime_years': params['geothermal_project_lifetime_years'],
        'discount_rate': params['discount_rate'],
        'inflation_rate': params['inflation_rate'],
        'aux_consumption_fraction': params['geothermal_aux_consumption_fraction'],
        'geothermal_capacity_factor': params['geothermal_capacity_factor'],
    }

    base_gross_power_mw = temp_geo_config.gross_electric_output_mw
    if base_gross_power_mw is None:
        base_gross_power_mw = 0.169

    geo_proj = GeothermalEconomics(geothermal_params_base, base_gross_power_mw, params['hours_per_year'])
    geo_proj.run_all()

    total_energy_geo_gwh_target = (
        geo_proj.net_power_mw
        * params['geothermal_capacity_factor']
        * params['hours_per_year']
        * params['geothermal_project_lifetime_years']
    ) / 1000

    # Step 2: Diesel sizing
    diesel_aux = params.get('diesel_aux_consumption_fraction', 0.0)
    required_diesel_net_mw = total_energy_geo_gwh_target * 1000 / (
        params['hours_per_year'] * params['diesel_project_lifetime_years']
    )
    required_diesel_gross_mw = required_diesel_net_mw / (1 - diesel_aux)

    # Step 2: Solar sizing
    temp_solar_params = {
        'solar_capacity_factor': params['solar_capacity_factor'],
        'panel_degradation_rate': params['panel_degradation_rate'],
        'solar_project_lifetime_years': params['solar_project_lifetime_years'],
    }
    dummy_solar = SolarEconomicsHybrid(temp_solar_params, gross_power_mw=1.0, hours_per_year=params['hours_per_year'])
    solar_energy_per_mw_mwh = 0
    for y in range(1, params['solar_project_lifetime_years'] + 1):
        solar_energy_per_mw_mwh += dummy_solar.calculate_energy_mwh_for_year(y)
    required_solar_gross_mw = total_energy_geo_gwh_target * 1000 / solar_energy_per_mw_mwh

    # Step 3: Instantiate all projects
    # Geothermal already done above

    diesel_params = {
        'capital_cost_usd_per_mw': params['diesel_capex_usd_per_mw'],
        'annual_om_percent_of_capex': params['diesel_annual_om_percent_of_capex'],
        'fuel_cost_usd_per_liter': params['diesel_fuel_cost_usd_per_liter'],
        'diesel_sfc_l_per_kwh': params['diesel_sfc_l_per_kwh'],
        'electricity_price_usd_per_mwh': params['electricity_price_usd_per_mwh'],
        'project_lifetime_years': params['diesel_project_lifetime_years'],
        'discount_rate': params['discount_rate'],
        'inflation_rate': params['inflation_rate'],
        'aux_consumption_fraction': diesel_aux,
    }
    diesel_proj = DieselEconomics(diesel_params, required_diesel_gross_mw, params['hours_per_year'])
    diesel_proj.run_all()

    solar_params = {
        'solar_capex_usd_per_mw': params['solar_capex_usd_per_mw'],
        'solar_annual_om_percent_of_capex': params['solar_annual_om_percent_of_capex'],
        'electricity_price_usd_per_mwh': params['electricity_price_usd_per_mwh'],
        'solar_project_lifetime_years': params['solar_project_lifetime_years'],
        'discount_rate': params['discount_rate'],
        'inflation_rate': params['inflation_rate'],
        'solar_capacity_factor': params['solar_capacity_factor'],
        'panel_degradation_rate': params['panel_degradation_rate'],
        'inverter_life_years': params['inverter_life_years'],
        'inverter_replacement_cost_per_mw': params['inverter_replacement_cost_per_mw'],
        'installed_solar_capacity_mw': required_solar_gross_mw,
        'battery_capacity_mwh': required_solar_gross_mw * params['battery_capacity_mwh_per_mw_pv'],
        'battery_capex_per_mwh': params['battery_capex_per_mwh'],
        'battery_life_years': params['battery_life_years'],
        'battery_o_and_m_cost_per_mwh_yr': params['battery_o_and_m_cost_per_mwh_yr'],
        'electricity_price_offpeak_usd_per_mwh': params['electricity_price_usd_per_mwh'],
        'electricity_price_peak_usd_per_mwh': params['electricity_price_usd_per_mwh'],
        'battery_annual_cycles': params['battery_annual_cycles'],
        'battery_efficiency': params['battery_efficiency'],
    }
    solar_proj = SolarEconomicsHybrid(solar_params, required_solar_gross_mw, params['hours_per_year'])
    solar_proj.run_all()

    # Step 4-5: Cumulative metrics
    inflation_rate = params['inflation_rate']

    geo_cum_cost, geo_cum_rev, geo_cum_profit = calculate_cumulative_metrics(
        geo_proj, 'Geothermal', params['geothermal_project_lifetime_years'], inflation_rate, params
    )
    diesel_cum_cost, diesel_cum_rev, diesel_cum_profit = calculate_cumulative_metrics(
        diesel_proj, 'Diesel', params['diesel_project_lifetime_years'], inflation_rate, params
    )
    solar_cum_cost, solar_cum_rev, solar_cum_profit = calculate_cumulative_metrics(
        solar_proj, 'Solar', params['solar_project_lifetime_years'], inflation_rate, params
    )

    # Build result dict
    results = {
        # Config outputs
        'thermal_power_mw': temp_geo_config.thermal_power_mw,
        'gross_electric_mw': temp_geo_config.gross_electric_output_mw,
        'net_electric_mw': temp_geo_config.net_electric_output_mw,
        'flowrate_kgs': temp_geo_config.flowrate_kgs,
        'total_energy_gwh': total_energy_geo_gwh_target,

        # Gross power
        'geo_gross_mw': base_gross_power_mw,
        'diesel_gross_mw': required_diesel_gross_mw,
        'solar_gross_mw': required_solar_gross_mw,

        # CAPEX
        'geo_capex': geo_proj.total_capex_usd,
        'diesel_capex': diesel_proj.total_capex_usd,
        'solar_capex': solar_proj.total_capex_usd,

        # Cumulative
        'geo_cum_cost': geo_cum_cost,
        'diesel_cum_cost': diesel_cum_cost,
        'solar_cum_cost': solar_cum_cost,
        'geo_cum_profit': geo_cum_profit,
        'diesel_cum_profit': diesel_cum_profit,
        'solar_cum_profit': solar_cum_profit,

        # NPV / LCOE
        'geo_npv': geo_proj.npv,
        'diesel_npv': diesel_proj.npv,
        'solar_npv': solar_proj.npv,
        'geo_lcoe': geo_proj.lcoe,
        'diesel_lcoe': diesel_proj.lcoe,
        'solar_lcoe': solar_proj.lcoe,

        # Project instances (for yearly charts)
        'geo_proj': geo_proj,
        'diesel_proj': diesel_proj,
        'solar_proj': solar_proj,
    }
    return results