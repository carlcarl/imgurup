# Upload to imgur using its API v3
usage: img.py [-h] {auth,update,list,upload} ...

## Usage
img.py [-h] {auth,update,list,upload}

optional arguments:
  -h, --help            show this help message and exit

Commands available: <br />
  {auth,update,list,upload}

* auth                (Authorization tokens)
* update              (Update tokens)
* list                (List all albums)
* upload              (Upload image)

## Commands Available:
* auth

	./img.py auth

* update

	./img.py update

* list

	./img.py list` 

	or 

	`./img.py list -u username

* upload

	./img.py upload -f ./test.jpg

	or add the album id 
	
	./img.py upload -f ./test.jpg -d AB123
	
## Packcage Dependency
* pycurl (Will use `requests` instead)

