
from time import localtime, strftime
from tempfile import NamedTemporaryFile

from .util import decodeForSure
   
################################################################################
############################# meta to pdfmark  #################################
################################################################################

def _uniconvHex(s):
    out = ""; s = decodeForSure(s)
    for c in s:
        out += str(hex(ord(c)))[2:].upper().rjust(4,"0")
    return out

def infoToPdfmark(i):
    marks = "["
    for x,v in zip(['title','subtitle','authors','year'],\
                    ['/Title','/Subject','/Author','/CreationDate']):
        if i[x]: 
            s = ", ".join(i[x]) if x == 'authors' else i[x]
            if x == 'year': s = "(D:%s)" % (s)
            else: s = "<FEFF"+_uniconvHex(s)+">"
            marks += " %s %s" % (v,s)
    marks += " /ModDate (D:%s)" % (strftime("%Y%m%d%H%M%S",localtime())) \
            +  " /Creator (springer_download.py)" \
            +  " /Producer (springer_download.py)" \
            +  " /DOCINFO pdfmark\n"
    return marks

def tocToPdfmark(toc,filt=lambda x:x):
    def convertTocAtoB(tA,lt):
        i = 0; tB = []
        while i < lt:
            ch = { 'title': tA[i][0] }
            if i+1 < len(tA): 
                if tA[i+1][1] == tA[i][1]:
                    ch['page_range'] = (tA[i][1],tA[i][1])
                else:
                    ch['page_range'] = (tA[i][1],tA[i+1][1]-1)
            else: ch['page_range'] = (tA[i][1],tA[i][1])
            j = i+1
            while j < lt and tA[j][2] > tA[i][2]: j+=1
            ch['children'] = convertTocAtoB(tA[i+1:],j-i-1)
            i = j; tB.append(ch)
        return tB
        
    tocB = convertTocAtoB(toc,len(toc))
    def getmark(t):
        m = ""
        for c in t:
            m += "["
            if len(c['children']) > 0: m += "/Count -%d " % (len(c['children']))
            m += "/Title <FEFF%s> /View [/XYZ null null null] /Page %d  /OUT pdfmark\n" \
                               % (_uniconvHex(filt(c['title'].strip())),c['page_range'][0])
            if len(c['children']) > 0: m += getmark(c['children'])
        return m
    return getmark(tocB)
   
def labelsToPdfmark(pls):
    if len(pls) == 0: return ""
    mark = "[/_objdef {pl} /type /dict /OBJ pdfmark\n[{pl} <</Nums ["
    tmp = []
    for label in pls:
        tmp2 = ["%s %s" % (i,j) for (i,j) in label[1].items()]
        tmp.append("%d <<%s>>" % (label[0]," ".join(tmp2)))
    mark += " ".join(tmp)
    mark += "]>> /PUT pdfmark\n"
    mark += "[{Catalog} <</PageLabels {pl}>> /PUT pdfmark"
    return mark
    

def getNoopFile():
    f = NamedTemporaryFile(prefix='pdfmark-noop-', delete=False)
    f.write("""
        /originalpdfmark { //pdfmark } bind def
        /pdfmark
        {
            {
                { counttomark pop }
                stopped
                { /pdfmark errordict /unmatchedmark get exec stop }
                if

                dup type /nametype ne
                { /pdfmark errordict /typecheck get exec stop }
                if

                dup /OUT eq
                { (Skipping OUT pdfmark\n) print cleartomark exit }
                if

                originalpdfmark exit
            } loop
        } def
    """)
    f.close()
    return f

def getRestoreFile():
    f = NamedTemporaryFile(prefix='pdfmark-restore-', delete=False)
    f.write('/pdfmark { originalpdfmark } bind def\n')
    f.close()
    return f

