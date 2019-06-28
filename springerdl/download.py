
# This file is part of Springer Link Downloader
#
# Copyright 2018 Thomas Vogt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import time, random
from tempfile import NamedTemporaryFile
from gettext import gettext as _

from . import util
from .const import *

def pdf_files(toc, pgs, pause):
    data = [pgs,pause,1,0]
    def count_pdfs(el, _, d):
        d[3] += int(el['pdf_url'] != "")
    util.tocIterateRec(toc, count_pdfs, data)
    util.tocIterateRec(toc, lambda x,y,z: _fetchCh(x,z), data)
    pgs.destroy()

def fetch_pdf_with_pgs(url, pgs, pause=0):
    if url != "":
        pdf = NamedTemporaryFile(delete=False)
        _pauseBeforeHttpGet(pause)
        webPDF  = util.connect(SPRINGER_URL + url)
        file_size = int(webPDF.getheader('Content-Length').strip())
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

def _fetchCh(ch, opts):
    pgs, pause = opts[0], opts[1]
    if pgs != None:
        pgs.set_text(_("Chapter %d/%d, downloading %%d/%%d kB") \
            % (opts[2],opts[3]))
    pdf = fetch_pdf_with_pgs(ch['pdf_url'], pgs, pause)
    if pdf != None:
        ch['pdf_file'] = pdf
        opts[2] += 1

def _pauseBeforeHttpGet(pause):
    if pause > 0:
        time.sleep((0.6 + random.random()*0.8)*pause)

