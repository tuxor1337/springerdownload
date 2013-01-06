
import os, sys
from distutils.core import setup
from distutils.dep_util import newer
from distutils.command.build_scripts \
      import build_scripts as distutils_build_scripts
from distutils.command.bdist_dumb import bdist_dumb

class build_scripts(distutils_build_scripts):
    def run(self):
        self.mkpath(self.build_dir)
        for script in self.scripts:
            newpath = os.path.join(self.build_dir, os.path.basename(script))
            if "single_file" in sys.argv \
               and os.path.basename(script) == "springer_download.py":
                newpath = os.path.join(self.build_dir, "__main__.py")
            elif newpath.lower().endswith(".py"):
                newpath = newpath[:-3]
            if newer(script, newpath) or self.force:
                self.copy_file(script, newpath)
                
class single_file(bdist_dumb):
    description = "create single executable"

    def reinitialize_command(self, name, **kw):
        cmd = bdist_dumb.reinitialize_command(self, name, **kw)
        if name == "install":
            cmd.install_lib = '/'
            cmd.install_scripts = '/'
        self.format="zip"
        print "==>",os.path.realpath(self.dist_dir)
        return cmd
    
    def run(self):
        bdist_dumb.run(self)
        for t,_,f in self.distribution.dist_files:
            if t == "bdist_dumb":
                zipfile = open(f,"r")
                exef = os.path.join(os.path.dirname(f), "springer_download")
                exefile = open(exef,"w")
                exefile.writelines("#!%s\n"%sys.executable)
                exefile.write(zipfile.read())
                zipfile.close(); exefile.close()
                os.chmod(exef,0777)

setup(name='Springer Link Downloader',
      version='1.0',
      cmdclass={"build_scripts": build_scripts, "single_file": single_file},
      description='Download whole books from link.springer.com',
      author='Thomas Vogt',
      author_email='tuxor1337@web.de',
      url='https://github.com/tuxor1337/springerdownload',
      packages=["springerdl"],
      scripts=["springer_download.py"],
      data_files=[("share/applications",["setup_data/springer_download.desktop"]),
                  ("share/doc/springerdl/examples",["examples/toc_from_pdf.py",
                                           "examples/toc_gui_gtk.py"]),
                  ("share/pixmaps",["setup_data/springer_download.png"])]
     )
