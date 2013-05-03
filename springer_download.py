#!/usr/bin/env python

import sys, string
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
        print "ImageMagick: %s" % IM_BIN
        print "Ghostscript: %s" % GS_BIN
        print "PDF Toolkit: %s" % PDFTK_BIN
        
    interface.doing(_("Fetching book info"))
    soup = util.getSoup(book_url)
    if soup == None:
        interface.err(_("The specified identifier doesn't point to an existing Springer book resource"))
        return False
    info = meta.fetchBookInfo(soup)
    interface.done()
    
    interface.out(", ".join(info['authors']))
    bookinfo = info['title']
    if info['subtitle'] != None:
        bookinfo += ": %s" % (info['subtitle'])
    bookinfo += " (%d chapters)" % (info['chapter_cnt'])
    interface.out(bookinfo)
    
    interface.doing(_("Fetching chapter data"))
    toc = meta.fetchToc(soup, book_url)
    if interface.option('sorted'):
        toc = sorted(toc, key=lambda el: el['page_range'][0])
    accessible_toc = util.getAccessibleToc(toc)
    interface.done()
    
    if interface.option('verbose'): util.printToc(accessible_toc)
    
    download.pdf_files(accessible_toc, interface.progress(""), \
        interface.option('pause'), info['chapter_cnt'])
        
    inputPDF = PdfFileReader(accessible_toc[0]['pdf_file'])
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
                accessible_toc.insert(0,{
                    'pdf_file': cover,
                    'children': [],
                    'page_range': [0,0],
                    'title': "Cover",
                })
                interface.done()
            else:
                interface.done(_("not available"))
    
    outf = interface.option('output-file')
    if outf == None:
        if interface.option('autotitle'):
            outf = "%s - %s.pdf" % (", ".join(info['authors']), \
                                            info['title'])
        else:
            outf = info['online_isbn']+".pdf"
    valid_chars = "-_.,() %s%s" % (string.ascii_letters, string.digits)
    outf = "".join(c if c in valid_chars else "_" for c in outf)
    
    merge.merge_by_toc(accessible_toc, info, outf, interface)
    
    return True
    
if __name__ == "__main__":
    sys.exit(main())
      
   
