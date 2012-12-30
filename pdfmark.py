
from util import decodeForSure
from time import localtime, strftime
   
################################################################################
############################# meta to pdfmark  #################################
################################################################################

def _uniconvHex(s):
   out = ""; s = decodeForSure(s)
   for c in s:
      out += str(hex(ord(c)))[2:].upper().rjust(4,"0")
   return out

def infoToPdfMark(i):
   marks = "["
   if i['title']:    marks += " /Title <FEFF%s>" % (_uniconvHex(i['title']))
   if i['subtitle']: marks += " /Subject <FEFF%s>" % (_uniconvHex(i['subtitle']))
   if i['authors']:  marks += " /Author <FEFF%s>" % (_uniconvHex(", ".join(i['authors'])))
   if i['year']:     marks += " /CreationDate (D:%s)" % (i['year'])
   marks += " /ModDate (D:%s)" % (strftime("%Y%m%d%H%M%S",localtime()))
         +  " /Creator (springer_download.py)"
         +  " /Producer (springer_download.py)"
         +  " /DOCINFO pdfmark\n"
   return marks

def tocToPdfmark(toc,filt=lambda x:x):
   marks = ""
   for a,b,c,d in toc:
      marks += "["
      if d > 0:
         marks += "/Count -%d " % (d)
      marks += "/Title <FEFF%s> /View [/XYZ null null null] /Page %d  /OUT pdfmark\n" \
                           % (_uniconvHex(filt(a.strip())),b)
   return marks
   
def labelsToPdfmark(pls):
   if len(pls) == 0:
      return ""
   mark = "[/_objdef {pl} /type /dict /OBJ pdfmark\n"
   mark += "[{pl} <</Nums ["
   tmp = []
   s = ""
   for label in pls:
      s = "%d <<" % (label[0])
      tmp2 = []
      for (i,j) in label[1].items():
         if type(j) == pyPdf.generic.TextStringObject:
            j = "(%s)" % (j)
         tmp2.append("%s %s" % (i,j))
      s += " ".join(tmp2)
      s += ">>"
      tmp.append(s)
   mark += " ".join(tmp)
   mark += "]>> /PUT pdfmark\n"
   mark += "[{Catalog} <</PageLabels {pl}>> /PUT pdfmark"
   return mark
   

