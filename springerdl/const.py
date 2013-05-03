
import os

SPRINGER_URL = "http://link.springer.com"
SPR_IMG_URL  = "http://images.springer.com"
DOWNLOAD_CHUNK_SIZE = 65536
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1'

BINPATH = { "gs": None, "pdftk": None, "convert": None}
for p in reversed(os.getenv("PATH").split(":")):
    for f in ["gs","convert","pdftk"]:
        candidate = os.path.join(p,f)
        if os.path.isfile(candidate):
            BINPATH[f] = candidate

GS_BIN = BINPATH['gs']
IM_BIN = BINPATH['convert']
PDFTK_BIN = BINPATH['pdftk']
