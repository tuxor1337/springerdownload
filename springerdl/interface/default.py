
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

class default_main(object):
    def __init__(self):
        self.options = {
            "autotitle": False,
            "pause": 0,
            "blanks": False,
            "dbpage": False,
            "verbose": False,
            "skip-meta": False,
            "sorted": False,
            "output-file": None,
            "cover": True,
            "springer_name": "",
            "proxy" : None,
            "user-agent" : USER_AGENT,
            "force-full-access": False,
            "download-only": False,
            "use-pdfs": None,
            "ignore-full": False,
        }

    def option(self, key):
        return self.options[key]

    def doing(self,s): self.busy = True
    def done(self,s="done"): self.relax()
    def out(self,s): self.relax()
    def err(self,s): self.relax()
    def progress(self,text):
        self.busy = True; self.set_text(text)
        self.pgs_b = 0; return self
    def relax(self): self.busy = False

    def set_text(self,txt): self.pgs_txt = txt
    def update(self,a,b):
        self.pgs_b = b; a = b if a > b else a
        if b == 0: a = b = 1
        text = self.pgs_txt % (a,b)
    def destroy(self):
        if self.pgs_b != 0: self.update(self.pgs_b,self.pgs_b)
        self.relax()
