#! /usr/bin/env python


import argparse
import pycurl
import StringIO
import sys
from ConfigParser import SafeConfigParser
import json
import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
CLIENT_ID = '55080e3fd8d0644'
CLIENT_SECRET = 'd021464e1b3244d6f73749b94d17916cf361da24'


def read_tokens(config='imgur.conf'):
    parser = SafeConfigParser()
    parser.read(config)

    try:
        access_token = parser.get('Token', 'access_token')
    except:
        logging.warning('Can\'t find access token, set to empty')
        access_token = None

    try:
        refresh_token = parser.get('Token', 'refresh_token')
    except:
        logging.warning('Can\'t find refresh token, set to empty')
        refresh_token = None

    return {'access_token': access_token,
            'refresh_token': refresh_token}


def list_albums(client_id=CLIENT_ID, account='me', access_token=None):
    url = 'https://api.imgur.com/3/account/%s/albums' % account
    c = pycurl.Curl()
    # c.setopt(pycurl.VERBOSE, 1)
    if access_token is None:
        # If without assigning a value to access_token,
        # then just read the value from config file
        tokens = read_tokens()
        access_token = tokens['access_token']
    if access_token is None:
        logging.warning('List albums without a access token')
        c.setopt(c.HTTPHEADER, ['Authorization: Client-ID %s' % client_id])
    else:
        logging.info('List albums  with access token')
        logging.debug('Access token: %s' % access_token)
        c.setopt(c.HTTPHEADER, ['Authorization: Bearer %s' % access_token])
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    result = json.loads(c.fp.getvalue())
    c.close()
    if check_success(result) is False:
        sys.exit(1)
    else:
        for data in result['data']:
            print('id: %s, title: %s, privacy: %s'
                  % (data['id'], data['title'], data['privacy']))


def upload_image(image_path=None, anonymous=True, album_id=None):
    url = 'https://api.imgur.com/3/image'
    c = pycurl.Curl()
    if anonymous:
        print('Upload image...')
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPPOST, [('image', (c.FORM_FILE, image_path))])
    else:
        tokens = read_tokens()
        access_token = tokens['access_token']
        if access_token is None:
            logging.error('Access token should not be empty')
            sys.exit(1)
        else:
            print('Upload image to the album...')
            c.setopt(c.POST, 1)
            c.setopt(c.HTTPHEADER, ['Authorization: Bearer %s' % access_token])
            c.setopt(c.HTTPPOST, [('album_id', album_id), ('image', (c.FORM_FILE, image_path))])

    # c.setopt(pycurl.VERBOSE, 1)
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    # print(c.fp.getvalue())
    result = json.loads(c.fp.getvalue())
    c.close()
    if check_success(result) is False:
        sys.exit(1)
    else:
        print('Link: %s' % result['data']['link'].replace('\\', ''))
        print('Delete link: http://imgur.com/delete/%s' % result['data']['deletehash'])


def update_token(refresh_token=None):
    url = 'https://api.imgur.com/oauth2/token'
    c = pycurl.Curl()
    # c.setopt(pycurl.VERBOSE, 1)
    if refresh_token is None:
        # Without assigning a value to the refresh_token parameter,
        # read the value from config file(Defualt is imgur.conf)
        tokens = read_tokens()
        refresh_token = tokens['refresh_token']
    if refresh_token is None:
        logging.error('Refresh token should not be empty')
        # TODO: Maybe use auth() again
        sys.exit(1)
    else:
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS,
                 'refresh_token=%s&client_id=%s&client_secret=%s&grant_type=refresh_token'
                 % (refresh_token, CLIENT_ID, CLIENT_SECRET))
        c.fp = StringIO.StringIO()
        c.setopt(pycurl.URL, url)
        c.setopt(c.WRITEFUNCTION, c.fp.write)
        c.perform()
        # print(c.fp.getvalue())
        result = json.loads(c.fp.getvalue())
        if check_success(result) is False:
            sys.exit(1)
        else:
            write_token(result)
        c.close()


def auth():
    auth_url = 'https://api.imgur.com/oauth2/authorize?client_id=%s&response_type=pin&state=carlcarl' % CLIENT_ID
    print ('Visit this URL in your browser: ' + auth_url)
    pin = raw_input('Enter PIN from browser: ')

    url = 'https://api.imgur.com/oauth2/token'
    c = pycurl.Curl()
    # c.setopt(pycurl.VERBOSE, 1)
    c.setopt(c.POST, 1)
    c.setopt(c.POSTFIELDS, 'client_id=%s&client_secret=%s&grant_type=pin&pin=%s'
             % (CLIENT_ID, CLIENT_SECRET, pin))
    c.fp = StringIO.StringIO()
    c.setopt(pycurl.URL, url)
    c.setopt(c.WRITEFUNCTION, c.fp.write)
    c.perform()
    # print(c.fp.getvalue())
    result = json.loads(c.fp.getvalue())
    if check_success(result) is False:
        sys.exit(1)
    else:
        write_token(result)
    c.close()


def check_success(result):
    if ('success' in result) and (result['success'] is False):
        logging.error(result['data']['error'])
        logging.debug(json.dumps(result))
        return False
    return True


def write_token(result, config='imgur.conf'):
    """
    There will be maybe more setting needed to be written to config
    So I just pass `result`
    """
    logging.info('Access token: %s' % result['access_token'])
    logging.info('Refresh token: %s' % result['refresh_token'])

    parser = SafeConfigParser()
    parser.read(config)
    if not parser.has_section('Token'):
        parser.add_section('Token')
    parser.set('Token', 'access_token', result['access_token'])
    parser.set('Token', 'refresh_token', result['refresh_token'])
    with open(config, 'wb') as f:
        parser.write(f)


def main():
    parser = argparse.ArgumentParser()
    p = parser.add_subparsers(title='Commands available', dest='command')
    p.add_parser('auth', help='Authorization tokens')
    p.add_parser('update', help='Update tokens')
    list_parser = p.add_parser('list', help='List all albums')
    list_parser.add_argument('-u', nargs='?', const=None, default=False,
                             metavar='username')
    upload_parser = p.add_parser('upload', help='Upload image')
    upload_parser.add_argument('-d', default=None,
                               help='The album you want your image to be uploaded to',
                               metavar='<ALBUM_ID>')
    upload_parser.add_argument('-f', required=True,
                               help='The image you want to upload',
                               metavar='<IMAGE_PATH>')
    args = parser.parse_args()

    if args.command == 'auth':
        logging.debug('auth token')
        auth()
    elif args.command == 'update':
        logging.debug('update token')
        update_token()
    elif args.command == 'list':
        logging.debug('list albums')
        list_albums(args.u)
    elif args.command == 'upload':
        logging.debug('upload image')
        anonymous = True if args.d is None else False
        upload_image(args.f, anonymous, args.d)
    else:
        logging.error('Unknown commands')
        logging.debug(args)
        sys.exit(1)

    # upload_image('/home/carlcarl/Downloads/rEHCq.jpg', False, '9DpVh')


if __name__ == '__main__':
    main()
