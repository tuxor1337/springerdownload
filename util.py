# -*- coding: utf-8 -*-

import httplib, re, urllib2

################################################################################
############################### Utilities, Tools  ##############################
################################################################################

############################## print_* to stdout  ##############################

from math import floor
from sys import stdout

class printer:
   def __init__(self, p=stdout):
      self.p = p
     
   def doing(self,s):
      self.p.write("==> %s..." % (s))
      self.p.flush()
      
   def done(self,s="done"):
      self.p.write(s+".\n")
      
   def out(self,s):
      self.p.write(s+"\n")
      
   def err(self,s):
      self.p.write("Error: "+s+"\n")
      
   def progress(self,text):
      return cli_progress(text,self.p)

class cli_progress:
   def __init__(self,text,p=stdout):
      self.txt = "==> "+text+"..."
      self.b = 0
      self.p = p
      
   def update(self,a,b,c="\r"):
      self.b = b
      a = a if a < b else b
      text = self.txt % (a,b)
      width = 70-len(text)
      marks = floor(width * (float(a)/float(b)))
      loader = '[' + ('=' * int(marks)) + (' ' * int(width - marks)) + ']'
      self.p.write("%s %s%s" % (text,loader,c))
      self.p.flush()
         
   def destroy(self):
      if self.b != 0:
         self.update(self.b,self.b," Done! \n")

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
    
def uniconvHex(string):
   out = ""
   if type(string) != unicode:
      try:
         string = string.decode("utf8")
      except UnicodeDecodeError:
         print string
         print type(string)
   for s in string:
      out += str(hex(ord(s)))[2:].upper().rjust(4,"0")
   return out
   
def decodeForSure(s):
   if type(s) == unicode:
      return s
   try:
      return unicode(s)
   except:
      for charset in ["utf8","latin1","ISO-8859-2","cp1252","utf_16be"]:
         try:
            return s.decode(charset)
         except (UnicodeDecodeError,UnicodeEncodeError),e:
            pass
      print type(s)
      print s
      return s.decode("ascii","replace")
      
def make_short(s,max=35):
   if len(s) > max:
      m = max/2
      return s[0:m-2]+"..."+s[-m+1:]
   return s

################################## Soup helpers ################################

from BeautifulSoup import BeautifulSoup
import copy

hexentityMassage = copy.copy(BeautifulSoup.MARKUP_MASSAGE)
hexentityMassage += [(re.compile('&#x([0-9a-fA-F]+);'), 
                     lambda m: '&#%d;' % int(m.group(1), 16))]
                     
def getSoup(url,params=None,charset='utf8'):
   try:
      html = urllib2.urlopen(url,params).read().decode(charset)
      soup = BeautifulSoup(html,convertEntities=BeautifulSoup.HTML_ENTITIES,
               markupMassage=hexentityMassage)
   except (urllib2.URLError,httplib.BadStatusLine):
      print "Connection to %s failed." % url
      return None
      #return getSoup(url,params,charset)
   return soup

def cleanSoup(soup):
   return u''.join(soup.findAll(text=True))
