Springer Link Downloader
========================

Downloader for link.springer.com written in Python using pyPdf, BeautifulSoup,
urllib2, ImageMagick and Ghostscript. For more information see 
http://tovotu.de/dev/518-Neuer-SpringerLink-Downloader/

Requirements
============

Springer Link Downloader depends on the following Python packages:

* urllib2, httplib
* pyPdf
* gobject (Gtk3)
* BeautifulSoup

Furthermore it makes use of these command line tools:

* ImageMagick (as /usr/bin/convert)
* ghostscript (as /usr/bin/gs)

Installation
============

There are no setup scripts yet. But the intended directory structure looks
something like this.

    /usr/bin/springer_download.py
    /usr/lib/python2.7/site-packages/springerdl/
    /usr/lib/python2.7/site-packages/springerdl/{__init__,fetcher,gui,pdfmark,pdftoc,util}.py
    /usr/share/doc/springerdl/examples/
    /usr/share/doc/springerdl/examples/toc_{from_pdf,gui_gtk}.py

License
=======

This program is free software; you can redistribute it and/or
modify it under the terms of VERSION 2 of the GNU General Public
License as published by the Free Software Foundation provided
that the above copyright notice is included.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Go to http://www.gnu.org/licenses/gpl-2.0.html to get a copy
of the license.
