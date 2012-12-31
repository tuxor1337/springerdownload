
from gi.repository import Gtk,Gdk

class toc_tree(Gtk.TreeView):
   def __init__(self,toc):
      self.toc_store = Gtk.TreeStore(str,str)
      Gtk.TreeView.__init__(self,self.toc_store)
      self.toc = toc
      
      self.cols = []
      for i,name in enumerate(["Title","Page"]):
             cell  = Gtk.CellRendererText()
             col = Gtk.TreeViewColumn(name)
             col.pack_start(cell,True)
             col.add_attribute(cell,"text",i)
             col.set_resizable(True)
             self.append_column(col)
             self.cols.append(col)
      self.cols[0].set_expand(True)
      self.cols[1].set_min_width(200)
      self.cols[1].set_max_width(300)
      self.hide()
      
      def add_toc(t,p=None):
         for el in t:
            pr = ""
            if el['page_range'][0] > 0:
               pr = "-".join([str(x) for x in el['page_range']])
            elif el['page_range'][0] < 0:
               pr = "-".join([int_to_roman(x+1000) for x in el['page_range']])
            this = self.toc_store.append(p, [el['title'] ,pr])
            if len(el['children']) != 0:
               add_toc(el['children'],this)
      add_toc(self.toc)

class toc_gui(Gtk.Window):
   def __init__(self,toc):
      Gtk.Window.__init__(self)
      self.toc      = toc
      self.tocliste = toc_tree(self.toc)

      screen = Gdk.Screen.get_default()
      self.geometry   = (screen.width()/640.0,screen.height()/480.0,\
             int(screen.width()*0.5),int(screen.height()*0.5))
      width  = int(500.0*max(1,self.geometry[0]))
      height = int(400.0*max(1,self.geometry[1]))
      self.set_size_request(width,height)
      self.set_position(Gtk.WindowPosition.CENTER)
      self.set_title("Table of Contents")
      
      self.scrollwin = Gtk.ScrolledWindow()
      self.scrollwin.add(self.tocliste)
      self.scrollwin.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
      self.add(self.scrollwin)
      
      self.connect("destroy", Gtk.main_quit)
      self.show_all()
      Gtk.main()
