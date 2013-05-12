
import re, os

from urllib2 import URLError
from httplib import BadStatusLine
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE

from . import util
from .const import *

def fetchBookInfo(root):
    info = []
    noaccess = len(root.cssselect("span.icon-unlock"))
    author_list = root.cssselect("div.summary li[itemprop=author]")
    if len(author_list) == 0:
        author_list = root.cssselect("div.summary li[itemprop=editor]")
    chapter_cnt = root.cssselect("span.chapter-count")[0].text_content()
    m = re.search(r'\(([0-9\.]+) chapters\)', chapter_cnt.strip())
    def get_id(x):
        el = root.cssselect("#%s" % x)
        return el[0].text_content() if len(el) != 0 else None
    info = {
        'authors' : [x.find("a").text_content() for x in author_list],
        'chapter_cnt' : int(m.group(1)),
        'title' : get_id("abstract-about-title"),
        'subtitle' : get_id("abstract-about-book-subtitle"),
        'print_isbn' : get_id("abstract-about-book-print-isbn"),
        'online_isbn' : get_id("abstract-about-book-online-isbn"),
        'publisher' : get_id("abstract-about-publisher"),
        'year' : get_id("abstract-about-book-chapter-copyright-year"),
        'noaccess' : bool(noaccess),
    }
                
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

    tmp_dpc = root.cssselect("span.number-of-pages")
    dl_page_cnt = int(tmp_dpc[0].text_content()) if len(tmp_dpc) != 0 else 1
    for i in range(1,dl_page_cnt+1):
        toc = tocMerge(toc,_tocFromDiv(root.cssselect("div.toc")[0]))
        if i < dl_page_cnt:
            root = util.getElementTree("%s/page/%d"  % (book_url,i+1))
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
        for subh3,subol in zip(li.findall("h3"), li.findall("ol")):
            pdf_url = page_range = ""
            fr_matt = subol.cssselect("li.front-matter-item")
            if len(fr_matt) != 0:
                page_range = fr_matt[0].cssselect("p.page-range")[0].text_content()
                if fr_matt[0].find("a"):
                    pdf_url = fr_matt[0].find("a").attrib["href"]
            append_ch(chl, subh3.text_content().strip(), \
                getTocRec(subol), pdf_url, [], page_range)
              
    def parseChItem(chl,li):
        try: title = li.find("h3").text_content()
        except:
            title = li.cssselect("p.title")[0].text_content().strip()
        try: 
            link = li.cssselect("span.action a")[0]
            pdf_url = link.attrib["href"] if "Download PDF" in link.text_content() else ""
        except: pdf_url = ""
        append_ch(chl, title, [], pdf_url, \
            [x.find("a").text_content().strip() \
                for x in li.cssselect("li[itemprop=author]")], \
            li.cssselect("p.page-range")[0].text_content(), "no-access" in li.attrib['class'])
     
    def getTocRec(ol):
        chl = []
        for li in ol.findall("li"):
            if "part-item" in li.attrib['class']: parsePartItem(chl,li)
            else: parseChItem(chl,li)
        return chl
    
    return getTocRec(div.find("ol"))

def fetchCover(isbn,size):
    try:
        webImg = util.connect("%s/covers/%s.tif" \
                       % (SPR_IMG_URL,isbn))
        tmp_img    = NamedTemporaryFile(delete=False,suffix=".tif")
        tmp_pdfimg = NamedTemporaryFile(delete=False,suffix=".pdf")
        tmp_img.write(webImg.read()); tmp_img.close()
        cmd = [IM_BIN, "-resize","%fx%f" % (2*size[0], 2*size[1]), \
                   "-density", "140", tmp_img.name,tmp_pdfimg.name]
        p = Popen(cmd,stdout=PIPE,stderr=PIPE)
        p.communicate(); os.remove(tmp_img.name)
        return tmp_pdfimg
    except (URLError, BadStatusLine):
        return None
        
