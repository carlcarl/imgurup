#! /usr/bin/env python


import pycurl
import StringIO

client_id = '55080e3fd8d0644'
client_secret = 'd021464e1b3244d6f73749b94d17916cf361da24'


def read_token():
    # TODO: Read from some file format
    return '02fa9a3987ea35ac6eafb5f9cc19cbba8fd13bf7'


def get_albums(account='me'):
    url = 'https://api.imgur.com/3/account/%s/albums' % account
    c = pycurl.Curl()
    # c.setopt(pycurl.VERBOSE, 1)
    access_token = read_token()
    if access_token == '':
        print('Warn: Without access token')
        c.setopt(c.HTTPHEADER, ['Authorization: Client-ID %s' % client_id])
    else:
        print('With access token')
        c.setopt(c.HTTPHEADER, ['Authorization: Bearer %s' % access_token])
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    print(c.fp.getvalue())
    # TODO: Parse to JSON
    c.close()


def upload_images(image_path='/home/carlcarl/Downloads/rEHCq.jpg', album_id='9DpVh'):
    url = 'https://api.imgur.com/3/image'
    c = pycurl.Curl()
    c.setopt(pycurl.VERBOSE, 1)
    c.setopt(c.POST, 1)
    c.setopt(c.HTTPPOST, [('album_id', album_id), ('image', (c.FORM_FILE, image_path))])
    access_token = read_token()
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer %s' % access_token])
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    print(c.fp.getvalue())
    # TODO: Parse to JSON
    c.close()


def auth():
    # url = 'https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=token&state=carlcarl' % client_id
    auth_url = 'https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=pin&state=carlcarl' % client_id
    print ('Visit this URL in your browser: ' + auth_url)
    pin = raw_input('Enter PIN from browser: ')

    url = 'https://api.imgur.com/oauth2/token'
    c = pycurl.Curl()
    c.setopt(pycurl.VERBOSE, 1)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    c.setopt(c.POST, 1)
    c.setopt(c.POSTFIELDS, 'client_id=%s&client_secret=%s&grant_type=pin&pin=%s'
             % (client_id, client_secret, pin))
    # c.setopt(c.HTTPHEADER, ['Authorization: Client-ID %s' % client_id])
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    print(c.fp.getvalue())
    # TODO: Parse to JSON
    c.close()


if __name__ == '__main__':
    get_albums()
    # auth()
