# -*- coding: utf-8 -*-

import httplib, re, urllib2, copy
from BeautifulSoup import BeautifulSoup
from math import floor
from sys import stdout
from gettext import gettext as _

################################################################################
############################### Utilities, Tools  ##############################
################################################################################

########################## Standard Output Class  ##############################

class printer:
    def __init__(self, p=stdout):
        self.p = p; self.busy = False
    def doing(self,s):
        self.p.write("==> %s..." % (s));
        self.p.flush(); self.busy = True
    def done(self,s="done"): self.p.write(s+"."); self.relax(); self.p.flush()
    def out(self,s):
        self.relax(); self.p.write(s+"\n"); self.p.flush()
    def err(self,s):
        self.relax(); self.p.write("Error: "+s+"\n"); self.p.flush()
    def progress(self,text): return cli_progress(text,self.p)
    def relax(self):
        if self.busy: self.p.write("\n")
        self.busy = False

class cli_progress:
    def __init__(self,text,p=stdout):
        self.txt, self.b, self.p = "==> "+text+"...", 0, p
    
    def update(self,a,b,c="\r"):
        self.b = b; a = b if a > b else a
        if b == 0: a = b = 1
        text = self.txt % (a,b); width = 70-len(text)
        marks = floor(width * (float(a)/float(b)))
        loader = '[' + ('=' * int(marks)) + (' ' * int(width - marks)) + ']'
        self.p.write("%s %s%s" % (text,loader,c)), self.p.flush()
         
    def destroy(self):
        if self.b != 0: self.update(self.b,self.b," Done! \n")

################################## Little Helpers ##############################

numeral_map = zip(
    (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
    ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
)

def int_to_roman(i):
    result = []
    for integer, numeral in numeral_map:
        count = int(i / integer)
        result.append(numeral * count)
        i -= integer * count
    return ''.join(result)

def roman_to_int(n):
    n = unicode(n).upper()
    i = result = 0
    for integer, numeral in numeral_map:
        while n[i:i + len(numeral)] == numeral:
            result += integer
            i += len(numeral)
    return result

def repairChars(s):
    if type(s) != unicode:
        try:
            s = s.decode("utf8")
        except UnicodeDecodeError:
            print s
            print type(s)
    for a,b in zip( (u'¨a',u'¨o',u'¨u',u'¨A',u'¨O',u'¨U'), \
                    (u'ä',u'ö',u'ü',u'Ä',u'Ö',u'Ü')):
        s = s.replace(a,b)
    return s
   
def decodeForSure(s):
    if type(s) == unicode: return s
    try: return unicode(s)
    except:
        for charset in ["utf8","latin1","ISO-8859-2","cp1252","utf_16be"]:
            try: return s.decode(charset)
            except: pass
        print _("Can't decode") + " s='%s',  type(s)=%s" % (s,type(s))
        return s.decode("ascii","replace")

################################## Soup helpers ################################

def getSoup(url,params=None,charset='utf8'):
    hexentityMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
    hexentityMassage += [(re.compile('&#x([0-9a-fA-F]+);'), 
                            lambda m: '&#%d;' % int(m.group(1), 16))]
    try:
        html = urllib2.urlopen(url,params).read().decode(charset)
        soup = BeautifulSoup(html,convertEntities=BeautifulSoup.HTML_ENTITIES,
                markupMassage=hexentityMassage)
    except (urllib2.URLError,httplib.BadStatusLine):
        print _("Connection to %s failed.") % url
        return None
    return soup

def cleanSoup(soup):
    return u''.join(soup.findAll(text=True))
   
