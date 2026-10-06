from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


DOCX_PATH = Path(r"D:\projects\iot-final\docs\proposal\Nguyen_Vu_Bao_De_cuong_da_chinh_sua.docx")
NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


with ZipFile(DOCX_PATH) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))

pages = defaultdict(list)
page = 1
for element in root.find(f"{NS}body").iter():
    if element.tag == f"{NS}lastRenderedPageBreak":
        page += 1
    elif element.tag == f"{NS}br" and element.get(f"{NS}type") == "page":
        page += 1
    elif element.tag == f"{NS}t" and element.text:
        pages[page].append(element.text)

for number in sorted(pages):
    text = " ".join("".join(pages[number]).split())
    print(f"PAGE {number}: {text[:1000]}")
