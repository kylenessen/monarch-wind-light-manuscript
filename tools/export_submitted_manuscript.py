#!/usr/bin/env python3
"""Export a clean MDPI Insects DOCX from a specific Git commit."""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
import zipfile
from xml.etree import ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DOCX = REPO_ROOT / "reference" / "manuscript_20260409.docx"
CSL = REPO_ROOT / "tools" / "acs-numeric.csl"
EXPECTED_REFERENCE_SHA256 = "cf749bb13082d53b814a1133fd0f5c031a9b1d579f75905adadb64932134b0e0"
EXPECTED_COMMIT = "12b7cc9465ce42000c7143ad6d3e10c7311aee5c"


@dataclass
class TableSpec:
    marker: str
    caption: str
    label: str | None
    rows: list[list[str]]
    merge_rows: set[int]


def run(*args: str, cwd: Path | None = None, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_command(text: str, command: str) -> str:
    start = text.index(f"\\{command}")
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1 : index]
    raise RuntimeError(f"Unclosed command: {command}")


def strip_latex(value: str) -> str:
    value = value.strip()
    value = re.sub(r"(?<!\\)%.*", "", value)
    previous = None
    while value != previous:
        previous = value
        value = re.sub(r"\\(?:textbf|textit|emph|mathrm|textrm|texttt)\{([^{}]*)\}", r"\1", value)
    replacements = {
        r"\&": "&",
        r"\%": "%",
        r"\_": "_",
        r"\quad": " ",
        r"\;": " ",
        r"\,": " ",
        "\\ ": " ",
        r"~": " ",
        r"\Delta": "Δ",
        r"\beta": "β",
        r"\rho": "ρ",
        r"\pm": "±",
        r"\times": "×",
        r"\geq": "≥",
        r"\leq": "≤",
        r"\sim": "~",
        r"\circ": "°",
        r"$-$": "−",
        r"---": "-",
        r"--": "-",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\\sqrt\[3\]\{\\Delta(?:\\mathrm\{BI\}|BI)\}", "∛ΔBI", value)
    value = re.sub(r"\\sqrt\{\|\\Delta(?:\\mathrm\{BI\}|\\?BI)_?\{?\\max\}?\|\}", "√|ΔBImax|", value)
    value = re.sub(r"\^\{2\}", "²", value)
    value = re.sub(r"_\{\\text\{([^{}]+)\}\}", r"_\1", value)
    value = re.sub(r"_\{([^{}]+)\}", r"_\1", value)
    value = value.replace("$", "")
    value = re.sub(r"\\(?:small|footnotesize|centering|raggedright|arraybackslash)\b", "", value)
    value = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", value)
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def split_table_rows(body: str) -> list[str]:
    rows: list[str] = []
    current: list[str] = []
    index = 0
    math = False
    while index < len(body):
        char = body[index]
        if char == "$" and (index == 0 or body[index - 1] != "\\"):
            math = not math
        if not math and body[index : index + 2] == r"\\":
            rows.append("".join(current))
            current = []
            index += 2
            continue
        current.append(char)
        index += 1
    if "".join(current).strip():
        rows.append("".join(current))
    return rows


def split_cells(row: str) -> list[str]:
    cells: list[str] = []
    current: list[str] = []
    depth = 0
    math = False
    for index, char in enumerate(row):
        if char == "$" and (index == 0 or row[index - 1] != "\\"):
            math = not math
        elif not math and char == "{":
            depth += 1
        elif not math and char == "}":
            depth = max(0, depth - 1)
        if char == "&" and not math and depth == 0 and (index == 0 or row[index - 1] != "\\"):
            cells.append("".join(current))
            current = []
        else:
            current.append(char)
    cells.append("".join(current))
    return cells


def parse_table_block(block: str, number: int) -> TableSpec:
    marker = f"[[TABLE_{number:02d}]]"
    caption_match = re.search(r"\\caption\{(.+?)\}(?:\s*\\label\{[^}]+\})?", block, re.S)
    if not caption_match:
        raise RuntimeError(f"Table {number} has no caption")
    caption = strip_latex(caption_match.group(1))
    label_match = re.search(r"\\label\{([^}]+)\}", block)
    label = label_match.group(1) if label_match else None

    tabular_match = re.search(
        r"\\begin\{(?:tabularx|tabular|longtable)\}(?:\{[^\n]*\}){1,2}(.*?)\\end\{(?:tabularx|tabular|longtable)\}",
        block,
        re.S,
    )
    if not tabular_match:
        raise RuntimeError(f"Could not parse table body for {marker}")
    body = tabular_match.group(1)
    body = re.sub(r"\\caption\{.*?\}(?:\s*\\label\{[^}]+\})?\s*\\\\", "", body, flags=re.S)
    body = re.sub(r"\\(?:toprule|midrule|bottomrule|endfirsthead|endhead|endfoot|endlastfoot|addlinespace)\b", "", body)
    body = re.sub(r"(?<!\\)%.*", "", body)

    parsed: list[list[str]] = []
    merge_rows: set[int] = set()
    for raw_row in split_table_rows(body):
        raw_row = raw_row.strip()
        if not raw_row:
            continue
        multicol = re.fullmatch(r"\\multicolumn\{\d+\}\{[^}]+\}\{(.*)\}", raw_row, re.S)
        if multicol:
            parsed.append([strip_latex(multicol.group(1))])
            merge_rows.add(len(parsed) - 1)
            continue
        cells = split_cells(raw_row)
        cleaned: list[str] = []
        merge = False
        for cell in cells:
            match = re.fullmatch(r"\\multicolumn\{\d+\}\{[^}]+\}\{(.*)\}", cell.strip(), re.S)
            if match:
                cleaned.append(strip_latex(match.group(1)))
                merge = True
            else:
                cleaned.append(strip_latex(cell))
        if any(cleaned):
            parsed.append(cleaned)
            if merge:
                merge_rows.add(len(parsed) - 1)

    if not parsed:
        raise RuntimeError(f"No rows parsed for {marker}")
    columns = max(len(row) for row in parsed if row)
    rows = [row + [""] * (columns - len(row)) for row in parsed]
    return TableSpec(marker, caption, label, rows, merge_rows)


def extract_tables(source: str) -> tuple[str, list[TableSpec]]:
    tables: list[TableSpec] = []
    pattern = re.compile(r"\\begin\{(table|longtable)\}(?:\[[^\]]*\])?")
    output: list[str] = []
    position = 0
    while match := pattern.search(source, position):
        env = match.group(1)
        end_token = f"\\end{{{env}}}"
        end = source.index(end_token, match.end()) + len(end_token)
        block = source[match.start() : end]
        spec = parse_table_block(block, len(tables) + 1)
        tables.append(spec)
        output.append(source[position : match.start()])
        output.append(f"\n\n{spec.marker}\n\n")
        position = end
    output.append(source[position:])
    return "".join(output), tables


def replace_cross_references(source: str, original: str, tables: list[TableSpec]) -> str:
    figure_labels = re.findall(r"\\label\{(fig:[^}]+)\}", original)
    table_labels = [table.label for table in tables if table.label]
    appendix_labels = re.findall(r"\\section\{[^}]+\}\s*\\label\{(app:[^}]+)\}", original)
    maps = {
        **{label: f"Figure {index}" for index, label in enumerate(figure_labels, 1)},
        **{label: f"Table {index}" for index, label in enumerate(table_labels, 1)},
        **{label: f"Appendix {chr(64 + index)}" for index, label in enumerate(appendix_labels, 1)},
    }

    source = re.sub(
        r"(?:Figure|Table|Appendix)~\\ref\{([^}]+)\}",
        lambda match: maps[match.group(1)],
        source,
    )
    source = re.sub(
        r"Appendices~\\ref\{([^}]+)\}\s+and\s+\\ref\{([^}]+)\}",
        lambda match: f"{maps[match.group(1)]} and {maps[match.group(2)]}",
        source,
    )
    source = re.sub(r"\\label\{(?:tab|app):[^}]+\}", "", source)
    unresolved = re.findall(r"\\ref\{([^}]+)\}", source)
    if unresolved:
        raise RuntimeError(f"Unresolved cross-references: {unresolved}")
    return source


def build_pandoc_source(original: str) -> tuple[str, list[TableSpec]]:
    title = extract_command(original, "Title")
    authors = extract_command(original, "Author")
    address = extract_command(original, "address")
    correspondence = extract_command(original, "corres")
    simple_summary = extract_command(original, "simplesumm")
    abstract = extract_command(original, "abstract")
    keywords = extract_command(original, "keyword")

    body_start = original.index(r"\begin{document}") + len(r"\begin{document}")
    body_end = original.rindex(r"\end{document}")
    body = original[body_start:body_end]
    body = re.sub(r"\\bibliography\{[^}]+\}", "", body)
    body = re.sub(r"\\reftitle\{[^}]+\}", "", body)
    body = body.replace(r"\appendixstart", "").replace(r"\begin{appendix}", "").replace(r"\end{appendix}", "")
    body = re.sub(r"\\vspace\{[^}]+\}", "", body)

    backmatter = (
        ("authorcontributions", "Author Contributions"),
        ("funding", "Funding"),
        ("dataavailability", "Data Availability"),
        ("conflictsofinterest", "Conflicts of Interest"),
        ("acknowledgments", "Acknowledgments"),
    )
    for command, heading in backmatter:
        content = extract_command(body, command)
        start = body.index(f"\\{command}")
        brace = body.index("{", start)
        depth = 0
        end = None
        for index in range(brace, len(body)):
            if body[index] == "{":
                depth += 1
            elif body[index] == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            raise RuntimeError(f"Unclosed back-matter command: {command}")
        body = body[:start] + f"\\section{{{heading}}}\n\n{content}\n" + body[end:]

    body, tables = extract_tables(body)
    body = replace_cross_references(body, original, tables)
    body = body.replace(r"\text{Butterfly index}", r"\mathrm{Butterfly\ index}")
    body = body.replace(r"\sqrt[3]{\Delta\mathrm{BI}}", "∛ΔBI")
    body = body.replace(r"\sqrt{\lvert \Delta\mathrm{BI}_{\max} \rvert}", "√|ΔBImax|")
    body = body.replace(r"\sqrt{|\Delta{BI}_{\max}|}", "√|ΔBImax|")

    addresses = [part.strip() for part in address.split(";") if part.strip()]
    address_block = "\n\n".join(f"[[ADDRESS]] {part}" for part in addresses)
    frontmatter = f"""
[[TITLE]] {title}

[[AUTHORS]] \\textbf{{Authors:}} {authors}

{address_block}

[[CORRESPONDENCE]] {correspondence}

\\section{{Simple Summary}}

{simple_summary}

\\section{{Abstract}}

{abstract}

\\section{{Keywords}}

{keywords}
"""
    wrapper = "\n".join(
        (
            r"\documentclass{article}",
            r"\usepackage{amsmath}",
            r"\usepackage{graphicx}",
            r"\usepackage{float}",
            r"\usepackage{hyperref}",
            r"\begin{document}",
            frontmatter,
            body,
            r"\end{document}",
            "",
        )
    )
    return wrapper, tables


def set_repeat_table_header(row) -> None:
    row_properties = row._tr.get_or_add_trPr()
    marker = row_properties.find(qn("w:tblHeader"))
    if marker is None:
        marker = OxmlElement("w:tblHeader")
        row_properties.append(marker)
    marker.set(qn("w:val"), "true")


def set_cell_margins(cell, top: int = 70, start: int = 90, bottom: int = 70, end: int = 90) -> None:
    cell_properties = cell._tc.get_or_add_tcPr()
    margins = cell_properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        cell_properties.append(margins)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths: list[int]) -> None:
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    properties = table._tbl.tblPr
    width_node = properties.first_child_found_in("w:tblW")
    if width_node is None:
        width_node = OxmlElement("w:tblW")
        properties.append(width_node)
    width_node.set(qn("w:w"), str(sum(widths)))
    width_node.set(qn("w:type"), "dxa")
    indent = properties.first_child_found_in("w:tblInd")
    if indent is None:
        indent = OxmlElement("w:tblInd")
        properties.append(indent)
    indent.set(qn("w:w"), "90")
    indent.set(qn("w:type"), "dxa")

    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        column = OxmlElement("w:gridCol")
        column.set(qn("w:w"), str(width))
        grid.append(column)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            cell.width = width = widths[min(index, len(widths) - 1)]
            cell_properties = cell._tc.get_or_add_tcPr()
            cell_width = cell_properties.first_child_found_in("w:tcW")
            if cell_width is None:
                cell_width = OxmlElement("w:tcW")
                cell_properties.append(cell_width)
            cell_width.set(qn("w:w"), str(width))
            cell_width.set(qn("w:type"), "dxa")
            set_cell_margins(cell)


def add_table_before(doc: Document, paragraph, spec: TableSpec, table_number: int) -> None:
    caption = paragraph.insert_paragraph_before(f"Table {table_number}. {spec.caption}")
    caption.style = "Table Caption"
    caption.paragraph_format.keep_with_next = True
    caption.paragraph_format.space_after = Pt(4)
    table = doc.add_table(rows=0, cols=len(spec.rows[0]))
    table.style = "Table"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    for row_index, values in enumerate(spec.rows):
        cells = table.add_row().cells
        for column_index, value in enumerate(values):
            cell = cells[column_index]
            cell.text = value
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for cell_paragraph in cell.paragraphs:
                cell_paragraph.style = "Compact"
                cell_paragraph.paragraph_format.space_before = Pt(0)
                cell_paragraph.paragraph_format.space_after = Pt(0)
                cell_paragraph.paragraph_format.line_spacing = 1.0
                if row_index == 0:
                    for run in cell_paragraph.runs:
                        run.bold = True
        if row_index in spec.merge_rows and len(cells) > 1:
            merged = cells[0].merge(cells[-1])
            merged.text = values[0]
            for cell_paragraph in merged.paragraphs:
                cell_paragraph.style = "Compact"
                cell_paragraph.paragraph_format.space_before = Pt(1.8)
                cell_paragraph.paragraph_format.space_after = Pt(1.8)
                for run in cell_paragraph.runs:
                    run.italic = True
    set_repeat_table_header(table.rows[0])
    columns = len(spec.rows[0])
    if columns == 2:
        widths = [1150, 8120]
    elif columns == 3:
        widths = [3090, 3090, 3090]
    elif columns == 4:
        widths = [5010, 1420, 1420, 1420]
    elif columns == 5:
        widths = [1350, 4560, 1120, 1120, 1120]
    elif columns == 6:
        widths = [950, 4800, 880, 880, 880, 880]
    elif columns == 7:
        widths = [700, 4150, 650, 850, 850, 1050, 1020]
    elif columns == 8:
        widths = [600, 3350, 600, 900, 850, 900, 850, 1220]
    else:
        widths = [9270 // columns] * columns
        widths[-1] += 9270 - sum(widths)
    set_table_geometry(table, widths)
    paragraph._p.addprevious(table._tbl)
    paragraph._element.getparent().remove(paragraph._element)


def set_style_font(style, name: str, size: float, color: str | None = None, bold=None, italic=None) -> None:
    style.font.name = name
    style.font.size = Pt(size)
    if color:
        style.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    run_properties = style.element.get_or_add_rPr()
    fonts = run_properties.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        run_properties.insert(0, fonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{attr}"), name)


def style_document(doc: Document, tables: list[TableSpec], source_commit: str) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)

    for style_name in ("Normal", "Body Text", "First Paragraph"):
        style = doc.styles[style_name]
        set_style_font(style, "Calibri", 11, "000000")
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.line_spacing = 1.05
        style.paragraph_format.widow_control = True
    set_style_font(doc.styles["Title"], "Calibri", 24, "000000")
    doc.styles["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles["Title"].paragraph_format.space_after = Pt(8)
    for name, size, before in (("Heading 1", 18, 14), ("Heading 2", 15, 8), ("Heading 3", 13, 7)):
        style = doc.styles[name]
        set_style_font(style, "Calibri", size, "0F4761")
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.keep_together = True
    for name in ("Image Caption", "Table Caption", "Caption"):
        if name in doc.styles:
            style = doc.styles[name]
            set_style_font(style, "Calibri", 10, "000000", italic=True)
            style.paragraph_format.space_before = Pt(3)
            style.paragraph_format.space_after = Pt(7)
            style.paragraph_format.keep_together = True
    if "Compact" in doc.styles:
        set_style_font(doc.styles["Compact"], "Calibri", 9, "000000")
    if "Bibliography" in doc.styles:
        style = doc.styles["Bibliography"]
        set_style_font(style, "Calibri", 9, "000000")
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.left_indent = Inches(0.22)
        style.paragraph_format.first_line_indent = Inches(-0.22)

    markers = {
        "[[TITLE]]": "Title",
        "[[AUTHORS]]": "First Paragraph",
        "[[ADDRESS]]": "Body Text",
        "[[CORRESPONDENCE]]": "Body Text",
    }
    for paragraph in doc.paragraphs:
        for marker, style_name in markers.items():
            if paragraph.text.startswith(marker):
                for text_node in paragraph._p.iter(qn("w:t")):
                    if text_node.text and marker in text_node.text:
                        text_node.text = text_node.text.replace(marker, "", 1).lstrip()
                        break
                leading = True
                for text_node in paragraph._p.iter(qn("w:t")):
                    if leading and text_node.text:
                        text_node.text = text_node.text.lstrip()
                    if text_node.text:
                        leading = False
                paragraph.style = style_name
                if marker == "[[TITLE]]":
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                break

    table_by_marker = {table.marker: table for table in tables}
    for paragraph in list(doc.paragraphs):
        if paragraph.text.strip() in table_by_marker:
            spec = table_by_marker[paragraph.text.strip()]
            add_table_before(doc, paragraph, spec, tables.index(spec) + 1)

    figure_number = 1
    for paragraph in doc.paragraphs:
        style_name = paragraph.style.name if paragraph.style else ""
        if style_name == "Image Caption" and paragraph.text.strip():
            run = OxmlElement("w:r")
            text = OxmlElement("w:t")
            text.text = f"Figure {figure_number}. "
            run.append(text)
            first_run = paragraph._p.find(qn("w:r"))
            paragraph._p.insert(0 if first_run is None else paragraph._p.index(first_run), run)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            figure_number += 1
        if "w:drawing" in paragraph._p.xml:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(0)
    if figure_number != 14:
        raise RuntimeError(f"Expected 13 figures, found {figure_number - 1}")

    for shape in doc.inline_shapes:
        max_width = Inches(5.55)
        max_height = Inches(6.7)
        scale = min(1.0, max_width / shape.width, max_height / shape.height)
        shape.width = int(shape.width * scale)
        shape.height = int(shape.height * scale)

    doc.core_properties.title = "Wind Does Not Disrupt Overwintering Monarch Butterfly Clusters"
    doc.core_properties.subject = f"MDPI Insects manuscript submitted from Git commit {source_commit}"
    doc.core_properties.author = "Kyle Nessen, Peter C. Ibsen, Jay E. Diffendorfer, Francis X. Villablanca"
    doc.core_properties.last_modified_by = ""
    doc.core_properties.keywords = "monarch butterfly; wind disruption; thermoregulation; MDPI Insects"


def strip_review_parts(path: Path) -> None:
    removable = (
        "word/comments.xml",
        "word/commentsExtended.xml",
        "word/commentsIds.xml",
        "word/commentsExtensible.xml",
        "word/people.xml",
    )
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False, dir=path.parent) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                if item.filename in removable:
                    continue
                data = source.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    root = ET.fromstring(data)
                    for child in list(root):
                        part_name = child.attrib.get("PartName", "")
                        if "comment" in part_name.lower() or part_name.endswith("/people.xml"):
                            root.remove(child)
                    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                elif item.filename == "word/_rels/document.xml.rels":
                    root = ET.fromstring(data)
                    for child in list(root):
                        target_name = child.attrib.get("Target", "")
                        if "comment" in target_name.lower() or target_name.endswith("people.xml"):
                            root.remove(child)
                    data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                target.writestr(item, data)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def validate(path: Path, tables: list[TableSpec], source_commit: str) -> None:
    doc = Document(path)
    all_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    headings = [paragraph.text for paragraph in doc.paragraphs if paragraph.style and paragraph.style.name == "Heading 1"]
    required = {
        "Simple Summary",
        "Abstract",
        "Keywords",
        "Introduction",
        "Materials and Methods",
        "Results",
        "Discussion",
        "Conclusions",
        "Author Contributions",
        "Funding",
        "Data Availability",
        "Conflicts of Interest",
        "Acknowledgments",
        "30-Minute Wind Disruption Analysis: Candidate Models",
        "Threshold Wind Disruption Analysis: Candidate Models",
        "Site Fidelity Analysis (Next Day Window): Candidate Models",
        "24-Hour Robustness Analysis: Candidate Models",
        "References",
    }
    missing = required.difference(headings)
    if missing:
        raise RuntimeError(f"Missing top-level sections: {sorted(missing)}")
    if len(doc.inline_shapes) != 13:
        raise RuntimeError(f"Expected 13 figures, found {len(doc.inline_shapes)}")
    if len(doc.tables) != 11:
        raise RuntimeError(f"Expected 11 tables, found {len(doc.tables)}")
    bibliography = [paragraph for paragraph in doc.paragraphs if paragraph.style and paragraph.style.name == "Bibliography"]
    if len(bibliography) != 66:
        raise RuntimeError(f"Expected 66 bibliography entries, found {len(bibliography)}")
    if re.search(r"\\(?:cite|ref)\{|\[\[(?:TITLE|TABLE|AUTHORS)", all_text):
        raise RuntimeError("Raw source markers remain in the exported document")
    if f"Git commit {source_commit}" not in doc.core_properties.subject:
        raise RuntimeError("Source commit metadata is missing")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        forbidden_parts = {name for name in names if "comment" in name.lower() or name.endswith("people.xml")}
        if forbidden_parts:
            raise RuntimeError(f"Review parts remain: {sorted(forbidden_parts)}")
        document_xml = archive.read("word/document.xml")
        for marker in (b"<w:ins", b"<w:del", b"<w:moveFrom", b"<w:moveTo", b"commentRange"):
            if marker in document_xml:
                raise RuntimeError(f"Review markup remains: {marker.decode(errors='ignore')}")
    if len(tables) != 11:
        raise RuntimeError(f"Source parser found {len(tables)} tables, expected 11")


def export(commit: str, output: Path, pandoc: str) -> None:
    resolved = run("git", "rev-parse", commit, cwd=REPO_ROOT, capture=True)
    if resolved != EXPECTED_COMMIT:
        raise RuntimeError(f"Expected commit {EXPECTED_COMMIT}, got {resolved}")
    if sha256(REFERENCE_DOCX) != EXPECTED_REFERENCE_SHA256:
        raise RuntimeError("The retained MDPI reference DOCX does not match its recorded checksum")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="monarch-submitted-docx-") as temp_name:
        temp_dir = Path(temp_name)
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        archive_path = temp_dir / "source.tar"
        with archive_path.open("wb") as archive_handle:
            subprocess.run(("git", "archive", resolved), cwd=REPO_ROOT, check=True, stdout=archive_handle)
        run("tar", "-xf", str(archive_path), "-C", str(source_dir))

        original = (source_dir / "manuscript.tex").read_text(encoding="utf-8")
        pandoc_source, tables = build_pandoc_source(original)
        wrapped_tex = temp_dir / "manuscript-word.tex"
        raw_docx = temp_dir / "manuscript-word-raw.docx"
        wrapped_tex.write_text(pandoc_source, encoding="utf-8")

        run(
            pandoc,
            str(wrapped_tex),
            "--from=latex",
            "--to=docx",
            "--citeproc",
            f"--csl={CSL}",
            f"--bibliography={source_dir / 'bibliography' / 'references.bib'}",
            f"--resource-path={source_dir}",
            f"--reference-doc={REFERENCE_DOCX}",
            "--metadata=link-citations:false",
            "--metadata=reference-section-title:References",
            f"--output={raw_docx}",
            cwd=source_dir,
        )

        doc = Document(raw_docx)
        style_document(doc, tables, resolved)
        doc.save(output)
        strip_review_parts(output)
    validate(output, tables, resolved)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", default="main")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pandoc", default=shutil.which("pandoc") or "pandoc")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    export(arguments.commit, arguments.output.resolve(), arguments.pandoc)
