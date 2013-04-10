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
        from gettext import gettext as _
        
        parser = ArgumentParser(description = _('Fetch whole books from'
                                            + ' link.springer.com.'))
        parser.add_argument('springername', metavar='SPRINGER_IDENTIFIER',
                        type=str, help = _('A string identifying the book, '
                                       + 'e.g. its URL or Online-ISBN.'))
        parser.add_argument('-o','--output', metavar='FILE', type=str, 
                        help=_('Place to store, default: "ONLINE_ISBN.pdf".'))  
        parser.add_argument('--no-cover', action="store_true", default=False,
                        help=_("Don't add front cover as first page."))
        parser.add_argument('--autotitle', action="store_true", default=False,
                        help=_("Save as AUTHORS - TITLE.pdf. Overwritten by -o option."))
        parser.add_argument('--gui', action="store_true", default=False,
                        help=_("Start the interactive GUI not interpreting the "\
                                + "rest of the command line."))
        parser.add_argument('--pause', metavar='T', type=int, default=0,
                        help=_("Add a pause of between 0.6*T and 1.4*T seconds "\
                                + "before each download to simulate human behaviour."))
        parser.add_argument('--blanks', action="store_true", default=False,
                        help=_("Insert blank pages between chapters such that "\
                                + "each chapter begins at an odd page number."))
        parser.add_argument('--double-pages', action="store_true", default=False,
                        help=_("Use only together with --blanks. Inserts blank "\
                                + "pages, such that the resulting PDF can be "\
                                + "printed in duplex mode with four pages per "\
                                + "sheet."))
        parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help=_("Verbose output."))
        args = parser.parse_args()
        opts =  {
            "cover": not args.no_cover,
            "autotitle": args.autotitle,
            "pause": args.pause,
            "blanks": args.blanks,
            "dbpage": args.double_pages,
            "verbose": args.verbose,
        }
        fet = springerFetcher(args.springername, args.output, printer(), opts)
        fet.run()
    else:
        from springerdl.gui import gui_main
        gui_main(springerFetcher)
      
    return 0

if __name__ == "__main__":
    sys.exit(main())
      
   
