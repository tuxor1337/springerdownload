#!/usr/bin/env python

import sys

################################################################################
################################## Main program ################################
################################################################################

def main(argv=sys.argv):
    from os import isatty
    from springerdl.fetcher import springerFetcher
   
    if (isatty(0) or len(argv) > 1) and "--gui" not in  argv[1:]:
        from argparse import ArgumentParser
        from springerdl.util import printer
        parser = ArgumentParser(description = 'Fetch whole books '
                                          + 'from link.springer.com.')
        parser.add_argument('springername', metavar='SPRINGER_IDENTIFIER',
                        type=str, help = 'A string identifying the book, '
                                       + 'e.g. its URL or Online-ISBN.')
        parser.add_argument('-o','--output', metavar='FILE', type=str, 
                        help='Place to store, default: "ONLINE_ISBN.pdf".')
        parser.add_argument('--no-cover', action="store_true", default=False,
                        help="Don't add front cover as first page.")
        parser.add_argument('--autotitle', action="store_true", default=False,
                        help="Save as %authors% - %title%.pdf. Overwritten by -o option.")
        parser.add_argument('--gui', action="store_true", default=False,
                        help= "Start the interactive GUI not interpreting "
                            + "the rest of the command line.")
        args = parser.parse_args()
        fet = springerFetcher(args.springername,args.output,\
                  printer(),not args.no_cover,args.autotitle)
        fet.run()
    else:
        from springerdl.gui import gui_main
        gui_main(springerFetcher)
      
    return 0

if __name__ == "__main__":
    sys.exit(main())
      
   
