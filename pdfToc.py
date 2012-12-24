
from util import uniconvHex, decodeForSure
   
################################################################################
########################## PDF toc and labels  #################################
################################################################################

import pyPdf

def getDestinationPageNumbers(pdf):
   def _setup_outline_page_ids(outline, _result=None,lvl=0):
       if _result is None:
           _result = {}
       for obj in outline:
           if isinstance(obj, pyPdf.pdf.Destination):
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

   outline_page_ids = _setup_outline_page_ids(pdf.getOutlines())
   page_id_to_page_numbers = _setup_page_id_to_num()
   
   result = []
   for (_, title), (page_idnum,lvl) in outline_page_ids.iteritems():
       result.append([title,page_id_to_page_numbers.get(page_idnum, '???'),lvl])
   return result
   
def getTocFromPdf(pdf,shift=0,default=None,baselvl=0,child_cnt=0):
   ch = getDestinationPageNumbers(pdf)
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

def tocToPdfmark(toc,filt=lambda x:x):
   marks = ""
   for a,b,c,d in toc:
      marks += "["
      if d > 0:
         marks += "/Count -%d " % (d)
      marks += "/Title <FEFF%s> /View [/XYZ null null null] /Page %d  /OUT pdfmark\n" \
                           % (uniconvHex(filt(a.strip())),b)
   return marks
   
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

if __name__ == "__main__":
   import argparse

   parser = argparse.ArgumentParser(description='Extract table of contents from pdf document')
   parser.add_argument('pdffile', metavar='FILE', type=str, 
                     help='Path to pdf file.')
   parser.add_argument('--pdfmarks', action="store_true", default=False,
                     help='Output TOC as pdfmarks')
   args = parser.parse_args()
   
   pdf = pyPdf.PdfFileReader(open(args.pdffile,"r"))
   toc = getTocFromPdf(pdf)
   if args.pdfmarks == True:
      print tocToPdfmark(toc)
      print labelsToPdfmark(getPagelabelsFromPdf(pdf))
   else:
      for x in toc:
         print x[0]
      
         
