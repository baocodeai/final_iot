import argparse
from pathlib import Path

from docx import Document


DOCX_PATH = Path(r"D:\projects\iot-final\docs\proposal\Nguyen_Vu_Bao_De_cuong_da_chinh_sua.docx")


def iter_block_items(parent):
    """Yield paragraphs and tables in their document order."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P

    body = parent.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


parser = argparse.ArgumentParser()
parser.add_argument("--start", type=int, default=1)
parser.add_argument("--end", type=int, default=10_000)
args = parser.parse_args()

doc = Document(DOCX_PATH)
for index, block in enumerate(iter_block_items(doc), start=1):
    if not (args.start <= index <= args.end):
        continue
    if hasattr(block, "rows"):
        print(f"\n[TABLE {index}]")
        for row in block.rows:
            print(" | ".join(cell.text.replace("\n", " / ").strip() for cell in row.cells))
    else:
        text = block.text.strip()
        if text:
            style = block.style.name if block.style else ""
            print(f"[{index:03d}] [{style}] {text}")
