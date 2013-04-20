# Upload to imgur using API(v3)


## Feature
Support CLI and KDE dialog upload

## Installation

	python setup.py install

## Usage
img [-h] [-f &lt;image path&gt;] [-d [&lt;album id&gt;]] [-g] [-n]

You can just type `img` without any argument, the program will ask you for another infomation.
But add `-f` argument with your image file would be easier to use, ex: `img -f xx.jpg`

Optional arguments:
*  -h, --help       show this help message and exit
*  -f &lt;image path&gt;  The image you want to upload
*  -d [&lt;album id&gt;]  The album id you want your image to be uploaded to
*  -g               GUI mode
*  -n               Anonymous upload

## Packcage Dependency
* None

## Todo
Support MacOS

