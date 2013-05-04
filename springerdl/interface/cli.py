
from math import floor
from argparse import ArgumentParser
from sys import stdout
from gettext import gettext as _

class cli_main(object):
    def __init__(self, fetcher):
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
        parser.add_argument('--skip-meta', action="store_true", default=False,
                        help=_("Skip ghostscripting meta information."))
        parser.add_argument('--sorted', action="store_true", default=False,
                        help=_("Try sorting the chapters instead of "\
                            + "concatenating in the order found on the website."))
        parser.add_argument('--double-pages', action="store_true", default=False,
                        help=_("Use only together with --blanks. Inserts blank "\
                                + "pages, such that the resulting PDF can be "\
                                + "printed in duplex mode with four pages per "\
                                + "sheet."))
        parser.add_argument('-v', '--verbose', action="store_true", default=False,
                        help=_("Verbose stdout."))
        parser.add_argument("--proxy-url", nargs='?', const=None, default=None, 
                            type=str, help=_("Set proxy address [default: %(default)s]"))
        parser.add_argument("--proxy-username", nargs='?', const=None, default=None, 
                            type=str, help=_("Set username to authenticate with at proxy [default: %(default)s]"))
        parser.add_argument("--proxy-password", nargs='?', const=None, default=None, 
                            type=str, help=_("Set password to authenticate with at proxy [default: %(default)s]"))
        parser.add_argument("--proxy-port", nargs='?', const=80, default=80, 
                            type=int, help=_("Set proxy port [default: %(default)s]"))
        parser.add_argument("--user-agent", nargs='?', const=None, default=None, 
                            type=str, help=_("Set custom user agent [default: %(default)s]"))
        
        args = parser.parse_args()
        
        proxy = {
            "url" : args.proxy_url,
            "username" : args.proxy_username,
            "password" : args.proxy_password,
            "port" : args.proxy_port
        }
        
        self.options =  {
            "springer_name": args.springername,
            "cover": not args.no_cover,
            "autotitle": args.autotitle,
            "pause": args.pause,
            "blanks": args.blanks,
            "dbpage": args.double_pages,
            "verbose": args.verbose,
            "skip-meta": args.skip_meta,
            "sorted": args.sorted,
            "output-file": args.output, 
            "proxy" : proxy,
            "user-agent" : args.user_agent,
        }
        self.busy = False
        fetcher(self)
        
    def option(self, key):
        return self.options[key]
        
    def doing(self,s):
        self.relax(); stdout.write("==> %s..." % (s));
        stdout.flush(); self.busy = True
    def done(self,s="done"): stdout.write(s+"."); self.relax(); stdout.flush()
    def out(self,s):
        self.relax(); stdout.write(s+"\n"); stdout.flush()
    def err(self,s):
        self.relax(); stdout.write("Error: "+s+"\n"); stdout.flush()
    def progress(self,text):
        self.busy = True; self.set_text(text)
        self.pgs_b = 0
        return self
    def relax(self):
        if self.busy: stdout.write("\n")
        self.busy = False
    
    def set_text(self,txt): self.pgs_txt = "==> "+txt+"..."
    def update(self,a,b,c="\r"):
        self.pgs_b = b; a = b if a > b else a
        if b == 0: a = b = 1
        text = self.pgs_txt % (a,b); width = 70-len(text)
        marks = floor(width * (float(a)/float(b)))
        loader = '[' + ('=' * int(marks)) + (' ' * int(width - marks)) + ']'
        stdout.write("%s %s%s" % (text,loader,c)), stdout.flush()
    def destroy(self):
        if self.pgs_b != 0:
            self.update(self.pgs_b,self.pgs_b," Done!")
        self.relax()
        
