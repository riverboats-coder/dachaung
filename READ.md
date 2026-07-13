HTGR-sCO₂ 4E分析本地包使用文档
版本：1.0
适用范围：基于论文 Thermo-economic and environmental analyses of supercritical carbon dioxide Brayton cycle for high temperature gas-cooled reactor (Zhou et al., 2024) 的经济（Economic）与环境（Environmental）模块复现。

1. 包结构
将以下文件放在项目目录下的 htgr_4e 文件夹中，确保 main_analysis.py 与 htgr_4e 同级：

text
your_project/
│
├── htgr_4e/                    # 本地包 (Local Package)
│   ├── __init__.py             # 包初始化文件
│   ├── environmental.py        # 环境分析模块
│   └── economic.py             # 经济分析模块
│
└── main_analysis.py            # 你的主调用程序
2. 环境分析模块 (environmental.py)
该模块用于计算系统全生命周期温室气体（GHG）排放强度及总量。

2.1 类：EnvironmentalAnalyzer
初始化参数
参数名	类型	单位	说明	默认值
W_net_kw	float	kW	系统净输出电功率（由热力学模拟提供）	必填
tau	int	h	年运行小时数	8000
n	int	年	电站设计寿命	30
主要方法
方法名	返回值	说明
get_emission_intensity()	float	返回排放强度，单位 g CO₂eq / kWh（基准工况下约 6.5）
get_total_emission(unit='kg')	float	返回全生命周期总排放量。unit 可选 'kg' 或 'ton'
3. 经济分析模块 (economic.py)
该模块用于计算系统各部件的固定投资成本及平准化度电成本（LCOE）。

3.1 类：EconomicAnalyzer
初始化参数
参数名	类型	单位	说明	默认值
tau	int	h	年运行小时数	8000
mu	float	-	运维费率（取设备投资比例）	0.06
c_Q_per_GJ	float	$/GJ	核燃料热成本	0.4
r	float	-	年利率	0.12
n	int	年	电站寿命	30
部件成本计算方法（需热力学数据输入）
方法名	对应部件	关键输入参数（单位）	公式来源
cost_reactor(Q)	反应堆	Q：热功率 (kW)	表4
cost_turbine(m, P, T)	透平	m：流量 (kg/s)
P：进口压力 (MPa)
T：进口温度 (K)	Bejan公式
cost_compressor(m, P_in, P_out)	压缩机	m：流量 (kg/s)
P_in：进口压力 (MPa)
P_out：出口压力 (MPa)	Bejan公式（标准修正版）
volume_pche(L, W, H, d, tp, pt)	PCHE换热器体积	全部为几何尺寸 (mm)	附录A 公式(A7)
cost_he(V)	换热器成本	V：体积 (m³)	表4（密度×单价）
LCOE主计算方法
方法名	返回值	说明
calculate_lcoe(W_net_kw, E_dot_fuel_kw, component_costs)	float	返回 $/kWh。内部自动调用 CRF 并汇总成本率。
参数详解：

W_net_kw：净输出功率 (kW)。

E_dot_fuel_kw：燃料热功率/㶲功率 (kW)，通常等于反应堆热功率。

component_costs：字典 (dict)，包含所有部件的成本（$），例如：

python
{
  'reactor': 1200000,
  'turbine': 800000,
  'compressor': 350000,
  'he_rhx': 600000,
  'he_htr': 400000,
  'he_ltr': 300000,
  'he_pc': 200000,
}
4. 与热力学队友的数据接口约定
为了保证主程序顺利运行，建议您与负责热力学模拟的同事约定以下数据传递格式（变量名可自行调整，但物理含义必须对应）：

热力学输出变量	符号/单位	用途（对应模块）
net_power	kW	环境分析（排放总量）、经济分析（LCOE分母）
reactor_heat	kW	反应堆成本计算、燃料成本率计算
turbine_m_dot	kg/s	透平成本计算
turbine_P_in	MPa	透平成本计算
turbine_T_in	K (开尔文)	透平成本计算（极易出错！）
compressor_m_dot	kg/s	压缩机成本计算
compressor_P_in / P_out	MPa	压缩机成本计算
he_length (L)	mm	换热器体积计算（若队友已算出体积V，则无需此参数）
其他几何参数（W, H, d, tp, pt）	mm	若使用标准值（见表A1），可直接在代码中写死
5. 完整使用示例（main_analysis.py）
以下代码展示了如何从队友的热力学结果对象中提取数据，调用本包进行4E分析。

python
# main_analysis.py
from htgr_4e import EnvironmentalAnalyzer, EconomicAnalyzer

# =========================================================
# 第一步：模拟接收队友的热力学计算结果
# =========================================================
class ThermodynamicResult:
    """模拟队友返回的热力学数据对象（实际使用时请替换为真实接口）"""
    def __init__(self):
        # 基准工况参数（对应论文R-S系统，仅供参考）
        self.net_power_kw = 250_000.0          # 250 MW
        self.reactor_heat_kw = 580_000.0       # 580 MWth

        # 顶部子循环透平参数
        self.turbine_top_m_dot = 300.0         # kg/s
        self.turbine_top_P_in = 26.0           # MPa
        self.turbine_top_T_in = 873.15         # 600 ℃ -> 必须为 873.15 K

        # 底部子循环压缩机参数
        self.compressor_m_dot = 280.0          # kg/s
        self.compressor_P_in = 7.6             # MPa
        self.compressor_P_out = 26.0           # MPa

        # 换热器几何尺寸（若队友只给了体积V，可直接用V计算成本，跳过体积函数）
        # 此处假设队友提供了RHX的长度（由10℃夹点温差迭代得出）
        self.rhx_L_mm = 2000.0
        self.rhx_W_mm = 200.0
        self.rhx_H_mm = 200.0

# 实例化热力学结果（实际使用时替换为队友程序返回的对象）
result = ThermodynamicResult()

# =========================================================
# 第二步：环境分析 (Environmental)
# =========================================================
env_analyzer = EnvironmentalAnalyzer(W_net_kw=result.net_power_kw)

# 获取排放强度 (g CO2eq / kWh)
emission_intensity = env_analyzer.get_emission_intensity()
# 获取生命周期总排放 (吨)
total_emission_ton = env_analyzer.get_total_emission(unit='ton')

print("========== 环境分析结果 ==========")
print(f"GHG 排放强度: {emission_intensity:.3f} g CO2eq/kWh")
print(f"全生命周期总排放: {total_emission_ton:.2f} 吨 CO2eq")

# =========================================================
# 第三步：经济分析 (Economic)
# =========================================================
eco_analyzer = EconomicAnalyzer()  # 使用默认经济参数

# 3.1 计算各部件固定投资成本
costs = {}

# 反应堆
costs['reactor'] = eco_analyzer.cost_reactor(result.reactor_heat_kw)

# 透平（注意温度单位：K）
costs['turbine'] = eco_analyzer.cost_turbine(
    m_dot=result.turbine_top_m_dot,
    P_in_MPa=result.turbine_top_P_in,
    T_in_K=result.turbine_top_T_in
)

# 压缩机
costs['compressor'] = eco_analyzer.cost_compressor(
    m_dot=result.compressor_m_dot,
    P_in_MPa=result.compressor_P_in,
    P_out_MPa=result.compressor_P_out
)

# 换热器（以RHX为例，查表A1取 d=2.0, tp=2.5, pt=2.4）
# 如果队友给的是体积V，可以跳过volume_pche，直接调用cost_he(V)
vol_rhx = eco_analyzer.volume_pche(
    L_mm=result.rhx_L_mm,
    W_mm=result.rhx_W_mm,
    H_mm=result.rhx_H_mm,
    d_mm=2.0,
    tp_mm=2.5,
    pt_mm=2.4
)
costs['he_rhx'] = eco_analyzer.cost_he(vol_rhx)

# 补充其他换热器（HTR, LTR, PC）...
# costs['he_htr'] = eco_analyzer.cost_he(...)

# 3.2 计算 LCOE
lcoe = eco_analyzer.calculate_lcoe(
    W_net_kw=result.net_power_kw,
    E_dot_fuel_kw=result.reactor_heat_kw,  # 燃料㶲功率近似等于热功率
    component_costs=costs
)

print("\n========== 经济分析结果 ==========")
print(f"固定投资总成本: ${sum(costs.values()):,.2f}")
print(f"平准化度电成本 (LCOE): {lcoe:.5f} $/kWh")

# 预期输出：
# GHG 排放强度 ≈ 6.5 g CO2eq/kWh
# LCOE ≈ 0.0283 ~ 0.0310 $/kWh (取决于具体构型)
6. 重点注意事项（避坑指南）
温度单位（致命错误）：cost_turbine 方法中的 T_in_K 必须是开尔文（K）。如果队友提供的是摄氏度（℃），务必在传入前执行 + 273.15。漏掉这一步会导致 exp(0.036*T) 计算完全失真，LCOE偏大几个数量级。

压缩机成本公式（学术歧义点）：论文原表4中压缩机公式排版疑似有误。本包采用了经过多篇同行文献（Luo et al., 2020）验证的标准Bejan形式，即 71.1 * m * PR * ln(PR)。若您发现复现值与论文偏差较大，可尝试改为 71.1 * m * ln(P_in) 进行对照验证。

换热器体积（L的来源）：换热器的长度 L 不是随便指定的，它必须由热力学模拟程序根据 10℃ 最小夹点温差 和 冷热侧压降（0.05MPa / 0.1MPa） 约束迭代计算得出。如果队友直接提供了换热器的固体体积 V，请直接调用 cost_he(V)，跳过 volume_pche 的几何计算。

单位换算检查：

c_Q_per_GJ 传入的是 $/GJ，内部已自动除以 1e6 转为 $/kJ。

LCOE最终结果的单位是 $/kWh（度电成本），符合国际电力市场常规口径。

如您在实际集成过程中遇到任何键值报错（KeyError）或数值异常，欢迎随时反馈具体的报错堆栈信息。祝您复现顺利！