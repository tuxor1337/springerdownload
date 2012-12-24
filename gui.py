
from util import printer, make_short

################################################################################
########################## Graphical User Interface  ###########################
################################################################################

from gi.repository import Gtk,Gdk

class gui_main(Gtk.Window):
   def __init__(self,fet):
      Gtk.Window.__init__(self)
      fet.p = self
      self.outf = None
      self.sprFet = fet

      screen = Gdk.Screen.get_default()
      self.geometry   = (screen.width()/640.0,screen.height()/480.0,\
             int(screen.width()*0.5),int(screen.height()*0.5))
      width  = int(300.0*max(1,self.geometry[0]))
      height = 120
      self.set_size_request(width,height)
      self.set_position(Gtk.WindowPosition.CENTER)
      self.set_title("Springer Downloader")
      
      vbox = Gtk.VBox()
      hbox = Gtk.HBox()
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
      if event.type == Gdk.EventType.KEY_PRESS and event.keyval == Gdk.keyval_from_name("Return"):
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
         self.butt_outf.set_label("Output file: "+make_short(self.outf))
      
   def doing(self,s):
      self.pgs.set_text(s+"...")
      while Gtk.events_pending():
         Gtk.main_iteration()
   
   def done(self,s="done"):
      self.pgs.set_text(self.pgs.get_text()+s+".")
      while Gtk.events_pending():
         Gtk.main_iteration()
   
   def out(self,s):
      self.pgs.set_text(s)
      while Gtk.events_pending():
         Gtk.main_iteration()
      
   def err(self,s):
      self.pgs.set_text("Error: "+s)
      while Gtk.events_pending():
         Gtk.main_iteration()
      
   def progress(self,s):
      self.pgs_text=s
      self.pgs_b = 0
      while Gtk.events_pending():
         Gtk.main_iteration()
      return self
      
   def update(self,a,b,c="..."):
      self.pgs_b = b
      self.pgs.set_text((self.pgs_text % (a,b))+c)
      self.pgs.set_fraction(float(a)/float(b))
      while Gtk.events_pending():
         Gtk.main_iteration()
      
   def destroy(self):
      if self.pgs_b != 0:
         self.update(self.pgs_b,self.pgs_b," Done!")
      while Gtk.events_pending():
         Gtk.main_iteration()
