#!/usr/bin/env python

################################################################################
################################## Main program ################################
################################################################################

if __name__ == "__main__":
   from sys import argv
   from os import isatty
   from springerdl.fetcher import springerFetcher
   
   if "--gui" in  argv[1:] or not isatty(0):
      from springerdl.gui import gui_main
      gui_main(springerFetcher)
   else:
      from argparse import ArgumentParser
      parser = ArgumentParser(description = 'Fetch whole books '
                                          + 'from link.springer.com.')
      parser.add_argument('springername', metavar='SPRINGER_IDENTIFIER',
                        type=str, help = 'A string identifying the book, '
                                       + 'e.g. its URL or Online-ISBN.')
      parser.add_argument('-o','--output', metavar='FILE', type=str, 
                        help='Place to store, default: "ONLINE_ISBN.pdf".')
      parser.add_argument('--no-cover', action="store_true", default=False,
                        help="Don't add front cover as first page.")
      parser.add_argument('--gui', action="store_true", default=False,
                        help= "Start the interactive GUI not interpreting "
                            + "the rest of the command line.")
      args = parser.parse_args()
      fet = springerFetcher(args.springername,args.output,\
                  printer(),not args.no_cover)
      fet.run()
      
   
