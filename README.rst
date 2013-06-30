imgurup
============
Upload to imgur using API(v3). Support CLI, KDE, Zenity(GTK) and Mac dialog upload. And you can also use your account to upload :).


Feature
-------
Support upload images(anonymously) or with your account.
Support CLI, KDE, Zenity(GTK) and Mac dialog upload

Installation
------------
::

	python setup.py install

or 

::

    sudo pip install imgurup


Usage
-----
``img [-h] [-f <image path>] [-d [<album id>]] [-g] [-n]``

You can just type ``img`` without any argument, the program will ask you for another infomation.

But add ``-f`` argument with your image file would be easier to use, ex: ``img -f xx.jpg``

After the authentication, the access_token and refresh_token will be saved in ``~/.imgurup.conf``

Optional arguments:
::

	-h, --help       show this help message and exit
	-f <image path>  The image you want to upload
	-d [<album id>]  The album id you want your image to be uploaded to
	-g               GUI mode
	-n               Anonymous upload
	-s               Add command in the context menu of file manager(Support Gnome and KDE)

Packcage Dependency
-------------------
* None

Todo
----
* None

Development
-----------

