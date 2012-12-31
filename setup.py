
import os
from distutils.core import setup
from distutils.dep_util import newer
from distutils.command.build_scripts \
      import build_scripts as distutils_build_scripts

class build_scripts(distutils_build_scripts):
    description = "copy scripts to build directory"

    def run(self):
        self.mkpath(self.build_dir)
        for script in self.scripts:
            newpath = os.path.join(self.build_dir, os.path.basename(script))
            if newpath.lower().endswith(".py"):
                newpath = newpath[:-3]
            if newer(script, newpath) or self.force:
                self.copy_file(script, newpath)

setup(name='Springer Link Downloader',
      version='1.0',
      cmdclass={"build_scripts": build_scripts},
      description='Download whole books from link.springer.com',
      author='Thomas Vogt',
      author_email='tuxor1337@web.de',
      url='https://github.com/tuxor1337/springerdownload',
      packages=['springerdl'],
      scripts=["springer_download.py"],
      data_files=[("share/applications",["setup_data/springer_download.desktop"]),
                  ("share/doc/springerdl/examples",["examples/toc_from_pdf.py",
                                           "examples/toc_gui_gtk.py"]),
                  ("share/pixmaps",["setup_data/springer_download.png"])]
     )

