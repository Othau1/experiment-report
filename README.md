# experiment-report · 实验报告生成 Skill

一个 Claude Code skill：根据实验资料，自动生成一份**简练、规范**的大学实验报告，最终**只输出一个 PDF**。

## 它能做什么

读入实验内容文件（`.docx` / `.pdf` / `.txt` / `.md` / 图片），按标准七段结构生成报告：

1. 实验名称、实验者姓名、同组者姓名、实验日期
2. 实验目的
3. 实验原理
4. 实验方法或步骤
5. 数据记录及其说明
6. 数据处理及实验结果
7. 实验讨论

**排版巧思（让报告更用心、篇幅更足）**：封面页（课程名 + 大字标题）、页眉页脚、摘要/关键词灰底框、公式右对齐编号、注意事项黄底框、参考文献悬挂缩进、表格隔行底纹、误差分析小节。

**核心原则**：资料里没有的信息（姓名、日期、实测数据、个人体会等）一律**留空**（渲染成灰色提示 + 下划线），绝不编造，也**不反问用户**。最终只留一个 PDF。

## 依赖

- Python（用 `py` 启动器）
- `reportlab`（生成 PDF）：`py -m pip install reportlab`
- `python-docx`（读 .docx）、`matplotlib`（可选，画实验曲线）
- 中文字体直接用系统自带的宋体 / 黑体 / 楷体 / 仿宋，无需配置

## 安装

把本目录复制到用户级 skills 目录即可全局可用：

```
cp -r . ~/.claude/skills/experiment-report
```

（Windows 下即 `C:\Users\<你>\.claude\skills\experiment-report`。）

安装后，直接对 Claude 说「帮我写这份实验报告」并附上实验资料文件即可触发。

## 目录结构

```
experiment-report/
├── SKILL.md                 # skill 定义与使用说明
├── scripts/
│   └── make_report.py       # 读 JSON → 生成 PDF
└── example/
    ├── example_report.json  # 输入示例
    └── example_report.pdf   # 输出示例
```

## 手动生成

```bash
py scripts/make_report.py example/example_report.json 输出.pdf
```

`make_report.py` 的输入 JSON 结构见 `SKILL.md` 中的说明与 `example/example_report.json`。
