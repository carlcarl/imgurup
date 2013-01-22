#! /usr/bin/env python


import pycurl
import StringIO
import sys
from ConfigParser import SafeConfigParser

client_id = '55080e3fd8d0644'
client_secret = 'd021464e1b3244d6f73749b94d17916cf361da24'


def read_tokens():
    parser = SafeConfigParser()
    parser.read('imgur.conf')
    return {'access_token': parser.get('token', 'access_token'),
            'refresh_token': parser.get('token', 'refresh_token')}


def get_albums(account='me'):
    url = 'https://api.imgur.com/3/account/%s/albums' % account
    c = pycurl.Curl()
    # c.setopt(pycurl.VERBOSE, 1)
    tokens = read_tokens()
    access_token = tokens['access_token']
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


def upload_images(image_path='/home/carlcarl/Downloads/rEHCq.jpg',
                  anonymous=False, album_id='9DpVh'):
    url = 'https://api.imgur.com/3/image'
    c = pycurl.Curl()
    if anonymous:
        print('Upload images...')
        c.setopt(c.HTTPPOST, [('image', (c.FORM_FILE, image_path))])
    else:
        tokens = read_tokens()
        access_token = tokens['access_token']
        if access_token == '':
            print('Error: Access token should not be empty')
            sys.exit(1)
        else:
            print('Upload images to the album...')
            c.setopt(c.HTTPHEADER, ['Authorization: Bearer %s' % access_token])
            c.setopt(c.HTTPPOST, [('album_id', album_id), ('image', (c.FORM_FILE, image_path))])

    c.setopt(pycurl.VERBOSE, 1)
    c.setopt(c.POST, 1)
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    print(c.fp.getvalue())
    # TODO: Parse to JSON
    c.close()


def update_token(refresh_token, giant_type='refresh_token'):
    url = 'https://api.imgur.com/oauth2/token'
    c = pycurl.Curl()
    # c.setopt(pycurl.VERBOSE, 1)
    tokens = read_tokens()
    refresh_token = tokens['refresh_token']
    if refresh_token == '':
        print('Error: refresh_token should not be empty')
        # TODO: Maybe use auth() again
        sys.exit(1)
    else:
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS,
                 'refresh_token=%s&client_id=%s&client_secret=%s&grant_type=refresh_token'
                 % (refresh_token, client_id, client_secret))
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
    # c.setopt(pycurl.VERBOSE, 1)
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
    # get_albums()
    # auth()
    tokens = read_tokens()
    update_token(tokens['refresh_token'])
