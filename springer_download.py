#!/usr/bin/env python

import sys, string, shutil, os
from gettext import gettext as _

from springerdl import meta, util, download, merge
from springerdl.pyPdf_ext import PdfFileReader_ext as PdfFileReader
from springerdl.const import *

def main(argv=sys.argv):
    from os import isatty
    if (isatty(0) or len(argv) > 1) and "--gui" not in  argv[1:]:
        from springerdl.interface.cli import cli_main
        interface = cli_main
    else:
        from springerdl.interface.gui import gui_main
        interface = gui_main
        
    interface(springer_fetch)
    return 0
    
def springer_fetch(interface):
    util.setupOpener(interface.option("proxy"), interface.option("user-agent"))
    
    springer_key = util.parseSpringerURL(interface.option("springer_name"))
    book_url = '%s/book/10.1007/%s' % (SPRINGER_URL, springer_key)
    if interface.option('verbose'):
        print("ImageMagick: %s" % IM_BIN)
        print("Ghostscript: %s" % GS_BIN)
        print("PDF Toolkit: %s" % PDFTK_BIN)
        
    interface.doing(_("Fetching book info"))
    root = util.getElementTree(book_url)
    if root == None:
        interface.err(_("The specified identifier doesn't point to an existing Springer book resource"))
        return False
    info = meta.fetchBookInfo(root)
    interface.done()
    
    interface.out(", ".join(info['authors']))
    bookinfo = info['title']
    if info['subtitle'] != None:
        bookinfo += ": %s" % (info['subtitle'])
    bookinfo += " ("
    bookinfo += _("%d chapters") % (info['chapter_cnt'])
    if info['full_pdf'] != None:
        bookinfo += _(", full book PDF available")
    bookinfo += ")"
    interface.out(bookinfo)
    if info['noaccess'] and interface.option('force-full-access'):
        sys.exit()
    
    outf = interface.option('output-file')
    valid_chars = "-_.,() %s%s" % (string.ascii_letters, string.digits)
    if outf == None:
        if interface.option('autotitle'):
            outf = "%s - %s.pdf" % (", ".join(info['authors']), \
                                            info['title'])
        else:
            outf = info['online_isbn']+".pdf"
        outf = "".join(c if c in valid_chars else "_" for c in outf)
    
    basename = os.path.basename(outf)
    target_dir = os.path.dirname(outf)
    if target_dir == "": target_dir = os.getcwd()
    basename = "".join(c if c in valid_chars else "_" for c in basename)
    outf = os.path.join(target_dir, basename)
        
    if info['full_pdf'] != None:
        pgs = interface.progress(_("Downloading %d/%d kB"))
        pdf = download.fetch_pdf_with_pgs(info['full_pdf'], pgs)
        pgs.destroy()
        interface.doing(_("Moving downloaded file to %s") % (target_dir))
        shutil.move(pdf.name, outf)
        interface.done()
        return 0
    
    interface.doing(_("Fetching chapter data"))
    toc = meta.fetchToc(root, book_url)
    if interface.option('sorted'):
        toc = sorted(toc, key=lambda el: el['page_range'][0])
    interface.done()
    
    if interface.option('use-pdfs') != None:
        data = [0, interface.option('use-pdfs')[:]]
        def count_pdfs(el, _, d):
            if el['noaccess'] != None or el['pdf_url'] != "":
                interface.out("%s = %s" % (d[1][d[0]],el['title']))
                el['pdf_file'] = open(d[1][d[0]], "rb")
                d[0] += 1
        util.tocIterateRec(toc, count_pdfs, data)
        if interface.option('verbose'): print(util.printToc(toc))
        if data[0] != len(data[1]):
            interface.err(_("Expected %d pdf files, got %s!") % 
                (pdf_total_count[0], len(interface.option('use-pdfs'))))
            return 1
    else:
        toc = util.getAccessibleToc(toc)
        if interface.option('verbose'): print(util.printToc(toc))
        download.pdf_files(toc, interface.progress(""), \
            interface.option('pause'))
        
    inputPDF = PdfFileReader(toc[0]['pdf_file'])
    tmp_box = inputPDF.pages[0].mediaBox
    info['pagesize'] = (tmp_box[2], tmp_box[3])
    if interface.option('cover'):
        if IM_BIN == None:
            interface.err(_("Skipping cover due to missing ImageMagick binary."))
        else:
            interface.doing(_("Fetching book cover"))
            cover = meta.fetchCover(info['print_isbn'], \
                info['pagesize'])
            if cover:
                toc.insert(0, {
                    'pdf_file': cover,
                    'children': [],
                    'page_range': [0,0],
                    'title': "Cover",
                })
                interface.done()
            else:
                interface.done(_("not available"))
    
    if interface.option('download-only'):
        interface.doing(_("Moving downloaded files to %s") % (target_dir))
        file_list = []
        def append_to_list(el, _, flist):
            if 'pdf_file' in el and el['pdf_file'] != None:
                flist.append([el['title'], el['pdf_file']])
        util.tocIterateRec(toc, append_to_list, file_list)
        for i,f in enumerate(file_list):
            if interface.option('autotitle'): 
                chpt = "".join(c if c in valid_chars else "_" for c in f[0])
                chpt += ".pdf"
            else:
                chpt = basename
            target_base = "%02d-%s" % (i, chpt)
            f[1].close()
            shutil.move(f[1].name, os.path.join(target_dir, target_base))
        interface.done()
    else:
        merge.merge_by_toc(toc, info, outf, interface)
    
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
      
   
