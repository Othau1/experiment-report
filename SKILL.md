---
name: experiment-report
description: 根据用户提供的实验资料，生成一份完整、规范、排版用心（含封面、摘要、公式编号、注意事项框、参考文献等）的大学实验报告，最终只输出一个 PDF 文件。当用户要求「写实验报告 / 生成实验报告 / 做实验报告 / 整理实验报告」时使用。
---

# 实验报告生成

把用户给的实验资料整理成一份**完整、规范、简练（无废话）**且**排版用心**的实验报告，最终**只输出一个 PDF**。

## 工作流程

1. **读取资料**：用户会给一份实验内容文件（`.docx` / `.pdf` / `.txt` / `.md` / 图片等）。`.docx` 用 `python-docx`，`.pdf` 用 PyMuPDF，图片若无 OCR 能力可用 Windows 自带 OCR（`Windows.Media.Ocr`，见下文「图片 OCR」）。
2. **按结构组织内容**（封面 → 摘要 → 七段正文 → 参考文献），把能写的内容写全、写准。
3. **写中间 JSON**：写入 `report.json`（结构见下）。
4. **生成 PDF**：`py scripts/make_report.py report.json 实验报告.pdf`
5. **清理**：删除中间文件，**只保留 PDF**，输出 PDF 路径。

## 报告结构（按此顺序）

- **封面页**：课程名（`course`）+ 大字标题 + 信息栏（姓名/同组/日期/指导教师，缺省留空）。
- **摘要与关键词**：`abstract` + `keywords`，灰底框显示。
- **七段正文**：
  1. 实验目的
  2. 实验原理（比预习详尽，含公式推导，不照抄教材）
  3. 实验方法或步骤（实际操作）
  4. 数据记录及其说明（详尽、注明单位、含常数）
  5. 数据处理及实验结果（计算、曲线、误差/不确定度分析、最终结果）
  6. 实验讨论
- **参考文献**：`references` 数组。

## 关键原则

- **不要询问用户实验的具体现象/数据。** 资料里没有的信息一律「留空」（渲染成灰色提示 + 下划线），不要反问、不要编造。
- **留空而非编造**：姓名、日期、实测数据、个人体会等，凡资料未给出的都留空。
- **简练**：去掉套话，每句都有信息量。
- **只输出 PDF**：最终只留一个 PDF。

## JSON 结构

```json
{
  "title": "声速的测量",
  "course": "大学物理实验",
  "meta": {"实验者姓名": "", "同组者姓名": "", "实验日期": "", "指导教师": ""},
  "abstract": "本实验采用……测量了……",
  "keywords": ["声速", "驻波", "相位比较", "时差法"],
  "sections": [
    {"heading": "一、实验目的", "blocks": [
      {"type": "ul", "items": ["…", "…"]}
    ]},
    {"heading": "二、实验原理", "blocks": [
      {"type": "subheading", "text": "1. 共振干涉（驻波）法"},
      {"type": "p", "text": "…"},
      {"type": "formula", "text": "v = λf", "num": "1"}
    ]}
  ],
  "references": ["[1] 张三. 大学物理实验. 北京: 高等教育出版社, 2020."]
}
```

`course`、`abstract`、`keywords`、`references` 均可省略；`meta` 里的 `指导教师` 也可省略。

**block 类型**（`sections[].blocks` 中每个元素）：

| type | 字段 | 说明 |
|------|------|------|
| `p` | `text` | 段落，支持 `<b>` `<i>` `<sub>` `<super>` |
| `subheading` | `text` | 小节标题（黑体，如「1. 共振干涉法」） |
| `ul` | `items` | 无序列表 |
| `ol` | `items` | 有序列表 |
| `formula` | `text`, `num` | 居中公式；`num` 可选，右对齐编号（如 "1"） |
| `table` | `headers`, `rows` | 表格（`headers` 可选），自动隔行浅色底纹 |
| `figure` | `path`, `caption` | 图片（先生成 PNG 再引用） |
| `note` | `title`, `text` | 黄底提示框（如「注意事项」） |
| `blank` | `label`, `hint` | 留空占位，灰字提示 + 下划线 |
| `spacer` | `height` | 垂直留白（pt） |

## 文本标记与转义

- 加粗 `<b>…</b>`、斜体 `<i>…</i>`、下标 `<sub>…</sub>`、上标 `<super>…</super>`（正文块与表格单元格有效）。
- 上下标一律用 `<sub>`/`<super>`（`m/s<super>2</super>`、`g<sub>0</sub>`）；Unicode 只有 `² ³ ¹` 在宋体可用，`⁰ ₀ ₁ ₂` 会缺字，别用。
- 字面「小于 / 大于」用**全角** `＜` `＞`，不要用 `&lt;`/`&gt;`。
- `&` 会被自动转义，无需手动处理。

## 让报告更用心 / 篇幅更足（排版与内容技巧）

默认已内置这些排版巧思，直接使用即可；需要更「长」时按需加内容：

**排版（已内置）**
- 封面页：`course`（课程名）+ 大字拉宽标题，独立成页。
- 页眉：从第 2 页起每页顶部显示实验名 + 细横线；页脚页码。
- 摘要/关键词灰底框、注意事项黄底框。
- 公式右对齐编号、表格表头底纹 + 隔行浅色、参考文献悬挂缩进。

**内容（让报告更长更扎实）**
- 加 `abstract`/`keywords`（150 字左右摘要）。
- 原理部分写**公式推导**（从基本关系逐步推出测量公式），并给公式编号 `num`。
- 数据处理里加「误差/不确定度分析」小节（系统误差、偶然误差、不确定度传递）。
- 实验讨论里可写误差来源、改进建议、个人体会（没有就留空）。
- 加 `references`（教材、讲义等）。

## 实验曲线（如需要）

有坐标数据、需画曲线时，先用 matplotlib 生成 PNG（中文字体 `SimHei`），再用 `figure` 块引用：

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

## 图片 OCR（读实验资料图片时）

本环境无独立 OCR 库时，可用 Windows 自带 OCR（无需安装，支持中文）。要点：
1. 长图先切片（`PIL` 按高 ~2000px 重叠切），否则单次识别效果差。
2. PowerShell 调 `Windows.Media.Ocr`，语言 `zh-Hans-CN`；`.ps1` 用纯 ASCII 路径（中文路径会被 GBK 误读）。
3. 公式、下标 OCR 常会乱码，需结合物理常识还原。

## 依赖

- Python（`py` 启动器）：`reportlab`、`python-docx`、`matplotlib`（可选）、`Pillow`（图片切片用）。
- `reportlab` 未安装时：`py -m pip install reportlab`。
- 中文字体用系统自带（宋体/黑体/楷体/仿宋），无需配置。
