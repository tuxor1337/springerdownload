
class cli_toc(object):
   def __init__(self,toc):
      self.toc = toc
      
   def show(self):
      def print_ch(el,lvl):
         print "-" * (lvl+1),
         print "%3d-%-3d" % (el['page_range'][0],el['page_range'][1]),
         print el['title']
         
      def iterateRec(func,toc,lvl=0):
         for el in toc:
            func(el,lvl)
            if len(el['children']) != 0:
               iterateRec(func,el['children'],lvl+1)
      iterateRec(print_ch,self.toc)
