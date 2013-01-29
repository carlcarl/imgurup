#! /usr/bin/env python
# coding: utf-8

import argparse
import requests
import sys
from ConfigParser import SafeConfigParser
import json
import logging

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
CLIENT_ID = '55080e3fd8d0644'
CLIENT_SECRET = 'd021464e1b3244d6f73749b94d17916cf361da24'


def read_tokens(config='imgur.conf'):
    """
    Read the token valuse from the config file
    Args:
        config: the name of the config
    Returns:
        A tuple which contains access_token and refresh_token
    """
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
    """
    List albums of the account
    """
    url = 'https://api.imgur.com/3/account/{account}/albums'.format(account=account)
    if access_token is None:
        # If without assigning a value to access_token,
        # then just read the value from config file
        tokens = read_tokens()
        access_token = tokens['access_token']
    if access_token is None:
        logging.warning('List albums without a access token')
        headers = {'Authorization': 'Client-ID {client_id}'.format(client_id=client_id)}
    else:
        logging.info('List albums  with access token')
        logging.debug('Access token: {access_token}'.format(access_token=access_token))
        headers = {'Authorization': 'Bearer {access_token}'.format(access_token=access_token)}

    result = requests.get(url, headers=headers, verify=False).text
    result = json.loads(result)
    if check_success(result) is False:
        sys.exit(1)
    else:
        for data in result['data']:
            print('id: {d[id]}, title: {d[title]}, privacy: {d[privacy]}'.format(d=data))


def upload_image(image_path=None, anonymous=True, album_id=None):
    """
    Upload a image
    Args:
        image_path: the path of the image you want to upload
        anonymous: True or False
        album_id: the id of the album
    """
    url = 'https://api.imgur.com/3/image'
    data = {}
    headers = {}
    if anonymous:
        print('Upload image...')
        headers = {'Authorization': 'Client-ID {client_id}'.format(client_id=CLIENT_ID)}
        files = {'image': open(image_path, 'rb')}
    else:
        tokens = read_tokens()
        access_token = tokens['access_token']
        if access_token is None:
            logging.error('Access token should not be empty')
            sys.exit(1)
        else:
            print('Upload image to the album...')
            files = {'image': open(image_path, 'rb')}
            data['album_id'] = album_id
            headers = {'Authorization': 'Bearer {access_token}'.format(access_token=access_token)}

    result = requests.post(url, headers=headers, data=data, files=files, verify=False).text
    result = json.loads(result)
    if check_success(result) is False:
        sys.exit(1)
    else:
        print('Link: {link}'.format(link=result['data']['link'].replace('\\', '')))
        print('Delete link: http://imgur.com/delete/{delete}'.format(delete=result['data']['deletehash']))


def update_token(refresh_token=None):
    """
    Update the access token and refresh token
    Args:
        refresh_token: the value of the refresh_token. If it's None, then read from the config again.
    """
    url = 'https://api.imgur.com/oauth2/token'
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
        result = requests.post(url,
                               data={'refresh_token': refresh_token, 'client_id': CLIENT_ID,
                                     'client_secret': CLIENT_SECRET, 'grant_type': 'refresh_token'},
                               verify=False).text
        result = json.loads(result)
        if check_success(result) is False:
            sys.exit(1)
        else:
            write_token(result)


def auth():
    """
    Authorization
    """
    auth_url = 'https://api.imgur.com/oauth2/authorize?\
client_id={client_id}&response_type=pin&state=carlcarl'.format(client_id=CLIENT_ID)
    print ('Visit this URL in your browser: ' + auth_url)
    pin = raw_input('Enter PIN code from displayed in the browser: ')

    url = 'https://api.imgur.com/oauth2/token'
    result = requests.post(url,
                           data={'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
                                 'grant_type': 'pin', 'pin': pin},
                           verify=False).text
    result = json.loads(result)
    if check_success(result) is False:
        sys.exit(1)
    else:
        write_token(result)


def check_success(result):
    """
    Check the value of the result is success or not
    Args:
        result: the result return from the server
    Returns:
        True if success, else False
    """
    if ('success' in result) and (result['success'] is False):
        logging.error(result['data']['error'])
        logging.debug(json.dumps(result))
        return False
    return True


def write_token(result, config='imgur.conf'):
    """
    Write token value to the config
    There will be maybe more setting needed to be written to config
    So I just pass `result`
    Args:
        result: the result return from the server
        config: the name of the config file
    """
    logging.info('Access token: %s', result['access_token'])
    logging.info('Refresh token: %s', result['refresh_token'])

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


if __name__ == '__main__':
    main()
