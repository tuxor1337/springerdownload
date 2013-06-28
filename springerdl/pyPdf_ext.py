from .util import decodeForSure

try:
    import pyPdf
except ImportError:
    import springerdl.PyPDF2 as pyPdf

def _new_createStringObject(string):
    if isinstance(string, unicode):
        return pyPdf.generic.TextStringObject(string)
    elif isinstance(string, str):
        if string.startswith(pyPdf.generic.codecs.BOM_UTF16_BE):
            try:
                retval = pyPdf.generic.TextStringObject(string.decode("utf-16"))
                retval.autodetect_utf16 = True
                return retval
            except UnicodeDecodeError:
                pass
        try:
            retval = pyPdf.generic.TextStringObject(
                pyPdf.generic.decode_pdfdocencoding(string)
            )
            retval.autodetect_pdfdocencoding = True
            return retval
        except UnicodeDecodeError:
            return pyPdf.generic.ByteStringObject(string)
    else:
        raise TypeError("createStringObject should have str or unicode arg")
pyPdf.generic.createStringObject = _new_createStringObject

class PdfFileReader_ext(pyPdf.PdfFileReader):
    def _buildOutline(self, node):
        try:
            return super(PdfFileReader_ext, self)._buildOutline(node)
        except pyPdf.utils.PdfReadError as e:
            print("%s" % e)
            return None

    def _getDestinationPageNumbers(self):
        def _setup_outline_page_ids(outline, _result=None,lvl=0):
            if _result is None:
                _result = {}
            for obj in outline:
                if isinstance(obj, pyPdf.pdf.Destination) and \
                    hasattr(obj.page, 'idnum'):
                    _result[(id(obj), obj.title)] = (obj.page.idnum,lvl)
                elif isinstance(obj, list):
                    _setup_outline_page_ids(obj, _result,lvl+1)
            return _result

        def _setup_page_id_to_num(pages=None, _result=None, _num_pages=None):
            if _result is None:
                _result = {}
            if pages is None:
                _num_pages = [1]
                pages = self.trailer["/Root"].getObject()["/Pages"].getObject()
            t = pages["/Type"]
            if t == "/Pages":
                for page in pages["/Kids"]:
                    _result[page.idnum] = len(_num_pages)
                    _setup_page_id_to_num(page.getObject(), _result, _num_pages)
            elif t == "/Page":
                    _num_pages.append(1)
            return _result

        try:
            outline_page_ids = _setup_outline_page_ids(self.getOutlines())
        except ValueError:
            "This should not happen, but does e.g. with 978-1-4419-6757-2!"
            return None
        page_id_to_page_numbers = _setup_page_id_to_num()

        result = []
        for (_, title), (page_idnum,lvl) in outline_page_ids.iteritems():
            if page_id_to_page_numbers.get(page_idnum) != None:
                result.append([title,page_id_to_page_numbers.get(page_idnum),lvl])
        return result
        
    def getToc(self,shift=0,default=None,baselvl=0,child_cnt=0):
        ch = self._getDestinationPageNumbers()
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
        
    def getPagelabels(self,shift=0,start=None):
        if start == None:
            start = shift
        try:
            pldef = self.trailer["/Root"]["/PageLabels"]["/Nums"]
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
  
