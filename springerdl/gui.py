
from gi.repository import Gtk,Gdk

################################################################################
########################## Graphical User Interface  ###########################
################################################################################

def _makeshort(s,max=35):
   if len(s) > max:
      m = max/2
      return s[0:m-2]+"..."+s[-m+1:]
   return s

class gui_main(Gtk.Window):
   def __init__(self,fet):
      Gtk.Window.__init__(self)
      self.sprFet = fet
      self.outf = None

      screen = Gdk.Screen.get_default()
      self.set_size_request(int(300.0*max(1,screen.width()/640.0)),120)
      self.set_position(Gtk.WindowPosition.CENTER)
      self.set_title("Springer Downloader")
      
      vbox, hbox = Gtk.VBox(), Gtk.HBox()
      self.spr_id = Gtk.Entry()
      self.spr_id.connect("key_press_event",self.button_key_cb)
      self.butt_fetch = Gtk.Button("Fetch!")
      self.butt_fetch.connect("key_press_event",self.button_key_cb)
      self.butt_fetch.connect("released",self.button_cb)
      self.pgs = Gtk.ProgressBar()
      self.pgs.set_show_text(True)
      self.pgs.set_text('Type in the URL and press "Fetch!" to start.')
      hbox.pack_start(self.spr_id,True,True,2)
      hbox.pack_start(self.butt_fetch,False,True,2)
      vbox.pack_start(self.pgs,True,True,2)
      vbox.pack_start(hbox,False,True,2)
      hbox = Gtk.HBox()
      self.cover = Gtk.CheckButton()
      self.cover.set_active(True)
      hbox.pack_start(self.cover,False,True,0)
      hbox.pack_start(Gtk.Label("Include book cover"),False,True,3)
      self.butt_outf = Gtk.Button("Choose output file...")
      self.butt_outf.connect("released",self.button_outf_cb)
      hbox.pack_end(self.butt_outf,False,True,2)
      vbox.pack_start(hbox,False,True,2)
      self.add(vbox)
      
      self.connect("destroy", Gtk.main_quit)
      self.show_all()
      
      Gtk.main()
      
   def button_key_cb(self,widget,event,data=None):
      if event.type == Gdk.EventType.KEY_PRESS \
            and event.keyval == Gdk.keyval_from_name("Return"):
         self.button_cb(widget,data)
         return True
      
   def button_cb(self,button,data=None):
      fet = self.sprFet(self.spr_id.get_text(),self.outf,\
                                 self,self.cover.get_active())
      self.pgs.set_fraction(0)
      [x.set_sensitive(False) for x in [self.spr_id,self.butt_outf,\
                              self.butt_fetch, self.cover]]
      fet.run()
      [x.set_sensitive(True) for x in [self.spr_id,self.butt_outf,\
                              self.butt_fetch, self.cover]]
      return True
      
   def button_outf_cb(self,button,data=None):
      chosen = Gtk.FileChooserDialog("Choose output file...",self,
         Gtk.FileChooserAction.SAVE,
         (Gtk.STOCK_SAVE,Gtk.ResponseType.OK,
         Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL))
      chosen.set_do_overwrite_confirmation(True)
      success = chosen.run()
      filename = chosen.get_filename()
      chosen.destroy()
      if success == Gtk.ResponseType.OK:
         self.outf = filename
         self.butt_outf.set_label("Output file: "+_makeshort(self.outf))
         
   def write(self,s): self.pgs.set_text(s)
   def flush(self):
      while Gtk.events_pending(): Gtk.main_iteration()
   def writef(self,s): self.write(s); self.flush()
   def doing(self,s):
      self.write(s+"..."); self.pgs.set_fraction(0.1); self.flush()
   def done(self,s="done"):
      self.write(self.pgs.get_text()+s+".")
      self.pgs.set_fraction(1); self.flush()
   def out(self,s): self.writef(s)
   def err(self,s): self.writef("Error: "+s)
   def progress(self,s):
      self.pgs_text, self.pgs_b = s, 0; self.flush(); return self
   def destroy(self): self.update(self.pgs_b,self.pgs_b," Done!")
   def update(self,a,b,c="..."):
      if a > b: a = b
      if b == 0: a = b = 1
      self.pgs_b = b
      self.write((self.pgs_text % (a,b))+c)
      self.pgs.set_fraction(float(a)/float(b))
      self.flush()
      
