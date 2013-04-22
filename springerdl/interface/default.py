
class default_main(object):
    def __init__(self):
        self.options = {
            "springer_name": "",
            "cover": True,
            "autotitle": False,
            "pause": 0,
            "blanks": False,
            "dbpage": False,
            "verbose": False,
            "skip-meta": False,
            "sorted": False,
            "output-file": None,
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
