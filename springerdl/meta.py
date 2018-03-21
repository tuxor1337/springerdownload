
import re, os

try:
    from urllib2 import URLError
    from httplib import BadStatusLine
except ImportError:
    from urllib.error import URLError
    from http.client import BadStatusLine

from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE

from . import util
from .const import *

def fetchBookInfo(root):
    info = []
    noaccess = len(root.cssselect("span.buybox__buy"))
    author_list = root.cssselect("div#authors span[itemprop=name]")
    if len(author_list) == 0:
        author_list = root.cssselect("div#editors span[itemprop=name]")
    chapter_cnt = root.cssselect("span[data-test=no-of-chapters]")[0].text_content()
    m = re.search(r'\(([0-9\.]+) (chapters|entries)\)', chapter_cnt.strip())
    full_pdf = root.cssselect("a.test-bookpdf-link")
    if len(full_pdf) > 0:
        full_pdf = full_pdf[0].get("href")
    else: 
        full_pdf = None
    def get_content(x):
        el = root.cssselect(x)
        return el[0].text_content() if len(el) != 0 else None
    info = {
        'authors' : [x.text_content() for x in author_list],
        'chapter_cnt' : int(m.group(1)),
        'title' : get_content("#book-title h1"),
        'subtitle' : get_content("#book-title h2"),
        'print_isbn' : get_content("#print-isbn"),
        'online_isbn' : get_content("#electronic-isbn"),
        'publisher' : get_content("#publisher-name"),
        'year' : get_content("#copyright-info"),
        'noaccess' : bool(noaccess),
        'full_pdf' : full_pdf,
    }
    if info['year'] is not None:
        m = re.search(r'.*([0-9]+)$', info['year'])
        info['year'] = m.group(1)
                
    return info

def fetchToc(root, book_url):
    toc = []
    def tocMerge(toc1,toc2):
        if len(toc2) != 0 and len(toc1) != 0:
            mergeitem = toc2.pop(0)
            if toc1[-1]['title'] == mergeitem['title']:
                if toc1[-1]['children'][-1]['title'] \
                    == mergeitem['children'][-1]['title'] \
                    and "Back Matter" in toc1[-1]['children'][-1]['title']:
                    toc1[-1]['children'].pop()
                toc1[-1]['children'] = tocMerge(toc1[-1]['children'],
                                                   mergeitem['children'])
            elif mergeitem['page_range'][1] != 0 and \
               (toc1[-1]['page_range'][0] > mergeitem['page_range'][1] \
               or toc1[-1]['page_range'][0] == 0):
                tmp = toc1[-1]
                toc1[-1] = mergeitem
                toc1.append(tmp)
            else:
               toc1.append(mergeitem)
        return toc1+toc2

    tmp_dpc = root.cssselect("span.test-maxpagenum")
    dl_page_cnt = int(tmp_dpc[0].text_content()) if len(tmp_dpc) != 0 else 1
    for i in range(1,dl_page_cnt+1):
        toc = tocMerge(toc, _tocFromDiv(root.cssselect("div#booktoc")[0]))
        if i < dl_page_cnt:
            root = util.getElementTree("%s?page=%d"  % (book_url,i+1))
    return toc

def _tocFromDiv(div):
    def append_ch(ch_list,title="", children=[], pdf_url="", \
              authors=[], page_range="", noaccess=None):
        title = title.replace("\n"," ")
        m = re.search(r'Pages ([0-9A-Z]+)-([0-9A-Z]+)', 
           page_range,re.I)
        try:
            page_range = [m.group(1),m.group(2)]
            if not page_range[0].isdigit():
                if re.match(r'^[IXVCMLD]+$', page_range[0]):
                    page_range = [-1000+util.roman_to_int(x) for x in page_range]
                else:
                    page_range = [0,0]
            page_range = [int(x) for x in page_range]
        except AttributeError:
            if len(ch_list) > 0 and ch_list[-1]['page_range'][1] != 0:
                p = ch_list[-1]['page_range'][1]+1
            else:
                p = 0
            page_range = [p,p]
        ch = {
            'children' : children,
            'title' : title,
            'pdf_url' : pdf_url,
            'noaccess' : noaccess,
            'authors' : authors,
            'page_range' : page_range,
        }
        ch_list.append(ch)
  
    def parsePartItem(chl,li):
        for subh3, subol in zip(li.findall("h3"), li.findall(".//ol")):
            pdf_url = page_range = ""
            fr_matt = subol.cssselect("li.front-matter-item")
            if len(fr_matt) != 0:
                page_range = fr_matt[0].cssselect("span[data-test=page-range]")[0].text_content()
                if fr_matt[0].cssselect("a"):
                    pdf_url = fr_matt[0].cssselect("a")[0].attrib["href"]
                fr_matt[0].getparent().remove(fr_matt[0])
            append_ch(chl, subh3.text_content().strip(), \
                getTocRec(subol), pdf_url, [], page_range)
              
    def parseChItem(chl,li):
        title = li.cssselect(".content-type-list__title")[0].text_content().strip()
        try: 
            link = li.cssselect("div.content-type-list__action a")[0]
            pdf_url = link.attrib["href"] if "PDF" in link.text_content() else ""
        except: pdf_url = ""
        author_list = li.cssselect("div[data-test=author-text]")
        if len(author_list) > 0:
            author_list = author_list[0].text_content().strip().split(',')
        else:
            author_list = []
        append_ch(chl, title, [], pdf_url, author_list,
            li.cssselect("span[data-test=page-range]")[0].text_content(),
            len(pdf_url) == 0)
     
    def getTocRec(ol):
        chl = []
        for li in ol.findall("li"):
            if "part-item" in li.attrib['class']: parsePartItem(chl,li)
            else: parseChItem(chl,li)
        return chl
    
    return getTocRec(div.find("ol"))

def fetchCover(isbn,size):
    try:
        webImg = util.connect("%s/cover-hires/book/%s" \
                       % (SPR_IMG_URL,isbn))
        img_suffix = ".tif"
        if "jpeg" in webImg.info()['content-type']:
            img_suffix = ".jpg"
        tmp_img    = NamedTemporaryFile(delete=False,suffix=img_suffix)
        tmp_pdfimg = NamedTemporaryFile(delete=False,suffix=".pdf")
        tmp_img.write(webImg.read()); tmp_img.close()
        cmd = [IM_BIN, "-resize","%fx%f" % (4*size[0], 4*size[1]), \
                   "-density", "290", tmp_img.name, tmp_pdfimg.name]
        p = Popen(cmd,stdout=PIPE,stderr=PIPE)
        p.communicate(); os.remove(tmp_img.name)
        return tmp_pdfimg
    except (URLError, BadStatusLine):
        return None
        
