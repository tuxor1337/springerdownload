Springer Link Downloader
========================

Downloader for link.springer.com written in Python using pyPdf and BeautifulSoup.
For more information see http://tovotu.de/dev/518-Neuer-SpringerLink-Downloader/

Requirements
------------

Springer Link Downloader depends on the following Python packages:

* urllib2, httplib, lxml (should be included by default with most distributions)
* pyPdf

It's totally possible running Springer Link Downloader in the command
line. But if you prefer a graphical user interface, run it with `--gui`
option. You will need `Gtk3` from the Python API of `gobject` to run the GUI.

Furthermore it makes use of these command line tools:

* ImageMagick (optional: the download of the frontcover is skipped if not available)
* ghostscript (optional: the metadata is skipped if not available)
* pdftk (optional: for `--pdftk` option)

Quick start: create a single working executable
-----------------------------------------------

You can create a working executable in `dist/springer_download` by simply
running the following command:

    % python setup.py single_file

Installation
------------

Simply install running:

    # python setup.py install

If you want to install as a user to your `$HOME` directory use the `--user`
option. Please note that you will have to remove the data manually if you want
to uninstall. Here are the files and folders created by the setup script:

    %{platform-prefix}/bin/springer_download
    %{platform-prefix}/share/applications/springer_download.desktop
    %{platform-prefix}/share/pixmaps/springer_download.png
    %{platform-prefix}/share/doc/springerdl/examples/
    %{python-site-packages}/springerdl/
    %{python-site-packages}/Springer_Link_Downloader-1.0-py2.7.egg-info

`%{python-site-packages}` and `%{platform-prefix}` depend on the operating system.
In Fedora these values default to `/usr/lib/python2.7/site-packages` and `/usr`
respectively.

Package maintainers might want to add the `--root` option to specify an
appropriate `%{buildroot}`. For more information see

    $ python setup.py install --help

Usage
-----

For detailed usage information please refer to

    $ springer_download.py --help
