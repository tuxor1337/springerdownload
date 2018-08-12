# -*- coding: utf-8 -*-
#
# This file is part of Springer Link Downloader
#
# Copyright 2018 Thomas Vogt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

try:
    from urllib2 import URLError
    import urllib2, httplib
except ImportError:
    from urllib.error import URLError
    import urllib.request as urllib2
    import http.client as httplib

import re, copy, lxml.html
from gettext import gettext as _

from .const import USER_AGENT, SPRINGER_URL, SPR_IMG_URL

################################## TOC Helpers #################################

def printToc(t,lvl=0):
    output = ""
    for el in t:
        output += "-" * (lvl+1)
        output += " %3d-%-3d %s" % (
            el['page_range'][0],
            el['page_range'][1],
            el['title']
        )
        if el['noaccess']:
            output +=  " (no access)\n"
        if len(el['children']) != 0:
            output += printToc(el['children'],lvl+1)
        output += "\n"
    return output.strip("\n")


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
            print(_("Can't decode") + " s='%s',  type(s)=%s" % (s,type(s)))
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
        print(_("Can't decode") + " s='%s',  type(s)=%s" % (s,type(s)))
        return s.decode("ascii","replace")

################################## Soup helpers ################################

def setupOpener(proxy,useragent):
    if proxy:
        url = proxy["url"]
        port = proxy["port"]
        if url:

            proxy_handler = None
            if not port:
                proxy_handler = urllib2.ProxyHandler({'http': url})
            else:
                proxy_handler = urllib2.ProxyHandler({'http': "%s:%d" % (url, port)})

            username = proxy["username"]
            password = proxy["password"]
            if username and password:
                password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

                password_mgr.add_password(None, SPRINGER_URL, username, password)
                password_mgr.add_password(None, SPR_IMG_URL, username, password)

                auth_handlers = [urllib2.ProxyBasicAuthHandler(password_mgr), urllib2.ProxyDigestAuthHandler(password_mgr)]

                opener = urllib2.build_opener(proxy_handler, *auth_handlers)
            else:
                opener = urllib2.build_opener(proxy_handler)

            urllib2.install_opener(opener)

    if useragent:
        global USER_AGENT
        USER_AGENT = useragent

def connect(url,params=None):
    request = urllib2.Request(url, params);
    request.add_header('User-Agent', USER_AGENT);

    return urllib2.urlopen(request)

def getElementTree(url,params=None):
    try:
        response = connect(url, params)
        if not response:
            return None

        html = response.read()

    except URLError as e:
        print(_("Connection to %s failed (%s).") % (url, e.reason))
        return None;

    except httplib.BadStatusLine as e:
        print(_("Connection to %s failed.") % (url))
        return None;

    return lxml.html.fromstring(html)

