

"""
First attempt to implement Python 3 support. There is still a long way to go
though, mainly because there is no pyPdf (or PyPdf2) for Python 3.
"""
try:
    from urllib2 import urlopen, URLError
    from httplib import BadStatusLine
except:
    from urllib.request import urlopen
    from urllib.error import URLError
    from http.client import BadStatusLine
    
import os, re, random, time, shutil
from subprocess import Popen, PIPE
from tempfile import TemporaryFile, NamedTemporaryFile
from pyPdf import PdfFileWriter, PdfFileReader
from gettext import gettext as _

from util import *
from pdftoc import *
from pdfmark import *

SPRINGER_URL = "http://link.springer.com"
SPR_IMG_URL  = "http://images.springer.com"

BINPATH = { "gs": None, "pdftk": None, "convert": None}
for p in reversed(os.getenv("PATH").split(":")):
    for f in ["gs","convert","pdftk"]:
        candidate = os.path.join(p,f)
        if os.path.isfile(candidate):
            BINPATH[f] = candidate

GS_BIN = BINPATH['gs']
IM_BIN = BINPATH['convert']
PDFTK_BIN = BINPATH['pdftk']

options_default = {
    "cover": True,
    "autotitle": False,
    "pause": 0,
    "blanks": False,
    "dbpage": False,
    "pdftk": False,
    "verbose": False,
}

################################################################################
################################## Fetcher #####################################
################################################################################
   
class springerFetcher(object):
    def __init__(self, springer_id, outf, p, options):
        self.opts = options
        for key in options_default:
            if key not in options:
                self.opts[key] = options_default[key]
        self.p, self.outf = p, outf
        self.key = self.parseSpringerURL(springer_id)
        self.book_url = '%s/book/10.1007/%s' % (SPRINGER_URL,self.key)
        self.outputPDF = PdfFileWriter(); self.labels = []
        self.total_pages = 0; self.extracted_toc = []
        self.chPdf = []
        
    def parseSpringerURL(self,url):
        url = url.replace("http://","")
        url = url.replace("link.springer.com/","")
        if "/" not in url:
            return url
        m = re.search(r'(book|referencework)/([^/]*)/([^/]*)', url)
        try:
            return m.group(3)
        except:
            return None
            
    def pauseBeforeHttpGet(self):
        if self.opts['pause'] > 0:	
            time.sleep((0.6 + random.random()*0.8)*self.opts['pause'])
    
    def insertBlankPage(self):
        tmp_blankpdf = NamedTemporaryFile(delete=False,suffix=".pdf")
        cmd = [GS_BIN,"-dBATCH","-dNOPAUSE","-sDEVICE=pdfwrite",\
               "-dDEVICEWIDTHPOINTS=%f" % self.info['pagesize'][0],\
               "-dDEVICEHEIGHTPOINTS=%f" % self.info['pagesize'][1],\
               "-sOutputFile=%s" % tmp_blankpdf.name]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE)
        p.communicate(input="")
        tmp_blankp = PdfFileReader(tmp_blankpdf)
        self.outputPDF.addPage(tmp_blankp.pages[0])
        self.total_pages += 1
   
    def run(self):
        if self.opts['verbose']:
            self.p.out(_("External paths:"))
            self.p.out("ImageMagick: %s" % IM_BIN)
            self.p.out("Ghostscript: %s" % GS_BIN)
            self.p.out("PDF Toolkit: %s" % PDFTK_BIN)
        self.pauseBeforeHttpGet()
        self.soup = getSoup(self.book_url)
        if self.soup == None:
            self.p.err(_("The specified identifier doesn't point to an existing Springer book resource"))
            return
        self.p.doing(_("Fetching book info"))
        self.fetchBookInfo()
        self.p.done()
        self.p.out(", ".join(self.info['authors']))
        bookinfo = self.info['title']
        if self.info['subtitle'] != None:
            bookinfo += ": %s" % (self.info['subtitle'])
        bookinfo += " (%d chapters)" % (self.info['chapter_cnt'])
        self.p.out(bookinfo)
        self.p.doing(_("Fetching chapter data"))
        self.fetchToc()
        self.p.done()
        pgs = self.p.progress(_("Fetching chapter %d of %d"))
        self.fetchPdfData(pgs)
        pgs.destroy()
        self.p.doing(_("Preparing table of contents"))
        self.createPdfmark()
        self.p.done()
        self.write()
      
################################## Book Info ###################################

    def fetchBookInfo(self):
        self.info = []
        author_list = self.soup.find("div", {"class" : "summary"})\
                        .findAll("li", {"itemprop":"author"})
        if len(author_list) == 0:
            author_list = self.soup.find("div", {"class" : "summary"})\
                        .findAll("li", {"itemprop":"editor"})
        chapter_cnt = self.soup.find("span", {"class" : "chapter-count" })
        m = re.search(r'\(([0-9\.]+) chapters\)', cleanSoup(chapter_cnt))
        def get_id(x):
            el = self.soup.find(attrs={"id" : x})
            return cleanSoup(el) if el != None else None
        self.info = {
            'authors' : [x.a.string for x in author_list],
            'chapter_cnt' : int(m.group(1)),
            'title' : get_id("abstract-about-title"),
            'subtitle' : get_id("abstract-about-book-subtitle"),
            'print_isbn' : get_id("abstract-about-book-print-isbn"),
            'online_isbn' : get_id("abstract-about-book-online-isbn"),
            'publisher' : get_id("abstract-about-publisher"),
            'year' : get_id("abstract-about-book-chapter-copyright-year")
        }
        if not self.outf:
            if self.opts['autotitle']:
                self.outf = "%s - %s.pdf" % (", ".join(self.info['authors']),
                                                self.info['title'])
            else:
                self.outf = self.info['online_isbn']+".pdf"
   
################################ Fetch TOC #####################################

    def fetchToc(self):
        self.toc = []
        def tocMerge(toc1,toc2):
            if len(toc2) != 0 and len(toc1) != 0:
                mergeitem = toc2.pop(0)
                if toc1[-1]['title'] == mergeitem['title']:
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

        tmp_dpc = self.soup.find("span", {"class" : "number-of-pages" })
        dl_page_cnt = int(tmp_dpc.string) if tmp_dpc != None else 1
        for i in range(1,dl_page_cnt+1):
            self.toc = tocMerge(self.toc,\
                self.tocFromDiv(self.soup.find("div", {"class" : "toc"})))
            if i < dl_page_cnt:
                self.pauseBeforeHttpGet()
                self.soup = getSoup("%s/page/%d"  % (self.book_url,i+1))

    def tocFromDiv(self,div):
        def append_ch(ch_list,title="", children=[], pdf_url="", \
                  authors=[], page_range="", noaccess=None):
            m = re.search(r'Pages ([0-9IXVLCDM]+)-([0-9IXVLCDM]+)', 
               page_range,re.I)
            try:
                page_range = [m.group(1),m.group(2)]
                if not page_range[0].isnumeric():
                   page_range = [-1000+roman_to_int(x) for x in page_range]
                page_range = [int(x) for x in page_range]
            except AttributeError:
                page_range = [0,0]
            title = title.replace("\n"," ")
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
                   page_range = cleanSoup(fr_matt.find("p",\
                                                 {"class" : "page-range" }))
                append_ch(chl, cleanSoup(subh3).strip(), \
                    getTocRec(subol), pdf_url, [],page_range)
                  
        def parseChItem(chl,li):
            try: title = cleanSoup(li.h3)
            except:
                title = cleanSoup(li("p", recursive=False, \
                   attrs={"class":re.compile(r'\btitle\b')})[0]).strip()
            try: 
                link = li.find("span",{"class":"action"}).a
                pdf_url = link["href"] if "Download PDF" in cleanSoup(link) else ""
            except: pdf_url = ""
            append_ch(chl, title, [], pdf_url, \
                [cleanSoup(x.a).strip() \
                    for x in li("li", {"itemprop" : "author"})], \
                cleanSoup(li.find("p", {"class" : "page-range" })), \
                "no-access" in li['class'])
         
        def getTocRec(ol):
            chl = []
            for li in ol("li",recursive=False):
                if "part-item" in li['class']: parsePartItem(chl,li)
                else: parseChItem(chl,li)
            return chl
            
        return getTocRec(div.ol)
      
################################## Cover #######################################

    def fetchCover(self):
        try:
            webImg = urlopen("%s/covers/%s.tif" \
                           % (SPR_IMG_URL,self.info['print_isbn']))
            tmp_img    = NamedTemporaryFile(delete=False,suffix=".tif")
            tmp_pdfimg = NamedTemporaryFile(delete=False,suffix=".pdf")
            tmp_img.write(webImg.read()); tmp_img.close()
            cmd = [IM_BIN, "-resize","%fx%f" % (2*self.info['pagesize'][0],\
                                                2*self.info['pagesize'][1]),\
                       "-density", "140", tmp_img.name,tmp_pdfimg.name]
            p = Popen(cmd,stdout=PIPE,stderr=PIPE)
            p.communicate(); os.remove(tmp_img.name)
            tmp_cover = PdfFileReader(tmp_pdfimg)
            self.chPdf.insert(0,tmp_pdfimg)
            self.outputPDF.addPage(tmp_cover.pages[0])
            self.extracted_toc += getTocFromPdf(tmp_cover,self.total_pages,"Cover")
            self.labels += [[0,{"/P":"(Cover)"}],[1,{"/S":"/D"}]]
            self.total_pages += 1
            return True
        except (URLError, BadStatusLine):
            return False
            
############################ Fetch PDF Files ###################################

    def fetchPdfData(self,pgs=None):
        self.tmp_pgs_j = 0
      
        def getAccessibleChildren(t):
            new_t = []
            for i in range(len(t)):
                if not t[i]['noaccess']:
                    t[i]['children'] = getAccessibleChildren(t[i]['children'])
                if t[i]['pdf_url'] != "" or len(t[i]['children']) != 0:
                    new_t.append(t[i])
            return new_t
            
        accessible_toc = getAccessibleChildren(self.toc)
      
        def iterateRec(t,func,lvl=0):
            for el in t:
                el = func(el,lvl)
                if len(el['children']) != 0:
                    iterateRec(el['children'],func,lvl+1)
                
        def fetchCh(el,lvl):
            if el['pdf_url'] != "":
                pdf = NamedTemporaryFile(delete=False)
                self.pauseBeforeHttpGet()
                webPDF  = urlopen(SPRINGER_URL + el['pdf_url'])
                pdf.write(webPDF.read())
                inputPDF = PdfFileReader(pdf)
                self.chPdf.append(pdf)
                el['page_cnt'] = 0
                if self.tmp_pgs_j == 0:
                    tmp_box = inputPDF.pages[0].mediaBox
                    self.info['pagesize'] = (tmp_box[2], tmp_box[3])
                    if self.opts['cover']:
                        if IM_BIN == None:
                            self.p.err(_("Skipping book cover due to"
                                + " missing ImageMagick binary."))
                        else:
                            self.p.doing(_("Fetching book cover"))
                            if self.fetchCover():
                                self.p.done()
                            else:
                                self.p.done(_("not available"))
                    if pgs != None:
                        pgs.update(self.tmp_pgs_j,self.info['chapter_cnt'])
                    el['page_cnt'] = 1
                [self.outputPDF.addPage(x) for x in inputPDF.pages]
                self.extracted_toc += getTocFromPdf(inputPDF,self.total_pages,\
                            el['title'],lvl,len(el['children']))
                pr = el['page_range'][0] if el['page_range'][0] != 0 else -999
                self.labels += getPagelabelsFromPdf(inputPDF,\
                                          self.total_pages,pr)
                el['page_cnt'] += inputPDF.getNumPages()
                self.total_pages += inputPDF.getNumPages()
                if self.opts['blanks']:
                    if self.opts['dbpage']:
                        if self.tmp_pgs_j == 0:
                            test_n = (4-((el['page_cnt']-1)%4))%4
                        else: test_n = (4-(el['page_cnt']%4))%4
                        for x in range(test_n):
                            self.insertBlankPage()
                    else:
                        for x in range(el['page_cnt'] % 2):
                            self.insertBlankPage()
                self.tmp_pgs_j += 1
                if pgs != None:
                    pgs.update(self.tmp_pgs_j,self.info['chapter_cnt'])
            else:
                self.extracted_toc.append([el['title'],1+self.total_pages,\
                                                     lvl,len(el['children'])])
            return el
        iterateRec(accessible_toc,fetchCh)
      
############################ Output to file ####################################

    def createPdfmark(self):
        self.pdfmarks = infoToPdfmark(self.info)
        self.pdfmarks += tocToPdfmark(self.extracted_toc,repairChars)
        self.pdfmarks += labelsToPdfmark(self.labels)
    
    def gs_parse(self,pdf):
        pdfmark_file = NamedTemporaryFile(delete=False)
        pdfmark_file.write(self.pdfmarks)
        pdfmark_file.flush(); pdfmark_file.seek(0)
        cmd = [GS_BIN,"-dBATCH","-dNOPAUSE","-sDEVICE=pdfwrite",\
               "-dAutoRotatePages=/None","-sOutputFile="+self.outf,\
               "-",pdfmark_file.name]
        p = Popen(cmd, stdin=pdf, stdout=PIPE, stderr=PIPE)
        pgs = self.p.progress(_("Writing to file (page %d of %d)"))
        pgs.update(0,self.total_pages)
        for line in iter(p.stdout.readline,""):
            if "Page" in line:
                pgs.update(int(line.replace("Page ","").strip()),self.total_pages)
        pdfmark_file.close()
        os.remove(pdfmark_file.name)
        pgs.destroy()
        if self.opts['verbose']:
            self.p.out(_("Ghostscript stderr:"))
            self.p.out(p.communicate()[1].strip())
            
    def pdftk_cat(self,pdf):
        self.p.doing(_("Concatenating"))
        cmd = [PDFTK_BIN]
        cmd.extend([f.name for f in self.chPdf])
        cmd.extend(["cat","output", pdf.name])
        Popen(cmd).communicate()
        self.p.done()
      
    def write(self):
        pdf = NamedTemporaryFile()
        if self.opts['pdftk'] and PDFTK_BIN != None:
            self.pdftk_cat(pdf)
        else:
            if PDFTK_BIN == None:
                self.p.err(_("No pdftk binary found. Falling back to"
                    + " pyPdf.PdfFileWriter"))
            try:
                self.p.doing(_("Concatenating"))
                self.outputPDF.write(pdf)
                self.p.done()
            except UnicodeDecodeError, e:
                self.p.err(_("An unexpected error occurred."))
                self.p.err(e)
                if PDFTK_BIN != None:
                    self.p.out(_("Another attempt using pdftk."))
                else:
                    sys.exit(1)
        pdf.flush(); pdf.seek(0)
        if GS_BIN != None:
            self.gs_parse(pdf)
        else:
            self.p.err(_("No Ghostscript binary found. Skipping PDF meta info."))
            self.p.out(_("Copying %s to %s!") % (pdf.name,self.outf))
            shutil.copy(pdf.name,self.outf)
        for f in self.chPdf:
            f.close(); os.unlink(f.name)
        self.p.out(_("==> Output written to %s!") % (self.outf))
        
