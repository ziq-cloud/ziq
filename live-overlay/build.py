"""Build overlay.html: inline the TRAXA icon and Oxanium font into src.html."""
import base64, io
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "promo" / "assets"
buf = io.BytesIO()
Image.open(ASSETS / "traxa_icon.png").resize((192, 192), Image.LANCZOS).save(buf, "PNG", optimize=True)
icon = base64.b64encode(buf.getvalue()).decode()
font = base64.b64encode((ASSETS / "fonts" / "oxanium-latin-500-normal.woff").read_bytes()).decode()
html = (HERE / "src.html").read_text().replace("__ICON__", icon).replace("__FONT__", font)
(HERE / "overlay.html").write_text(html)
print("wrote", HERE / "overlay.html", len(html), "bytes")
