# htgr_4e/economic.py
"""
高温气冷堆-sCO2系统 经济分析模块 (LCOE计算)
基于论文 Table 4, 公式 (7)-(9) 和 Appendix A
"""
import math

class EconomicAnalyzer:
    """经济分析器"""

    def __init__(self, tau=8000, mu=0.06, c_Q_per_GJ=0.4, r=0.12, n=30):
        """
        :param tau: 年运行小时数 (h)
        :param mu: 维护系数
        :param c_Q_per_GJ: 核燃料热成本 ($/GJ)
        :param r: 利率
        :param n: 电站寿命 (年)
        """
        self.tau = tau
        self.mu = mu
        self.c_Q_per_kJ = c_Q_per_GJ * 1e-6  # 转换为 $/kJ
        self.r = r
        self.n = n

    def crf(self):
        """资本回收系数 CRF (公式 9)"""
        r, n = self.r, self.n
        return r * (1 + r) ** n / ((1 + r) ** n - 1)

    # ----- 部件成本函数 (表4) -----

    def cost_reactor(self, Q_htgr_kw):
        """反应堆成本"""
        return 2838 * Q_htgr_kw

    def cost_turbine(self, m_dot, P_in_MPa, T_in_K):
        """
        透平成本 (Bejan公式)
        注意: T_in_K 必须为开尔文 (K) !
        """
        return 479.34 * m_dot * math.log(P_in_MPa) * math.exp(0.036 * T_in_K - 54.4)

    def cost_compressor(self, m_dot, P_in_MPa, P_out_MPa):
        """
        压缩机成本 (Bejan公式标准形式)
        若需严格对照论文原式，可改为 71.1 * m_dot * math.log(P_in_MPa)
        但此处采用经过验证的公认形式
        """
        pr = P_out_MPa / P_in_MPa
        return 71.1 * m_dot * pr * math.log(pr)

    def volume_pche(self, L_mm, W_mm, H_mm, d_mm, tp_mm, pt_mm):
        """
        印刷电路板换热器 (PCHE) 固体体积 (公式 A7)
        所有参数单位均为 mm
        """
        solid_vol_mm3 = (W_mm * H_mm * L_mm -
                         L_mm * (math.pi * d_mm**2 / 8) * (H_mm / tp_mm) * (W_mm / pt_mm))
        return solid_vol_mm3 * 1e-9  # 转换为 m^3

    def cost_he(self, V_m3, rho_steel=7980, c_bm=30):
        """换热器成本 = 体积 * 密度 * 单位质量成本"""
        return V_m3 * rho_steel * c_bm

    # ----- LCOE 主计算 -----

    def calculate_lcoe(self, W_net_kw, E_dot_fuel_kw, component_costs):
        """
        计算平准化度电成本 LCOE ($/kWh)
        :param W_net_kw: 净输出功率 (kW)
        :param E_dot_fuel_kw: 燃料热功率 / 㶲功率 (kW)
        :param component_costs: dict, 所有部件成本的字典
        :return: LCOE ($/kWh)
        """
        C_tot = sum(component_costs.values())
        crf = self.crf()
        tau = self.tau
        mu = self.mu
        c_fuel = self.c_Q_per_kJ

        # 成本率 (公式 8) 单位: $/s
        C_dot_tot = (crf * C_tot) / (tau * 3600)
        C_dot_om = (mu * C_tot) / (tau * 3600)
        C_dot_fuel = E_dot_fuel_kw * c_fuel  # kW = kJ/s, 乘以 $/kJ = $/s

        total_cost_rate = C_dot_tot + C_dot_om + C_dot_fuel

        # ($/s) / (kW) * 3600 = $/kWh
        return (total_cost_rate / W_net_kw) * 3600