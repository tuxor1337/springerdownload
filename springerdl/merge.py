
import shutil, sys
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from gettext import gettext as _

from . import util, pdfmark
from .const import *
from .pyPdf_ext import PdfFileReader_ext as PdfFileReader
        
def merge_by_toc(toc, info, outf, interface):
    data = {
        "pdf_cnt": 0,
        "files": [],
        "labels": [],
        "interface": interface,
        "total_pages": 0,
        "extracted_toc": [],
        "page_size": info['pagesize'],
    }
    util.tocIterateRec(toc, _processCh, data)
    cat_pdf = NamedTemporaryFile(delete=False)
    if PDFTK_BIN != None:
        pdftk_cat(data['files'], cat_pdf, interface)
    elif GS_BIN != None:
        o = gs_cat(data['files'], cat_pdf, interface)
        if interface.option('verbose'):
            interface.out(_("Ghostscript stdout:"))
            interface.out(o[0])
            interface.out(_("Ghostscript stderr:"))
            interface.out(o[1])
    else:
        interface.err(_("Need either ghostscript or pdftk for concatenation."))
        sys.exit(1)
        
    cat_pdf.flush(); cat_pdf.seek(0)
    if GS_BIN != None and interface.option('skip-meta') == False:
        pdfmarks = pdfmark.infoToPdfmark(info)
        pdfmarks += pdfmark.tocToPdfmark(data['extracted_toc'],util.repairChars)
        pdfmarks += pdfmark.labelsToPdfmark(data['labels'])
        o = gs_meta(cat_pdf, pdfmarks, outf, interface, data['total_pages'])
        if interface.option('verbose'):
            interface.out(_("Ghostscript stderr:"))
            interface.out(o)
    else:
        if GS_BIN == None:
            interface.err(_("No Ghostscript binary found."))
        interface.out(_("Skipping PDF meta info."))
        interface.doing(_("Copying %s to %s...") % (cat_pdf.name, outf))
        shutil.copy(cat_pdf.name,outf)
        interface.done()
    for f in data['files']:
        f.close()
        if interface.option("use-pdfs") == None:
            os.unlink(f.name)
    cat_pdf.close()
    os.remove(cat_pdf.name)
    interface.out(_("Output written to %s!") % (outf))
    

def _processCh(el, lvl, data):
    if data['interface'].option('skip-meta') == False:
        if 'pdf_file' in el and el['pdf_file'] != None:
            if data['interface'].option('blanks'):
                if data['interface'].option('dbpage'):
                    test_n = (5-(data['total_pages']%4))%4
                    for x in range(test_n):
                        _insertBlankPage(data)
                else:
                    if 1 == data['total_pages'] % 2:
                        _insertBlankPage(data)
            inputPDF = PdfFileReader(el['pdf_file'])
            data['extracted_toc'] += inputPDF.getToc(data['total_pages'],\
                el['title'],lvl,len(el['children']))
            pr = el['page_range'][0] if el['page_range'][0] != 0 else -999
            if el['title'] == "Cover":
                data['labels'] += [[0,{"/P":"(Cover)"}],[1,{"/S":"/D"}]]
            else:
                data['labels'] += inputPDF.getPagelabels(data['total_pages'], pr)
            el['page_cnt'] = inputPDF.getNumPages()
            data['total_pages'] += inputPDF.getNumPages()
        else:
            data['extracted_toc'].append([el['title'],1+data['total_pages'],\
                lvl,len(el['children'])])
    if 'pdf_file' in el and el['pdf_file'] != None:
        data['files'].append(el['pdf_file'])

def _insertBlankPage(data):
    tmp_blankpdf = NamedTemporaryFile(delete=False,suffix=".pdf")
    cmd = [GS_BIN,"-dBATCH","-dNOPAUSE","-sDEVICE=pdfwrite",\
           "-dDEVICEWIDTHPOINTS=%f" % data['page_size'][0],\
           "-dDEVICEHEIGHTPOINTS=%f" % data['page_size'][1],\
           "-sOutputFile=%s" % tmp_blankpdf.name]
    Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    data['files'].append(tmp_blankpdf)
    data['total_pages'] += 1
   
def gs_cat(pdf_list, outf, interface):
    interface.doing(_("Concatenating"))
    cmd = [GS_BIN,"-dBATCH","-dNOPAUSE","-sDEVICE=pdfwrite",\
           "-dAutoRotatePages=/None","-sOutputFile="+outf.name]
    cmd.extend([f.name for f in pdf_list])
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    outp = p.communicate()
    interface.done()
    return [outp[0].strip(),outp[1].strip()]
        
def pdftk_cat(pdf_list, outf, interface):
    interface.doing(_("Concatenating"))
    cmd = [PDFTK_BIN]
    cmd.extend([f.name for f in pdf_list])
    cmd.extend(["cat","output", outf.name])
    Popen(cmd).communicate()
    interface.done()

def gs_meta(pdf, pdfmarks, outf, interface, page_cnt):
    pdfmark_file = NamedTemporaryFile(delete=False)
    pdfmark_file.write(pdfmarks)
    pdfmark_file.flush(); pdfmark_file.seek(0)
    cmd = [GS_BIN,"-dBATCH","-dNOPAUSE","-sDEVICE=pdfwrite",\
           "-dAutoRotatePages=/None","-sOutputFile="+outf,\
           pdf.name, pdfmark_file.name]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    pgs = interface.progress(_("Writing to file (page %d of %d)"))
    pgs.update(0,page_cnt)
    for line in iter(p.stdout.readline,""):
        if "Page" in line:
            pgs.update(int(line.replace("Page ","").strip()),page_cnt)
    pdfmark_file.close()
    os.remove(pdfmark_file.name)
    pgs.destroy()
    outp = p.communicate()
    return outp[1].strip()

