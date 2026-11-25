from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import ContentStream

root = Path(__file__).resolve().parent
reader = PdfReader(root / "AA2_Pipeline_SistemaRestaurante.pdf")
assert len(reader.pages) == 16

used_fonts = set()
nonblack_text = []
for page_number, page in enumerate(reader.pages, start=1):
    resources = page["/Resources"]["/Font"]
    current_font = None
    fill = (0, 0, 0)
    for operands, operator in ContentStream(page.get_contents(), reader).operations:
        if operator == b"Tf":
            current_font = operands[0]
        elif operator == b"rg":
            fill = tuple(float(value) for value in operands)
        elif operator == b"g":
            gray = float(operands[0])
            fill = (gray, gray, gray)
        elif operator == b"k":
            cyan, magenta, yellow, black = (float(value) for value in operands)
            fill = (1 - min(1, cyan + black), 1 - min(1, magenta + black), 1 - min(1, yellow + black))
        elif operator in (b"Tj", b"TJ", b"'", b'"'):
            if current_font is not None:
                used_fonts.add(str(resources[current_font].get_object()["/BaseFont"]))
            if fill != (0, 0, 0):
                nonblack_text.append((page_number, fill))

texts = [page.extract_text() for page in reader.pages]
body = "\n".join(texts)
assert [text.splitlines()[0] for text in texts] == [str(number) for number in range(1, 17)]
assert all("Arial" in font for font in used_fonts), used_fonts
assert not nonblack_text, nonblack_text
assert all(citation in body for citation in ("2026a", "2026b", "Davis & Daniels, 2016", "Smart, 2011"))
assert "[1]" not in body and "[2]" not in body
print("Páginas: 16 (portada + 15 de contenido)")
print("Fuentes con texto visible:", sorted(used_fonts))
print("Color del texto visible: negro")
print("Numeración y citas autor-fecha: correctas")
