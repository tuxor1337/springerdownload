# -*- coding: utf-8 -*-

import httplib, re, urllib2, copy
from BeautifulSoup import BeautifulSoup

################################## TOC Helpers #################################

def printToc(t,lvl=0):
    for el in t:
        print "-" * (lvl+1),
        print "%3d-%-3d" % (el['page_range'][0],el['page_range'][1]),
        print el['title'],
        if el['noaccess']:
            print " (no access)",
        print
        if len(el['children']) != 0:
            printToc(el['children'],lvl+1)
      
def tocIterateRec(toc, func, data=None, lvl=0):
    for el in toc:
        func(el,lvl,data)
        if len(el['children']) != 0:
            tocIterateRec(el['children'],func,data,lvl+1)
            
def getAccessibleToc(toc):
    new_t = []
    for ch in toc:
        if not ch['noaccess']:
            new_ch = copy.deepcopy(ch)
            new_ch['children'] = getAccessibleToc(new_ch['children'])
            if ch['pdf_url'] != "" or len(new_ch['children']) != 0:
                new_t.append(new_ch)
    return new_t
    
################################## Little Helpers ##############################
        
def parseSpringerURL(url):
    url = url.replace("http://","")
    url = url.replace("link.springer.com/","")
    if "/" not in url:
        return url
    m = re.search(r'(book|referencework)/([^/]*)/([^/]*)', url)
    try:
        return m.group(3)
    except:
        return None

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
        print "Connection to %s failed." % url
        return None
    return soup

def cleanSoup(soup):
    return u''.join(soup.findAll(text=True))
   
