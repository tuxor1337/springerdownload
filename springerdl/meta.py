
import re, os

from urllib2 import URLError
from httplib import BadStatusLine
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE

from . import util
from .const import *

def fetchBookInfo(soup):
    info = []
    author_list = soup.find("div", {"class" : "summary"})\
                    .findAll("li", {"itemprop":"author"})
    if len(author_list) == 0:
        author_list = soup.find("div", {"class" : "summary"})\
                    .findAll("li", {"itemprop":"editor"})
    chapter_cnt = soup.find("span", {"class" : "chapter-count" })
    m = re.search(r'\(([0-9\.]+) chapters\)', util.cleanSoup(chapter_cnt))
    def get_id(x):
        el = soup.find(attrs={"id" : x})
        return util.cleanSoup(el) if el != None else None
    info = {
        'authors' : [x.a.string for x in author_list],
        'chapter_cnt' : int(m.group(1)),
        'title' : get_id("abstract-about-title"),
        'subtitle' : get_id("abstract-about-book-subtitle"),
        'print_isbn' : get_id("abstract-about-book-print-isbn"),
        'online_isbn' : get_id("abstract-about-book-online-isbn"),
        'publisher' : get_id("abstract-about-publisher"),
        'year' : get_id("abstract-about-book-chapter-copyright-year")
    }
                
    return info

def fetchToc(soup, book_url):
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

    tmp_dpc = soup.find("span", {"class" : "number-of-pages" })
    dl_page_cnt = int(tmp_dpc.string) if tmp_dpc != None else 1
    for i in range(1,dl_page_cnt+1):
        toc = tocMerge(toc,_tocFromDiv(soup.find("div", {"class" : "toc"})))
        if i < dl_page_cnt:
            soup = util.getSoup("%s/page/%d"  % (book_url,i+1))
    return toc

def _tocFromDiv(div):
    def append_ch(ch_list,title="", children=[], pdf_url="", \
              authors=[], page_range="", noaccess=None):
        title = title.replace("\n"," ")
        m = re.search(r'Pages ([0-9A-Z]+)-([0-9A-Z]+)', 
           page_range,re.I)
        try:
            page_range = [m.group(1),m.group(2)]
            if not page_range[0].isnumeric():
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
        ch_list.append({'children':children,
            'title':title, 'pdf_url':pdf_url,'noaccess': noaccess,
            'authors':authors, 'page_range':page_range})
  
    def parsePartItem(chl,li):
        for subh3,subol in zip(li("h3",recursive=False), \
                               li("ol",recursive=False)):
            pdf_url = page_range = ""
            fr_matt = subol("li",recursive=False, \
                attrs={"class":re.compile(r'\bfront-matter-item\b')})
            if len(fr_matt) != 0:
               fr_matt = fr_matt[0].extract()
               pdf_url = fr_matt("a")[0]["href"]
               page_range = util.cleanSoup(fr_matt.find("p",\
                                             {"class" : "page-range" }))
            append_ch(chl, util.cleanSoup(subh3).strip(), \
                getTocRec(subol), pdf_url, [],page_range)
              
    def parseChItem(chl,li):
        try: title = util.cleanSoup(li.h3)
        except:
            title = util.cleanSoup(li("p", recursive=False, \
               attrs={"class":re.compile(r'\btitle\b')})[0]).strip()
        try: 
            link = li.find("span",{"class":"action"}).a
            pdf_url = link["href"] if "Download PDF" in util.cleanSoup(link) else ""
        except: pdf_url = ""
        append_ch(chl, title, [], pdf_url, \
            [util.cleanSoup(x.a).strip() \
                for x in li("li", {"itemprop" : "author"})], \
            util.cleanSoup(li.find("p", {"class" : "page-range" })), \
            "no-access" in li['class'])
     
    def getTocRec(ol):
        chl = []
        for li in ol("li",recursive=False):
            if "part-item" in li['class']: parsePartItem(chl,li)
            else: parseChItem(chl,li)
        return chl
    
    return getTocRec(div.ol)

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
        
