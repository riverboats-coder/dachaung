# htgr_4e/environmental.py
"""
高温气冷堆-sCO2系统 全生命周期温室气体排放分析模块
基于论文 Table 5 和 Appendix B
"""

class EnvironmentalAnalyzer:
    """环境分析器"""

    def __init__(self, W_net_kw, tau=8000, n=30):
        """
        初始化环境分析器
        :param W_net_kw: 系统净输出电功率 (kW)，来自热力学模拟
        :param tau: 年运行小时数 (h)，默认 8000
        :param n: 电站寿命 (年)，默认 30
        """
        self.W_net = W_net_kw
        self.tau = tau
        self.n = n
        self.annual_energy = W_net_kw * tau
        self.lifetime_energy = self.annual_energy * n

        # 石墨生产排放因子 (Table B1)
        self.CO2_per_g = 7.75
        self.CH4_per_g = 1.44e-4
        self.N2O_per_g = 1.45e-4

        # 全球增温潜势 (GWP)
        self.GWP_CH4 = 25
        self.GWP_N2O = 298

    def _graphite_factor(self):
        """计算每克石墨产生的 CO2 当量 (g CO2eq / g 石墨)"""
        return self.CO2_per_g + self.CH4_per_g * self.GWP_CH4 + self.N2O_per_g * self.GWP_N2O

    def _fuel_balls_emission(self):
        """燃料球制造中的石墨消耗排放 (g CO2eq / kWh)"""
        balls_per_year = 130000
        mass_per_ball = 208  # g
        graphite_frac = 0.97
        annual_graphite_kg = balls_per_year * mass_per_ball * graphite_frac  # g/year
        annual_emission = annual_graphite_kg * self._graphite_factor()       # g CO2eq / year
        return annual_emission / self.annual_energy

    def _core_graphite_emission(self):
        """堆芯结构（500吨石墨）建设排放 (g CO2eq / kWh)"""
        total_graphite_g = 500_000_000  # 500吨 = 5亿克
        total_emission = total_graphite_g * self._graphite_factor()
        return total_emission / self.lifetime_energy

    def get_emission_intensity(self):
        """
        获取综合 GHG 排放强度 (g CO2eq / kWh)
        包含：铀生产、燃料制造、电厂建设、运行、乏燃料、废物管理
        """
        # 固定常数项 (已按表5累加)
        fixed = 3.559 + 0.21 + 0.451 + 0.00788 + 1.021

        # 乏燃料后处理 (基于1000 MWe基准折算)
        spent_fuel = 5.29 * 250 / (1000 / 0.3)

        # 废物管理
        waste = 0.433

        # 石墨相关项
        fuel_balls = self._fuel_balls_emission()
        core_graphite = self._core_graphite_emission()

        return fixed + spent_fuel + waste + fuel_balls + core_graphite

    def get_total_emission(self, unit='kg'):
        """
        获取全生命周期总排放量
        :param unit: 'kg' 或 'ton'
        :return: float
        """
        intensity_g_per_kwh = self.get_emission_intensity()
        total_g = intensity_g_per_kwh * self.lifetime_energy
        if unit == 'kg':
            return total_g / 1000
        elif unit == 'ton':
            return total_g / 1_000_000
        else:
            return total_g