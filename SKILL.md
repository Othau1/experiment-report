---
name: experiment-report
description: 根据用户提供的实验资料，生成一份简练、符合规范（含实验目的/原理/步骤/数据记录/数据处理/讨论等部分）的大学实验报告，最终只输出一个 PDF 文件。当用户要求「写实验报告 / 生成实验报告 / 做实验报告 / 整理实验报告」时使用。
---

# 实验报告生成

把用户给的实验资料整理成一份**完整、规范、简练（无废话）**的实验报告，最终**只输出一个 PDF**。

## 工作流程

1. **读取资料**：用户会给一份实验内容文件（可能是 `.docx` / `.pdf` / `.txt` / `.md` / 图片等）。先用合适的方式提取其中的文字与数据（`.docx` 用 `python-docx`，`.pdf` 用 PyMuPDF 等；`.txt`/`.md` 直接读；图片用 Read 工具查看）。
2. **按七段结构组织内容**（见下方模板），把能写的内容写全、写准。
3. **写中间 JSON**：把组织好的内容写入一个 `report.json`（结构见 `example/example_report.json`）。
4. **生成 PDF**：运行
   ```
   py scripts/make_report.py report.json 实验报告.pdf
   ```
5. **清理**：删除中间文件（`report.json` 等），**只保留 PDF**。输出 PDF 的路径即可。

## 报告结构（务必按此顺序）

1. **实验名称、实验者姓名、同组者姓名、实验日期** —— 名称作标题；姓名/同组/日期若有则填，没有就留空。
2. **实验目的** —— 简洁列点。
3. **实验原理** —— 比预习报告更详尽，但**不要照抄教材**，用概括性语言+关键公式。公式用 Unicode 符号（如 `T = 2π√(L/g)`、`μ`、`Δ`、`σ`），上下标用 `<sub>`/`<super>`。
4. **实验方法或步骤** —— 写**实际操作**情况（而非照搬预习），可列步骤。
5. **数据记录及其说明** —— 数据尽量详尽、**注明单位**，含有关常数（如重力加速度标准值、室温等）。有表格就放表格，没数据就留空。
6. **数据处理及实验结果** —— 计算过程、实验曲线（可用 matplotlib 出图后用 `figure` 块引用）、表格、可信程度分析、最终结果。
7. **实验讨论** —— 误差来源、改进建议、个人体会等。

## 关键原则

- **不要询问用户实验的具体现象/数据。** 资料里没有的信息一律「留空」，用 `blank` 块（渲染成灰色提示 + 下划线），**不要**反过来问用户，也不要编造。
- **留空而非编造**：实验者姓名、同组者姓名、实验日期、实际测量数据、用户自己的观察与体会等，凡资料中未给出的，都留空。
- **简练**：去掉套话、空话；每句话都有信息量。
- **只输出 PDF**：最终目录里只留一个 PDF，中间文件删掉。

## JSON 结构

```json
{
  "title": "实验名称",
  "meta": {"实验者姓名": "", "同组者姓名": "", "实验日期": ""},
  "sections": [
    {"heading": "一、实验目的", "blocks": [
      {"type": "p", "text": "..."},
      {"type": "ul", "items": ["...", "..."]}
    ]},
    {"heading": "二、实验原理", "blocks": [
      {"type": "p", "text": "..."},
      {"type": "formula", "text": "T = 2π√(L/g)"}
    ]}
  ]
}
```

**block 类型**（`blocks` 数组里每个元素是一个 block）：

| type | 字段 | 说明 |
|------|------|------|
| `p` | `text` | 段落，支持 `<b>` `<i>` `<sub>` `<super>` 标记 |
| `ul` | `items` | 无序列表 |
| `ol` | `items` | 有序列表 |
| `formula` | `text` | 居中公式，支持 `<sub>` `<super>` |
| `table` | `headers`, `rows` | 表格（`headers` 可选） |
| `figure` | `path`, `caption` | 图片（先单独生成 PNG 再引用） |
| `blank` | `label`, `hint` | 留空占位，`label` 是待填内容名，`hint` 是灰色补充说明 |

## 文本标记与转义

- 加粗 `<b>…</b>`、斜体 `<i>…</i>`、下标 `<sub>…</sub>`、上标 `<super>…</super>`（正文块和表格单元格都有效）。
- 上下标一律用 `<sub>`/`<super>` 标记（如 `m/s<super>2</super>`、`g<sub>0</sub>`）。Unicode 里只有 `² ³ ¹` 在宋体中可用，`⁰ ₀ ₁ ₂` 等会缺字，别用。
- 字面「小于 / 大于」一律用**全角** `＜` `＞`（如 `θ ＜ 5°`），不要用 `&lt;`/`&gt;`。
- 文本里的 `&` 会被自动转义，无需手动处理。

## 实验曲线（如需要）

数据里有坐标数据、需要画曲线时，先用 matplotlib 生成 PNG（中文字体用 `SimHei`），再在 JSON 里用 `figure` 块引用。例如：

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.plot(x, y, "o-")
plt.xlabel("L / m"); plt.ylabel("T / s")
plt.savefig("curve.png", dpi=150)
```

## 依赖

- Python（用 `py` 启动器）：`reportlab`、`python-docx`、`matplotlib`（可选，画曲线用）。
- 若 `reportlab` 未安装：`py -m pip install reportlab`。
- 中文字体直接用系统自带（宋体/黑体/楷体/仿宋），无需额外配置。
