import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _text_from_run(run: ET.Element) -> str:
    parts: list[str] = []
    for t in run.findall(".//w:t", NS):
        if t.text:
            parts.append(t.text)
    return "".join(parts)


def extract_docx_text_with_links(docx_path: Path) -> list[str]:
    with zipfile.ZipFile(docx_path) as z:
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")

    rels_root = ET.fromstring(rels_xml)
    rid_to_target: dict[str, str] = {}
    for rel in rels_root.findall("rel:Relationship", NS):
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        rtype = rel.attrib.get("Type", "")
        if rid and target and rtype.endswith("/hyperlink"):
            rid_to_target[rid] = target

    doc_root = ET.fromstring(doc_xml)

    paras: list[str] = []
    for p in doc_root.findall(".//w:p", NS):
        parts: list[str] = []

        for child in list(p):
            tag = child.tag
            if tag == f"{{{NS['w']}}}hyperlink":
                rid = child.attrib.get(f"{{{NS['r']}}}id")
                url = rid_to_target.get(rid or "")
                link_text: list[str] = []
                for run in child.findall(".//w:r", NS):
                    link_text.append(_text_from_run(run))
                txt = "".join(link_text).strip()
                if txt and url:
                    # Make URL explicit so templates can auto-link it.
                    parts.append(f"{txt} ({url})")
                elif txt:
                    parts.append(txt)
            elif tag == f"{{{NS['w']}}}r":
                txt = _text_from_run(child)
                if txt:
                    parts.append(txt)

        line = "".join(parts).strip()
        if line:
            paras.append(line)

    return paras


def main() -> int:
    # Windows PowerShell consoles often default to a legacy code page.
    # Force UTF-8 so we can print smart punctuation/arrows safely.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) != 2:
        print("Usage: python tools/extract_docx.py <path-to-docx>", file=sys.stderr)
        return 2

    docx_path = Path(sys.argv[1])
    if not docx_path.exists():
        print(f"File not found: {docx_path}", file=sys.stderr)
        return 2

    for line in extract_docx_text_with_links(docx_path):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
