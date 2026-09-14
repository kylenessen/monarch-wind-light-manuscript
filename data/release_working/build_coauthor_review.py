"""Create the coauthor review guide using the bundled Python document runtime.

Run through uv with --no-project and the workspace dependency Python interpreter.
The DOCX is a review companion. It is not added to the public data package.
"""

import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "data/release"
OUT = Path(__file__).with_name("Monarch_data_release_coauthor_review.docx")
meta = ET.parse(RELEASE / "metadata.xml")
authors = [node.text for node in meta.findall("idinfo/citation/citeinfo/origin")]
contact = meta.findtext("idinfo/ptcontac/cntinfo/cntemail")
validation = json.loads((Path(__file__).parent / "validation.json").read_text())
counts = validation["table_rows"]
assert authors == ["Kyle Nessen", "Peter C. Ibsen", "Jay E. Diffendorfer", "Francis X. Villablanca"]
assert contact == "knessen@calpoly.edu"
with (RELEASE / "data_dictionary.csv").open() as source:
    field_count = len(list(csv.DictReader(source)))

doc = Document()
section = doc.sections[0]
section.different_first_page_header_footer = False
doc.settings.odd_and_even_pages_header_footer = False
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin, section.bottom_margin = Inches(.75), Inches(.75)
section.left_margin, section.right_margin = Inches(1), Inches(1)
section.header_distance, section.footer_distance = Inches(.3), Inches(.3)

for style_name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Header", "Footer"):
    style = doc.styles[style_name]
    style.font.name = "Calibri"
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.widow_control = True
# Remove inherited decorative title rules from the bundled default document.
for border in doc.styles.element.xpath(".//w:pBdr"):
    border.getparent().remove(border)
doc.styles["Normal"].font.size = Pt(11)
doc.styles["Normal"].paragraph_format.space_after = Pt(8)
doc.styles["Normal"].paragraph_format.line_spacing = 1.08
doc.styles["Title"].font.size = Pt(22)
doc.styles["Title"].font.bold = True
doc.styles["Title"].paragraph_format.space_after = Pt(8)
doc.styles["Subtitle"].font.size = Pt(11)
doc.styles["Subtitle"].paragraph_format.space_after = Pt(12)
for style_name, size in (("Heading 1", 15), ("Heading 2", 12)):
    style = doc.styles[style_name]
    style.font.size = Pt(size)
    style.font.bold = True
    style.paragraph_format.space_before = Pt(10)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.keep_with_next = True

header = section.header.paragraphs[0]
header.text = "Monarch monitoring data release"
header.style = doc.styles["Header"]
header.runs[0].font.size = Pt(9)
footer = section.footer.paragraphs[0]
footer.paragraph_format.tab_stops.add_tab_stop(Inches(5.65))
footer.add_run("Coauthor review draft    September 13 2026\t")
footer.add_run("Page ")
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
footer._p.append(field)
for run in footer.runs:
    run.font.size = Pt(9)


def para(text, *, size=None):
    p = doc.add_paragraph(text)
    if size:
        for run in p.runs:
            run.font.size = Pt(size)
    return p


def heading(text, level=1):
    doc.add_heading(text, level=level)


def new_page(title):
    paragraph = doc.add_heading(title, level=1)
    paragraph.paragraph_format.page_break_before = True


def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for col, width in zip(t.columns, widths):
        col.width = Inches(width)
    for cells, values in [(t.rows[0].cells, headers)] + [(t.add_row().cells, r) for r in rows]:
        for cell, value, width in zip(cells, values, widths):
            cell.width = Inches(width)
            cell.text = str(value)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement("w:" + edge)
        for name, value in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
            element.set(qn("w:" + name), value)
        borders.append(element)
    t._tbl.tblPr.append(borders)
    repeat = OxmlElement("w:tblHeader")
    t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for i, row in enumerate(t.rows):
        no_split = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(no_split)
        for j, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props = cell._tc.get_or_add_tcPr()
            margins = OxmlElement("w:tcMar")
            for side, value in (("top", "70"), ("bottom", "70"), ("left", "90"), ("right", "90")):
                edge = OxmlElement("w:" + side)
                edge.set(qn("w:w"), value)
                edge.set(qn("w:type"), "dxa")
                margins.append(edge)
            props.append(margins)
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "434343" if i == 0 else ("F4F4F4" if i % 2 == 0 else "FFFFFF"))
            props.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j == 1 else WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.size = Pt(9.5)
                    run.font.bold = i == 0
                    run.font.color.rgb = RGBColor(255, 255, 255) if i == 0 else RGBColor(0, 0, 0)
    return t


doc.add_paragraph("Monarch monitoring data release", style="Title")
doc.add_paragraph("Coauthor review guide    September 13 2026", style="Subtitle")
para("I am circulating this guide with our draft data release so we can review its scope, processing decisions and limitations before completing the USGS release process. The tables and draft XML are prepared, and the analysis scripts reproduce the retained numerical results. Please focus on whether the descriptions accurately represent the field study and make the data usable without additional explanation from us.")
para("Authors in manuscript order are " + ", ".join(authors[:-1]) + " and " + authors[-1] + ". Kyle Nessen is corresponding author at " + contact + ".", size=10)
para("Kyle Nessen and Francis X. Villablanca are affiliated with the Biological Sciences Department at California Polytechnic State University, San Luis Obispo. Peter C. Ibsen and Jay E. Diffendorfer are affiliated with the USGS Geosciences and Environmental Change Science Center, Denver.", size=10)
heading("Scope and contents", 2)
para("The release covers the 2023–2024 and 2024–2025 field seasons at Vandenberg Space Force Base, California. It includes available observations beyond the manuscript subset. Native classification JSON, its summary CSV and reviewed camera temperatures cover the first season. Analysis inputs are maintained separately in the manuscript repository. There are no second-season temperature data.")
table(["File", "Rows", "What one row represents"], [
    ("deployments.csv", f"{counts['deployments']:,}", "A camera deployment"),
    ("photo_index.csv", f"{counts['photo_index']:,}", "A retained JPEG and its folder path"),
    ("classifications.csv", f"{counts['classifications']:,}", "A classified image and its BI primitives"),
    ("temperature_measurements.csv", f"{counts['temperature_measurements']:,}", "A reviewed image-overlay temperature record"),
    ("wind_measurements.csv", f"{counts['wind_measurements']:,}", "A wind observation linked to a deployment"),
], [2.55, .75, 3.2])
para(f"The package also contains data_dictionary.csv with definitions for all {field_count} data columns, metadata.xml and README.md. The photographs are organized in collections by deployment. This guide is a review companion, not an additional observational dataset.", size=10).paragraph_format.space_before = Pt(7)

new_page("Deployments photographs and recorded time")
heading("Deployment locations and boundaries", 2)
para("There are 19 first-season deployments and nine second-season deployments. Camera and wind-meter field names remain available for linking equipment across records. Latitude and longitude describe approximate camera positions in WGS84, EPSG 4326, in decimal degrees. Locations were recorded with a cellphone under canopy, and some points were adjusted against satellite imagery. First-season points were already in WGS84. Second-season camera points were transformed from EPSG 3498, NAD83(NSRS2007) California zone 5 in US survey feet. The number of decimal places does not establish positional accuracy.")
para("First-season start and end times come from the original deployment GeoPackage. The start_time and end_time columns use YYYY-MM-DD HH:MM:SS format. Second-season start and end times are the earliest and latest EXIF capture times in the reviewed photo collection. The wind selection uses these boundaries. A deployment end time therefore does not imply that its wind meter recorded through that time.")
heading("Photograph organization and joins", 2)
para("The photo index covers 59,039 first-season JPEGs and 167,791 reviewed second-season JPEGs. Deployment identifiers are unique across the release. SC12 identifies the first-season NOVA camera and BlueLake wind meter. SC13 identifies the second-season IRIS camera and RockWall wind meter, correcting the reused source label SC12. Join by deployment_id. Add image_filename for photo joins. Analysis tables contain first-season records only.")
para("TGR1 includes 2,973 photographs with capture times reconstructed from the deployment endpoints. The EXIF metadata and filenames use these times. The visible overlays retain the incorrect camera timestamps.")
para("The folder pattern is photos/deployment_id/. Filenames follow deployment_id_YYYYMMDDHHMMSS.JPG. The timestamp format code is %Y%m%d%H%M%S, using a four-digit year, two-digit month and day, and 24-hour hour, minute and second. Deployment identifiers may themselves contain underscores. Second-season names use recorded EXIF capture times. Existing first-season canonical filenames are preserved.")
para("The release retains one photograph per deployment and capture timestamp.")
heading("Clock convention", 2)
para("Timestamps use device clock times without a UTC offset. TGR1 photo times were reconstructed from deployment start and end using elapsed camera time in image order. Other timestamps remain as recorded.")

new_page("Wind observations and limitations")
heading("Combining the source databases", 2)
para("The wind preparation combined 92 located SQLite databases. It selected records only when the instrument matched the deployment assignment and the recorded time fell within the inclusive deployment interval. This removes unrelated study records outside those assignments and intervals. Numeric whitespace and timestamp representations were standardized for matching. Original database files and recorded measurements were not edited.")
para("Duplicates were identified using instrument, timestamp, wind speed, gust and direction together. Source database row IDs were not treated as globally unique. Different instruments remain distinct, and differing measurements at the same time would be retained for review. No conflicting measurement tuples were found in the retained reconciliation. The working audit preserves source-database and source-row provenance outside the public tables.")
para("The result contains 725,714 distinct wind measurements and 757,260 deployment-associated rows. The first season contributes 531,937 rows and the second contributes 225,323. The difference between distinct measurements and rows is explained by 31,546 StarDust observations assigned to both SC9 and SC10. Both source deployment records name that meter and have overlapping intervals. This supports shared wind coverage for two camera views. It does not establish that both cameras were mounted on one pole. These shared observations must not be counted as independent measurements.")
heading("Fields and direction conventions", 2)
para("The public wind table retains deployment_id, wind_sensor_name, timestamp_recorded, wind_speed_m_s, wind_gust_m_s and wind_direction_degrees. Wind speed and gust are in meters per second. Gust is the logger maximum for the recording interval, normally one minute. These measurements describe conditions near the logger, rather than sustained exposure at every butterfly position.")
para("Wind direction retains the original logger values from 0 to 360 degrees, reported clockwise from north. Speed and gust are reported in meters per second.")
heading("Known coverage limitations", 2)
para("All available wind records with timestamps within the assigned deployment interval are included as recorded. PS01 records end January 31, 2025. SC13 records extend through December 23, 2024, with additional records on January 14, 2025.")
para("Seven second-season deployments have no available wind records within their deployment intervals. The release includes the records available for each deployment.")

new_page("Butterfly classifications and temperature")
heading("Observed primitives and Butterfly Index", 2)
para("The classification summary includes saved daytime classifications, including unconfirmed annotations. Native deployment JSON files retain the full annotations. Untouched unconfirmed zero placeholders are omitted. Second-season images remain unclassified in this release. An image without a classification does not establish butterfly absence.")
para("Each classification contains the deployment identifier, camera name, image filename, recorded time and observer information. It preserves counts of image cells in the 0, 1–9, 10–99 and 100–999 butterfly categories. It also preserves counts of occupied cells marked as receiving direct sunlight in each occupied category. These primitives allow readers to calculate alternative category-weighted indices without changing the original annotations.")
para("Butterfly Index, or BI, is the sum of category lower bounds across the image cells. The category weights are 0, 1, 10 and 100. Sun-exposed BI is the subtotal from occupied cells marked as receiving direct sunlight. BI measures indexed visible cluster size and is not a count of individually identified butterflies. The classification table contains total BI and sun-exposed BI. Changes in BI are confined to the analysis tables.")
heading("Observer attribution and accepted zero", 2)
para("record_user_id preserves the user identifier saved in the image record.")
heading("Reviewed camera temperatures", 2)
para("The temperature table contains 56,066 first-season records linked to image filename, recorded time, deployment and camera. Temperatures were extracted from the image overlays with optical character recognition, then previously reviewed and corrected where necessary. The release copies the reviewed Celsius values, including missing values, without new recalibration or clock changes. The table omits OCR confidence and processing-status columns to keep the released measurements simple.")
para("These are approximate local camera readings. They are not independently calibrated ambient-air temperatures. There are no second-season temperature data, and the release will not imply that a second-season temperature series is missing from the package.")

new_page("Manuscript reproducibility")
para("The observational release includes both monitoring seasons and native image classifications. The manuscript repository separately preserves the exact analysis inputs, scripts and results. Readers reproducing the paper should use the repository. Readers developing a new analysis can use the observations in this release.")
para("The R scripts read data/analysis_inputs/analysis_30_minute.csv and data/analysis_inputs/analysis_next_day.csv. These contain 1,894 thirty-minute pairs and 96 next-day pairs. Their numerical values are preserved.")

new_page("Coauthor review and USGS handoff")
heading("What we are asking colleagues to review", 2)
para("Please review whether the release scope and file descriptions accurately represent the observations, including deployments outside the manuscript subset. Check the camera and wind-meter assignments, deployment boundaries and location descriptions. The deployment identifiers should let a reader connect every table and photograph without relying on local knowledge of the equipment names.")
para("Please also check the scientific definitions and limitations. The central points are that BI is an index, camera temperature is an approximate instrument reading, shared wind records are not independent, and incomplete wind coverage has not been filled. Recorded device times and measurement definitions should be consistent across the README, dictionary and XML. Known recording gaps are documented rather than presented as complete continuous series.")
para("The author list follows the manuscript, and I am the corresponding author. We will send this draft to our USGS contacts for review. The release DOI, USGS metadata identifier, institutional metadata contact, final distribution wording and formal release review remain to be completed with them. The XML contains explicit placeholders for those unfinished administrative fields. It is well-formed XML and its field definitions match the CSV headers, but it is not yet a validated or approved submission record.")
heading("How the review package is organized", 2)
para("The review materials comprise this guide, README.md, metadata.xml, data_dictionary.csv and the five observation tables listed on the first page. The photo index identifies the associated JPEG collections. The Word guide explains the setup, while the dictionary supplies a definition, units, missing-value convention and observed range for every data column. Observed ranges describe this dataset and are not automatically limits for valid future measurements.")
para("The local staging package uses directory links for most photo collections and file hard links for the renamed SC13 collection, avoiding extra copies of image bytes. Before final upload, the indexed JPEGs must be placed in ordinary archives with the deployment paths preserved. Symbolic links and unlisted source files should not be distributed. Working reconciliation records, source provenance audits and this review guide are kept outside the public observational package.")
heading("Where readers will find the scripts", 2)
para("Analysis scripts remain in the manuscript repository at https://github.com/kylenessen/monarch-wind-light-manuscript. They are not included as data-release attachments. From the matching repository version, Rscript analysis/run_results_analyses.R runs the primary results workflow. The focused BI-category and observer checks have a separate documented workflow. The final released data should cite a fixed public repository version so future readers can use the corresponding scripts.")
para("The current metadata and this guide draw on the manuscript, the released tables, the dictionary, the frozen deployment layers and the reconciliation and verification reports. The RainWise WindLog manual is the source for the instrument direction and logging description. It is available at https://rainwise.com/downloads/windsoft/WindLog140805%20.pdf. The supplied Pismo XML was used only as an example of metadata structure. Its study facts and identifiers were not adopted.")

doc.core_properties.title = "Monarch monitoring data release"
doc.core_properties.subject = "Coauthor review of the draft data release"
doc.core_properties.author = "Kyle Nessen"
doc.core_properties.keywords = "monarch butterfly, data release, coauthor review"
doc.core_properties.comments = "Prepared for coauthor review. No release approval is asserted."
doc.save(OUT)
print(OUT)
