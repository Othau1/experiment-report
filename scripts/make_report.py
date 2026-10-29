# -*- coding: utf-8 -*-
"""
实验报告 PDF 生成器（增强版）。

用法：
    py scripts/make_report.py <input.json> [output.pdf]

输入 JSON 结构见 SKILL.md 与 example/。
支持：封面、摘要/关键词、公式编号、注意事项框、参考文献、页眉页脚、表格隔行底纹。
依赖：reportlab（中文字体用系统自带的 宋体/黑体/楷体/仿宋）。
"""
import json
import sys
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak)
from reportlab.lib.utils import ImageReader

FONT_DIR = "C:/Windows/Fonts"
PAGE_W, PAGE_H = A4
LEFT = RIGHT = 2.0 * cm
TOP = BOTTOM = 2.5 * cm
USABLE_W = PAGE_W - LEFT - RIGHT

_FONT_CANDIDATES = [
    ("SimSun", "simsun.ttc", 0),     # 宋体（正文）
    ("SimHei", "simhei.ttf", None),  # 黑体（标题/加粗）
    ("SimKai", "simkai.ttf", None),  # 楷体（封面/摘要/注意）
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

try:
    registerFontFamily("Body", normal="SimSun", bold="SimHei",
                       italic="SimSun", boldItalic="SimHei")
except Exception:
    pass

BODY = "SimSun"
HEI = "SimHei"
KAI = "SimKai"


def esc_amp(s):
    """转义 &（保留 <b>/<i>/<sub>/<super> 标记）。"""
    if s is None:
        return ""
    return str(s).replace("&", "&amp;")


def esc_all(s):
    """纯文本转义 & < >。"""
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def spaced(s, sep=" "):
    """字符间加空格，用于封面标题的拉宽排版。"""
    return sep.join(str(s))


# ---------------------------------------------------------------- 样式
S_COVER_COURSE = ParagraphStyle("covercourse", fontName=KAI, fontSize=16,
                                leading=24, alignment=TA_CENTER)
S_COVER_TITLE = ParagraphStyle("covertitle", fontName=HEI, fontSize=30,
                               leading=44, alignment=TA_CENTER)
S_COVER_META = ParagraphStyle("covermeta", fontName=KAI, fontSize=14,
                              leading=32, alignment=TA_CENTER)
S_ABSTRACT = ParagraphStyle("abstract", fontName=KAI, fontSize=10, leading=16,
                            alignment=TA_JUSTIFY, spaceAfter=3)
S_KEYWORDS = ParagraphStyle("keywords", fontName=KAI, fontSize=10, leading=16)
S_NOTE = ParagraphStyle("note", fontName=KAI, fontSize=10, leading=16)
S_HEADING = ParagraphStyle("heading", fontName=HEI, fontSize=12, leading=18,
                           spaceBefore=12, spaceAfter=6)
S_SUBHEADING = ParagraphStyle("subheading", fontName=HEI, fontSize=11,
                              leading=16, spaceBefore=8, spaceAfter=4)
S_BODY = ParagraphStyle("body", fontName=BODY, fontSize=10.5, leading=17,
                        alignment=TA_JUSTIFY, firstLineIndent=21, spaceAfter=4)
S_FORMULA = ParagraphStyle("formula", fontName=BODY, fontSize=11, leading=18,
                           alignment=TA_CENTER, spaceBefore=6, spaceAfter=6)
S_FORMULA_CELL = ParagraphStyle("formulacell", fontName=BODY, fontSize=11,
                                leading=18, alignment=TA_CENTER)
S_FORMULA_NUM = ParagraphStyle("formulanum", fontName=BODY, fontSize=11,
                               leading=18, alignment=TA_RIGHT)
S_CAPTION = ParagraphStyle("caption", fontName=BODY, fontSize=9, leading=13,
                           alignment=TA_CENTER,
                           textColor=colors.HexColor("#444444"),
                           spaceBefore=2, spaceAfter=8)
S_LIST = ParagraphStyle("list", fontName=BODY, fontSize=10.5, leading=17,
                        leftIndent=16, spaceAfter=2)
S_CELL = ParagraphStyle("cell", fontName=BODY, fontSize=9.5, leading=13,
                        alignment=TA_CENTER)
S_CELL_H = ParagraphStyle("cellh", fontName=HEI, fontSize=9.5, leading=13,
                          alignment=TA_CENTER)
S_REF = ParagraphStyle("ref", fontName=BODY, fontSize=9.5, leading=15,
                       leftIndent=18, firstLineIndent=-18, spaceAfter=2)


def blank_text(label, hint=None, length=22):
    h = f"<font color='#999999'>{esc_all(hint)}</font>" if hint else ""
    line = "＿" * length
    return f"{esc_all(label)}：{h}{line}"


def cover_blank(label, length=12):
    return f"{esc_all(label)}：{'＿' * length}"


def render_block(block):
    out = []
    t = block.get("type")

    if t == "p":
        out.append(Paragraph(esc_amp(block.get("text", "")), S_BODY))

    elif t == "subheading":
        out.append(Paragraph(esc_all(block.get("text", "")), S_SUBHEADING))

    elif t == "ul":
        for item in block.get("items", []):
            out.append(Paragraph("• " + esc_amp(item), S_LIST))

    elif t == "ol":
        for i, item in enumerate(block.get("items", []), 1):
            out.append(Paragraph(f"{i}. " + esc_amp(item), S_LIST))

    elif t == "formula":
        text = esc_amp(block.get("text", ""))
        num = block.get("num")
        if num:
            tbl = Table([[Paragraph(text, S_FORMULA_CELL),
                          Paragraph(f"({num})", S_FORMULA_NUM)]],
                        colWidths=[USABLE_W - 50, 50], hAlign="CENTER")
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            out.append(tbl)
        else:
            out.append(Paragraph(text, S_FORMULA))

    elif t == "note":
        title = block.get("title", "注意")
        p = Paragraph(f"【{esc_all(title)}】{esc_all(block.get('text', ''))}", S_NOTE)
        tbl = Table([[p]], colWidths=[USABLE_W])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF8E1")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddcf8f")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        out.append(tbl)
        out.append(Spacer(1, 6))

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
            for ri in range(1, len(data)):
                if ri % 2 == 0:
                    style.append(("BACKGROUND", (0, ri), (-1, ri),
                                  colors.HexColor("#FAFAFA")))
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
            out.append(Paragraph(blank_text("图", block.get("caption", "图片")),
                                 S_BODY))

    elif t == "spacer":
        out.append(Spacer(1, float(block.get("height", 6))))

    return out


def render_cover(title, course, meta):
    story = []
    story.append(Spacer(1, 70))
    if course:
        story.append(Paragraph(spaced(course), S_COVER_COURSE))
        story.append(Spacer(1, 40))
    story.append(Paragraph(spaced(title), S_COVER_TITLE))
    story.append(Spacer(1, 70))
    keys = ["实验者姓名", "同组者姓名", "实验日期"]
    if "指导教师" in meta:
        keys.append("指导教师")
    for k in keys:
        v = meta.get(k, "")
        if v:
            story.append(Paragraph(f"{esc_all(k)}：{esc_all(v)}", S_COVER_META))
        else:
            story.append(Paragraph(cover_blank(k), S_COVER_META))
    story.append(PageBreak())
    return story


def render_abstract(abstract, keywords):
    out = []
    inner = []
    if abstract:
        inner.append(Paragraph("【摘要】" + esc_all(abstract), S_ABSTRACT))
    if keywords:
        inner.append(Paragraph("【关键词】" + "；".join(esc_all(k) for k in keywords),
                               S_KEYWORDS))
    if inner:
        tbl = Table([[b] for b in inner], colWidths=[USABLE_W])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F7F7")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        out.append(tbl)
        out.append(Spacer(1, 8))
    return out


def build(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "实验报告")
    course = data.get("course", "")
    meta = data.get("meta", {})
    abstract = data.get("abstract", "")
    keywords = data.get("keywords", [])
    references = data.get("references", [])

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=LEFT, rightMargin=RIGHT,
                            topMargin=TOP, bottomMargin=BOTTOM,
                            title=title)

    def onpage(canvas, doc_):
        canvas.saveState()
        if doc_.page > 1:
            canvas.setFont(KAI, 9)
            canvas.setFillColor(colors.HexColor("#777777"))
            canvas.drawCentredString(PAGE_W / 2.0, PAGE_H - 40, title)
            canvas.setStrokeColor(colors.HexColor("#cccccc"))
            canvas.setLineWidth(0.5)
            canvas.line(LEFT, PAGE_H - 48, PAGE_W - RIGHT, PAGE_H - 48)
        canvas.setFont("SimSun", 9)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawCentredString(PAGE_W / 2.0, 36, f"第 {doc_.page} 页")
        canvas.restoreState()

    story = []
    story += render_cover(title, course, meta)
    story += render_abstract(abstract, keywords)

    for sec in data.get("sections", []):
        heading = sec.get("heading", "")
        if heading:
            story.append(Paragraph(esc_all(heading), S_HEADING))
        for block in sec.get("blocks", []):
            story.extend(render_block(block))

    if references:
        story.append(Paragraph("参考文献", S_HEADING))
        for r in references:
            story.append(Paragraph(esc_all(r), S_REF))

    doc.build(story, onFirstPage=onpage, onLaterPages=onpage)
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
