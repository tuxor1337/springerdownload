
from setuptools import setup, find_packages

data_files = [
    ("share/applications", ["setup_data/springer_download.desktop"]),
    ("share/doc/springerdl/examples", [
        "examples/toc_from_pdf.py",
        "examples/toc_gui_gtk.py",
    ]),
    ("share/pixmaps", ["setup_data/springer_download.png"])]

setup(
    name='springerdownload',
    version="1.3",
    description='Download whole books from link.springer.com',
    keywords='download books documents science',
    url='https://framagit.org/tuxor1337/springerdownload',
    project_urls={ 'Source': 'https://framagit.org/tuxor1337/springerdownload', },
    author='Thomas Vogt',
    author_email='thomas.vogt@tovotu.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Topic :: Internet',
    ],
    packages=find_packages(),
    scripts=["bin/springer_download"],
    data_files=data_files,
    install_requires=[
        "PyGObject",
        "PyPDF2",
        "lxml",
        "cssselect",
    ],
)
