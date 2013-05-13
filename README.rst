imgurup
============
Upload to imgur using API(v3). Support authorization, CLI, KDE and Mac dialog upload


Feature
-------
Support upload images(anonymously) or with your account.
Support CLI and KDE dialog upload

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

Optional arguments:
::

	-h, --help       show this help message and exit
	-f <image path>  The image you want to upload
	-d [<album id>]  The album id you want your image to be uploaded to
	-g               GUI mode
	-n               Anonymous upload

Packcage Dependency
-------------------
* None

Todo
----
* Nothing for now

