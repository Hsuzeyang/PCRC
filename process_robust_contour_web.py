import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO, StringIO
from PIL import Image

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(page_title="工艺稳健性 Contour Plot (Low-Volume Capability)", layout="wide")
plt.rcParams["axes.unicode_minus"] = False

# -------------------------- 侧边栏参数控制面板 --------------------------
with st.sidebar:
    st.header("工艺参数配置面板")
    st.subheader("因子1 (X轴)")
    p1_min = st.number_input("下限", value=80.0)
    p1_max = st.number_input("上限", value=120.0)

    st.subheader("因子2 (Y轴)")
    p2_min = st.number_input("下限", value=20.0)
    p2_max = st.number_input("上限", value=60.0)

    st.subheader("产品规格限")
    LSL = st.number_input("LSL 下限", value=10.0)
    USL = st.number_input("USL 上限", value=30.0)

    st.subheader("响应模型系数 mu = a*x1 + b*x2 + c*x1*x2")
    a_coef = st.number_input("x1系数 a", value=0.22)
    b_coef = st.number_input("x2系数 b", value=0.45)
    c_coef = st.number_input("交互项 c", value=-0.0018)

    st.subheader("标准差波动模型 sigma")
    sig_base = st.number_input("基础波动", value=1.2)
    sig_x1 = st.number_input("x1波动系数", value=0.003)
    sig_x2 = st.number_input("x2波动系数", value=0.008)

    grid_res = st.slider("网格精度", min_value=50, max_value=200, value=120, step=10)

# -------------------------- 生成网格 & 计算Cpk --------------------------
# 网格矩阵
x1 = np.linspace(p1_min, p1_max, grid_res)
x2 = np.linspace(p2_min, p2_max, grid_res)
X1, X2 = np.meshgrid(x1, x2)

# 均值响应
mu = a_coef * X1 + b_coef * X2 + c_coef * X1 * X2
# 小批量标准差
sigma = sig_base + sig_x1 * np.abs(X1 - (p1_min+p1_max)/2) + sig_x2 * np.abs(X2 - (p2_min+p2_max)/2)
sigma = np.where(sigma < 1e-6, 1e-6, sigma)

# 工艺能力Cpk
cpk_low = (mu - LSL) / (3 * sigma)
cpk_high = (USL - mu) / (3 * sigma)
Z_cpk = np.minimum(cpk_low, cpk_high)
Z_cpk = np.where(Z_cpk < 0, 0, Z_cpk)

# -------------------------- 绘制等高线图 --------------------------
fig, ax = plt.subplots(figsize=(10, 7), dpi=120)
levels_fill = [0, 0.67, 1.0, 1.33, 1.67, 2.0, 3.0]
contour_fill = ax.contourf(X1, X2, Z_cpk, levels=levels_fill, cmap="RdYlGn", alpha=0.8)

# 标注等高线
line_levels = [1.33, 1.67, 2.0]
cnt_lines = ax.contour(X1, X2, Z_cpk, levels=line_levels, colors="black", linewidths=1)
ax.clabel(cnt_lines, inline=True, fontsize=9, fmt="%.2f")

# Cpk=1.33 合格分界线
ax.contour(X1, X2, Z_cpk, levels=[1.33], colors="darkblue", linewidths=2, linestyles="--")

# 图表标签
cbar = fig.colorbar(contour_fill, ax=ax)
cbar.set_label("Process Capability Cpk (工艺稳健性)", fontsize=11)
ax.set_xlabel("Process Factor 1", fontsize=11)
ax.set_ylabel("Process Factor 2", fontsize=11)
ax.set_title("Contour Plot of Process Robustness\nLow-Volume Manufacturing Process Capability Estimation", fontsize=12)
ax.grid(alpha=0.3)
plt.tight_layout()

# -------------------------- 网页展示 & 导出功能 --------------------------
st.title("工艺稳健性等高线在线分析工具")
st.markdown("文献依据：*Estimating process capability in development and for low-volume manufacturing*")
st.pyplot(fig)

# 导出高清图片
buf = BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
buf.seek(0)
img = Image.open(buf)
st.download_button(
    label="下载300DPI高清Contour图",
    data=buf,
    file_name="Process_Robustness_Cpk_Contour.png",
    mime="image/png"
)

# 说明文本
st.subheader("图表解读说明")
st.markdown("""
1. 蓝色虚线：Cpk=1.33 工艺稳健合格阈值；
2. 绿色区域：Cpk≥1.33，工艺窗口稳定、抗波动强；
3. 红黄区域：Cpk＜1.33，小批量生产易出现超规格风险；
4. 等高线越密集：参数敏感，微小波动即大幅降低工艺能力；
5. 适配研发阶段、小批量试制无大量历史数据的工艺能力评估。
""")