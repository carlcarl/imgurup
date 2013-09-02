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
``img [-h] [-f [<image path> [<image path> ...]]] [-d [<album id>]] [-g] [-n] [-q]``

You can just type ``img`` without any argument, the program will ask you for another infomation.

But add ``-f`` argument with your image file would be easier to use, ex: ``img -f xx.jpg``

After the authentication, the access_token and refresh_token will be saved in ``~/.imgurup.conf``

Optional arguments:
::

	-h, --help       show this help message and exit
	-f [<image path> [<image path> ...]] The images you want to upload
	-d [<album id>]  The album id you want your image to be uploaded to
	-g               GUI mode
	-n               Anonymous upload
	-s               Add command in the context menu of file manager(Support Gnome and KDE)
	-q               Choose album with each file

Packcage Dependency
-------------------
* None

Todo
----
* None

Development
-----------


License
-------
(The MIT License)

Copyright (C) 2013 黃健瑋(Chien-Wei Huang)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

