# -*- coding: utf-8 -*-
"""
实验报告 PDF 生成器。

用法：
    py scripts/make_report.py <input.json> [output.pdf]

输入为 JSON 文件，结构见 example/example_report.json。
依赖：reportlab（中文字体用系统自带的 宋体/黑体/楷体/仿宋）。
"""
import json
import sys
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, KeepTogether)
from reportlab.lib.utils import ImageReader

FONT_DIR = "C:/Windows/Fonts"
PAGE_W, PAGE_H = A4
LEFT = RIGHT = 2.0 * cm
TOP = BOTTOM = 2.5 * cm
USABLE_W = PAGE_W - LEFT - RIGHT

# ---------------------------------------------------------------- 字体注册
_FONT_CANDIDATES = [
    ("SimSun", "simsun.ttc", 0),   # 宋体（正文）
    ("SimHei", "simhei.ttf", None),  # 黑体（标题/加粗）
    ("SimKai", "simkai.ttf", None),  # 楷体
    ("SimFang", "simfang.ttf", None),  # 仿宋
]

for _name, _fn, _sub in _FONT_CANDIDATES:
    _path = os.path.join(FONT_DIR, _fn)
    if os.path.exists(_path):
        try:
            if _sub is not None:
                pdfmetrics.registerFont(TTFont(_name, _path, subfontIndex=_sub))
            else:
                pdfmetrics.registerFont(TTFont(_name, _path))
        except Exception as _e:
            print(f"[warn] 注册字体失败 {_fn}: {_e}", file=sys.stderr)

# 正文字体族：正常用宋体，加粗用黑体
try:
    registerFontFamily("Body", normal="SimSun", bold="SimHei",
                       italic="SimSun", boldItalic="SimHei")
except Exception:
    pass

BODY = "SimSun"
HEI = "SimHei"


def esc_amp(s):
    """转义 & （允许 <b>/<i>/<sub>/<super> 等标记）。"""
    if s is None:
        return ""
    return str(s).replace("&", "&amp;")


def esc_all(s):
    """纯文本转义 & < >。"""
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ---------------------------------------------------------------- 样式
S_TITLE = ParagraphStyle("title", fontName=HEI, fontSize=16, leading=24,
                         alignment=TA_CENTER, spaceAfter=6)
S_META = ParagraphStyle("meta", fontName=BODY, fontSize=10.5, leading=18,
                        alignment=TA_CENTER)
S_HEADING = ParagraphStyle("heading", fontName=HEI, fontSize=12, leading=18,
                           spaceBefore=12, spaceAfter=6)
S_BODY = ParagraphStyle("body", fontName=BODY, fontSize=10.5, leading=17,
                        alignment=TA_JUSTIFY, firstLineIndent=21, spaceAfter=4)
S_FORMULA = ParagraphStyle("formula", fontName=BODY, fontSize=11, leading=18,
                           alignment=TA_CENTER, spaceBefore=6, spaceAfter=6)
S_CAPTION = ParagraphStyle("caption", fontName=BODY, fontSize=9, leading=13,
                           alignment=TA_CENTER, textColor=colors.HexColor("#444444"),
                           spaceBefore=2, spaceAfter=8)
S_LIST = ParagraphStyle("list", fontName=BODY, fontSize=10.5, leading=17,
                        leftIndent=16, spaceAfter=2)
S_CELL = ParagraphStyle("cell", fontName=BODY, fontSize=9.5, leading=13,
                        alignment=TA_CENTER)
S_CELL_H = ParagraphStyle("cellh", fontName=HEI, fontSize=9.5, leading=13,
                          alignment=TA_CENTER)


def blank_text(label, hint=None, length=22):
    """留空占位：灰色提示 + 下划线。"""
    h = f"<font color='#999999'>{esc_all(hint)}</font>" if hint else ""
    line = "＿" * length
    return f"{esc_all(label)}：{h}{line}"


def render_block(block):
    """把单个 block 转成 platypus flowable 列表。"""
    out = []
    t = block.get("type")

    if t == "p":
        out.append(Paragraph(esc_amp(block.get("text", "")), S_BODY))

    elif t == "ul":
        for item in block.get("items", []):
            out.append(Paragraph("• " + esc_amp(item), S_LIST))

    elif t == "ol":
        for i, item in enumerate(block.get("items", []), 1):
            out.append(Paragraph(f"{i}. " + esc_amp(item), S_LIST))

    elif t == "formula":
        out.append(Paragraph(esc_amp(block.get("text", "")), S_FORMULA))

    elif t == "blank":
        out.append(Paragraph(blank_text(block.get("label", "待填写"),
                                        block.get("hint")), S_BODY))

    elif t == "table":
        headers = block.get("headers", [])
        rows = block.get("rows", [])
        data = []
        if headers:
            data.append([Paragraph(esc_amp(h), S_CELL_H) for h in headers])
        for r in rows:
            data.append([Paragraph(esc_amp(c), S_CELL) for c in r])
        if data:
            tb = Table(data, hAlign="CENTER")
            style = [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#666666")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
            if headers:
                style.append(("BACKGROUND", (0, 0), (-1, 0),
                              colors.HexColor("#EEEEEE")))
            tb.setStyle(TableStyle(style))
            out.append(tb)
            out.append(Spacer(1, 6))

    elif t == "figure":
        path = block.get("path")
        if path and os.path.exists(path):
            try:
                w, h = ImageReader(path).getSize()
                max_w = min(USABLE_W * 0.92, 460)
                if w > max_w:
                    h = h * max_w / w
                    w = max_w
                img = Image(path, width=w, height=h)
                img.hAlign = "CENTER"
                out.append(img)
                cap = block.get("caption")
                if cap:
                    out.append(Paragraph(esc_all(cap), S_CAPTION))
            except Exception as e:
                out.append(Paragraph(
                    f"<font color='red'>[图片加载失败: {esc_all(str(e))}]</font>",
                    S_CAPTION))
        else:
            out.append(Paragraph(
                blank_text("图", block.get("caption", "图片")), S_BODY))

    elif t == "spacer":
        out.append(Spacer(1, float(block.get("height", 6))))

    return out


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("SimSun", 9)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawCentredString(PAGE_W / 2.0, 36, f"第 {doc.page} 页")
    canvas.restoreState()


def build(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "实验报告")
    meta = data.get("meta", {})

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=LEFT, rightMargin=RIGHT,
                            topMargin=TOP, bottomMargin=BOTTOM,
                            title=title)
    story = []

    # 标题
    story.append(Paragraph(esc_all(title), S_TITLE))
    story.append(Spacer(1, 4))

    # 元信息（姓名 / 同组 / 日期）：居中两行
    def meta_pair(label, key):
        v = meta.get(key, "")
        if v:
            return f"{esc_all(label)}：{esc_all(v)}"
        return blank_text(label, "待填写", length=10)

    story.append(Paragraph(
        meta_pair("实验者姓名", "实验者姓名") + "　　" +
        meta_pair("同组者姓名", "同组者姓名"), S_META))
    story.append(Paragraph(meta_pair("实验日期", "实验日期"), S_META))
    story.append(Spacer(1, 6))

    # 分隔线
    story.append(Table([[""]], colWidths=[USABLE_W], rowHeights=[0.5],
                       style=TableStyle([
                           ("LINEBELOW", (0, 0), (-1, -1), 1,
                            colors.HexColor("#000000")),
                       ])))
    story.append(Spacer(1, 4))

    # 各章节
    for sec in data.get("sections", []):
        heading = sec.get("heading", "")
        if heading:
            story.append(Paragraph(esc_all(heading), S_HEADING))
        for block in sec.get("blocks", []):
            story.extend(render_block(block))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output_path


def main(argv):
    if not argv:
        print(__doc__)
        sys.exit(1)
    input_path = argv[0]
    output_path = argv[1] if len(argv) > 1 else os.path.splitext(input_path)[0] + ".pdf"
    if not os.path.exists(input_path):
        print(f"[error] 找不到输入文件: {input_path}", file=sys.stderr)
        sys.exit(1)
    out = build(input_path, output_path)
    print(f"[ok] 已生成 PDF: {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
