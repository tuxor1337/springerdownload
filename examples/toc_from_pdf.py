
from springerdl.pdftoc import getTocFromPdf
import argparse, pyPdf

parser = argparse.ArgumentParser(description = 'Extract table of contents '\
                                             + 'from pdf document')
parser.add_argument('pdffile', metavar='FILE', type=str, 
                  help='Path to pdf file.')
parser.add_argument('--pdfmark', action="store_true", default=False,
                  help='Output TOC as pdfmarks.')
parser.add_argument('--gui', action="store_true", default=False,
                  help='Output TOC in a GUI. Overwrites --pdfmark.')
args = parser.parse_args()

pdf = pyPdf.PdfFileReader(open(args.pdffile,"r"))
toc = getTocFromPdf(pdf)

# There are two possible TOC formats.
# A) This is how pdfmark handles the table of contents:
#    A list of 4-tuples, where each tuple contains the following:
#     0) the chapter title
#     1) the page in the pdf document where the chapter starts
#     2) the chapter's level of nesting in the document's structure
#     3) the number of direct subchapters (not including subsubchapters)
#    This is clearly a low-level format, that doesn't store a lot of
#    information. Without the respective PDF document it's not even possible
#    to reconstruct the page range of the last chapter.
# B) This is the intuitive way of handling a table of contents:
#    A recursively defined list of python dictionaries, where each dict may
#    contain some meta information like "title", "subtitle", "authors" (a list),
#    "year" etc.
#    Each dict contains an entry "page_range" (a 2-tuple containing the page
#    numbers of the first and last page of the chapter, not including
#    subchapters) as well as an entry "children" which is in itself a list
#    describing a table of contents according to B.
# Conversion between A and B is not very difficult. But it's obviously
# not lossless, since B stores a lot more meta information along with each
# chapter's entire page range, whereas A only holds the page number of each
# chapter's first page.
# It's possible to think of a slight modification of A storing arbitrary meta
# information about each chapter - simply by replacing the first entry of each
# tuple (or even the whole tuple) by a dict. It came in handy to have such a
# reduced format though because it's what is naturally needed when handling 
# TOCs that come from PDF documents or that are to be used with pdfmark.
#
# "getTocFromPdf" returns a TOC in format A. But especially when working with
# GTK Tree Stores it's nice to have the TOC in format B. So we rather sketchily
# implement a function for this conversion task.

def convertTocAtoB(tA,lt):
    i = 0; tB = []
    while i < lt:
        ch = { 'title': tA[i][0] }
        if i+1 < len(tA): ch['page_range'] = (tA[i][1],tA[i+1][1]-1)
        else: ch['page_range'] = (tA[i][1],tA[i][1]+1)
        j = i+1
        while j < lt and tA[j][2] > tA[i][2]: j+=1
        ch['children'] = convertTocAtoB(tA[i+1:],j-i-1)
        i = j; tB.append(ch)
    return tB
   
converted_toc =  convertTocAtoB(toc,len(toc))

if args.gui:
    from toc_gui_gtk import toc_gui
    toc_gui(converted_toc)
elif args.pdfmark:
    from springerdl.pdfmark import tocToPdfmark, labelsToPdfmark
    print tocToPdfmark(toc)
    print labelsToPdfmark(getPagelabelsFromPdf(pdf))
else:
    def printToc(toc,lvl=0):
        for el in toc:
            print "-" * (lvl+1),
            print "%3d-%-3d" % (el['page_range'][0],el['page_range'][1]),
            print el['title']
            if len(el['children']) != 0:
                iterateRec(func,el['children'],lvl+1)
    printToc(toc)
   
