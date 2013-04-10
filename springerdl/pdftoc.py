
import pyPdf

from .util import decodeForSure
   
################################################################################
########################## PDF toc and labels  #################################
################################################################################

def _getDestinationPageNumbers(pdf):
    def _setup_outline_page_ids(outline, _result=None,lvl=0):
        if _result is None:
            _result = {}
        for obj in outline:
            if isinstance(obj, pyPdf.pdf.Destination) and not \
                isinstance(obj.page, pyPdf.generic.NullObject):
                _result[(id(obj), obj.title)] = (obj.page.idnum,lvl)
            elif isinstance(obj, list):
                _setup_outline_page_ids(obj, _result,lvl+1)
        return _result

    def _setup_page_id_to_num(pages=None, _result=None, _num_pages=None):
        if _result is None:
            _result = {}
        if pages is None:
            _num_pages = [1]
            pages = pdf.trailer["/Root"].getObject()["/Pages"].getObject()
        t = pages["/Type"]
        if t == "/Pages":
            for page in pages["/Kids"]:
                _result[page.idnum] = len(_num_pages)
                _setup_page_id_to_num(page.getObject(), _result, _num_pages)
        elif t == "/Page":
                _num_pages.append(1)
        return _result

    try:
        outline_page_ids = _setup_outline_page_ids(pdf.getOutlines())
    except ValueError:
        "This should not happen, but does e.g. with 978-1-4419-6757-2!"
        return None
    page_id_to_page_numbers = _setup_page_id_to_num()

    result = []
    for (_, title), (page_idnum,lvl) in outline_page_ids.iteritems():
        if page_id_to_page_numbers.get(page_idnum) != None:
            result.append([title,page_id_to_page_numbers.get(page_idnum),lvl])
    return result
   
def getTocFromPdf(pdf,shift=0,default=None,baselvl=0,child_cnt=0):
    ch = _getDestinationPageNumbers(pdf)
    if ch == None: return []
    ch.sort(key=lambda x: x[1:3])
    ch = [[decodeForSure(x[0]),x[1]+shift,x[2]+baselvl] for x in ch]
    for i in range(len(ch)):
        j = k = 0
        while i+j+1 < len(ch) and ch[i+j+1][2] > ch[i][2]:
            k += 1 if ch[i+j+1][2] == ch[i][2]+1 else 0
            j += 1
        ch[i].append(k)
    if len(ch) == 0 and default != None:
        ch.append([default,1+shift,baselvl,child_cnt])
    return ch
   
def getPagelabelsFromPdf(pdf,shift=0,start=None):
    if start == None:
        start = shift
    try:
        pldef = pdf.trailer["/Root"]["/PageLabels"]["/Nums"]
    except KeyError:
        pldef = []
    pls = []
    for i in range(0,len(pldef),2):
        pls.append([int(pldef[i])+shift,pldef[i+1].getObject()])
    if len(pls) == 0:
        if start < 0:
            pls.append([shift,{"/S":"/r","/St":str(1000+start)}])
        else:
            pls.append([shift,{"/S":"/D","/St":str(start)}])
    return pls
         
