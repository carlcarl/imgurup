imgurup
============

.. image:: https://img.shields.io/pypi/v/imgurup.svg
   :target: https://pypi.python.org/pypi/imgurup
   :alt: Latest PyPI version
.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :alt: MIT license
.. image:: https://coveralls.io/repos/carlcarl/imgurup/badge.svg?branch=master&service=github 
   :target: https://coveralls.io/github/carlcarl/imgurup?branch=master

Upload to imgur using its API(v3).
Support CLI, KDE, Zenity(GTK) and Mac dialog upload.


Feature
-------
| Support upload images(anonymously/account)
| Support CLI, KDE, Zenity(GTK) and Mac dialog upload
| Support Python 3

Installation
------------
.. code-block:: bash

    $ sudo python setup.py install

or 

.. code-block:: bash

    $ sudo pip install imgurup


Usage
-----
``img [-h] [-f [<image path> [<image path> ...]]] [-d [<album id>]] [-g] [-n] [-q]``

| You can just type ``img`` without any argument, the program will ask you for another infomation.
| But add ``-f`` argument with your image file would be easier to use, ex: ``img -f xx.jpg``
| After the authentication, the access_token and refresh_token will be saved in ``~/.imgurup.conf``

Optional arguments:
::

    -h, --help       show this help message and exit
    -f [<image path> [<image path> ...]] The images you want to upload
    -d [<album id>]  The album id you want your image to be uploaded to
    -g               GUI mode
    -n               Anonymous upload
    -s               Add command in the context menu of file manager(Support Gnome and KDE)
    -q               Choose album with each file
    -t               Use image name as the title

Packcage Dependency
-------------------
* None

Customize example
-----------------

.. code-block:: python

    from imgurup import Imgur


    class MyImgur(Imgur):

        def get_error_dialog_args(self, msg='Error'):
            args = [
                'zenity',
                '--error',
                '--text={text}'.format(text=msg),
            ]
            return args

        def get_auth_msg_dialog_args(self, auth_msg, auth_url):
            args = [
                'zenity',
                '--entry',
                '--text={msg}'.format(msg=auth_msg),
                '--entry-text={link}'.format(link=auth_url),
            ]
            return args

        def get_enter_pin_dialog_args(self, token_msg):
            args = [
                'zenity',
                '--entry',
                '--text={msg}'.format(msg=token_msg),
            ]
            return args

        def get_ask_image_path_dialog_args(self):
            args = [
                'zenity',
                '--file-selection',
            ]
            return args

        def get_ask_album_id_dialog_args(self, albums, no_album_msg):
            i = 1
            arg = [
                'zenity',
                '--list',
                '--text="Choose the album"',
                '--column=No.',
                '--column=Album name',
                '--column=Privacy',
            ]
            for album in albums:
                arg.append(str(i))
                arg.append('{album[title]}'.format(album=album))
                arg.append('{album[privacy]}'.format(album=album))
                i += 1
            arg.append(str(i))
            arg.append(no_album_msg)
            arg.append('public')

        def get_show_link_dialog_args(self, links):
            args = [
                'zenity',
                '--info',
                '--text={links}'.format(links=links),
            ]
            return args


License
-------

The ``imgurup`` package is written by Chien-Wei Huang. It’s MIT licensed and freely available.

Feel free to improve this package and send a pull request to GitHub.
