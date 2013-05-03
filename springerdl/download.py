
import time, random
from tempfile import NamedTemporaryFile
from gettext import gettext as _

from util import connect

from . import util
from .const import * 

def pdf_files(toc, pgs, pause, cnt):
    data = [pgs,pause,1,cnt]
    util.tocIterateRec(toc, lambda x,y,z: _fetchCh(x,z), data)
    pgs.destroy()

def _fetchCh(ch, opts):
    pgs, pause = opts[0], opts[1]
    if pgs != None:
        pgs.set_text(_("Chapter %d/%d, downloading %%d/%%d kB") \
            % (opts[2],opts[3]))
    pdf = _fetchChPdf(ch['pdf_url'], pgs, pause)
    if pdf != None:
        ch['pdf_file'] = pdf
        opts[2] += 1

def _fetchChPdf(url, pgs, pause):
    if url != "":
        pdf = NamedTemporaryFile(delete=False)
        _pauseBeforeHttpGet(pause)
        webPDF  = connect(SPRINGER_URL + url)
        file_size = int(webPDF.info().getheader('Content-Length').strip())
        downloaded_size = 0
        while 1:
            data = webPDF.read(DOWNLOAD_CHUNK_SIZE)
            pdf.write(data)
            if not data:
                break
            downloaded_size += len(data)
            pgs.update(downloaded_size/1024,file_size/1024)
        return pdf
    else:
        return None
            
def _pauseBeforeHttpGet(pause):
    if pause > 0:	
        time.sleep((0.6 + random.random()*0.8)*pause)
        
