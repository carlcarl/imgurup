#! /usr/bin/env python
# coding: utf-8

import argparse
import httplib
import urllib
import random
import string
import mimetypes
import sys
from ConfigParser import SafeConfigParser
import json
import logging
import os
import subprocess

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
CLIENT_ID = '55080e3fd8d0644'
CLIENT_SECRET = 'd021464e1b3244d6f73749b94d17916cf361da24'
is_gui = False
access_token = None
refresh_token = None
connect = None


class Env:
    CLI = 0
    KDE = 1


def detect_env():
    global is_gui
    if is_gui is True and os.environ.get('KDE_FULL_SESSION') == 'true':
        return Env.KDE
    else:
        return Env.CLI


def read_tokens(config='imgur.conf'):
    '''
    Read the token valuse from the config file
    Args:
        config: the name of the config
    '''
    parser = SafeConfigParser()
    parser.read(config)

    global access_token, refresh_token
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


def list_albums(account='me'):
    '''
    List albums of the account
    '''
    for data in get_albums(account, access_token)['data']:
        print('id: {d[id]}, title: {d[title]}, privacy: {d[privacy]}'.format(d=data))


def get_albums(account='me'):
    '''
    Return albums(json) of the account
    '''
    url = '/3/account/{account}/albums'.format(account=account)

    global access_token
    if account != 'me':
        logging.info('Get album list without a access token')
        headers = {'Authorization': 'Client-ID {client_id}'.format(client_id=CLIENT_ID)}
    else:
        if access_token is None:
            # If without assigning a value to access_token,
            # then just read the value from config file
            read_tokens()
        logging.info('Get album list with access token')
        logging.debug('Access token: {access_token}'.format(access_token=access_token))
        headers = {'Authorization': 'Bearer {access_token}'.format(access_token=access_token)}

    connect.request('GET', url, None, headers)
    result = connect.getresponse().read()
    result = json.loads(result)
    return result


def update_token():
    '''
    Update the access token and refresh token
    '''
    url = '/oauth2/token'

    global access_token, refresh_token
    if refresh_token is None:
        # Without assigning a value to the refresh_token parameter,
        # read the value from config file(Defualt is imgur.conf)
        read_tokens()
    if refresh_token is None:
        logging.error('Refresh token should not be empty')
        # TODO: Maybe use auth() again
        sys.exit(1)
    else:
        global connect
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        params = urllib.urlencode({'refresh_token': refresh_token, 'client_id': CLIENT_ID,
                                   'client_secret': CLIENT_SECRET, 'grant_type': 'refresh_token'})
        connect.request('POST', url, params, headers)
        result = connect.getresponse().read()
        result = json.loads(result)
        if check_success(result) is False:
            sys.exit(1)
        else:
            access_token = result['access_token']
            refresh_token = result['refresh_token']
            write_token(result)


def auth():
    '''
    Authorization
    '''
    auth_url = 'https://api.imgur.com/oauth2/authorize?\
    client_id={client_id}&response_type=pin&state=carlcarl'.format(client_id=CLIENT_ID)
    auth_msg = 'This is the first time you use this program, you have to visit this URL in your browser and copy the PIN code: ' + auth_url

    token_msg = 'Enter PIN code displayed in the browser: '
    token_url = '/oauth2/token'

    env = detect_env()
    if env == Env.KDE:
        p1 = subprocess.Popen(['kdialog', '--msgbox', auth_msg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p1.communicate()[0].strip()

        p1 = subprocess.Popen(['kdialog', '--title', 'Input dialog', '--inputbox', token_msg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pin = p1.communicate()[0].strip()
    else:
        print(auth_msg)
        pin = raw_input(token_msg)

    connect.request('POST', token_url, urllib.urlencode({'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
                                                         'grant_type': 'pin', 'pin': pin}))
    result = json.loads(connect.getresponse().read())
    if check_success(result) is False:
        sys.exit(1)
    else:
        global access_token, refresh_token
        access_token = result['access_token']
        refresh_token = result['refresh_token']
        write_token(result)


def check_success(result):
    '''
    Check the value of the result is success or not
    Args:
        result: the result return from the server
    Returns:
        True if success, else False
    '''
    if ('success' in result) and (result['success'] is False):
        logging.error(result['data']['error'])
        logging.debug(json.dumps(result))
        return False
    return True


def write_token(result, config='imgur.conf'):
    '''
    Write token value to the config
    There will be maybe more setting needed to be written to config
    So I just pass `result`
    Args:
        result: the result return from the server
        config: the name of the config file
    '''
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


def random_string(length):
    '''
    From http://stackoverflow.com/questions/68477
    '''
    return ''.join(random.choice(string.letters) for ii in range(length + 1))


def encode_multipart_data(data, files):
    '''
    From http://stackoverflow.com/questions/68477
    '''
    boundary = random_string(30)

    def get_content_type(filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def encode_field(field_name):
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"' % field_name,
                '', str(data[field_name]))

    def encode_file(field_name):
        filename = files[field_name]
        return ('--' + boundary,
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename),
                'Content-Type: %s' % get_content_type(filename),
                '', open(filename, 'rb').read())

    lines = []
    for name in data:
        lines.extend(encode_field(name))
    for name in files:
        lines.extend(encode_file(name))
    lines.extend(('--%s--' % boundary, ''))
    body = '\r\n'.join(lines)

    headers = {'content-type': 'multipart/form-data; boundary=' + boundary,
               'content-length': str(len(body))}

    return body, headers


def upload_image(image_path=None, anonymous=True, album_id=None):
    '''
    Upload a image
    Args:
        image_path: the path of the image you want to upload
        anonymous: True or False
        album_id: the id of the album
    '''
    url = '/3/image'
    global connect
    connect = httplib.HTTPSConnection('api.imgur.com')
    data = {}
    headers = {}
    env = detect_env()
    if image_path is None:
        if env == Env.KDE:
            p1 = subprocess.Popen(['kdialog', '--getopenfilename', '.'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            image_path = p1.communicate()[0].strip()
            if image_path == '':  # Cancel dialog
                sys.exit(1)
        else:
            image_path = input('Enter your image location: ')
    if anonymous:  # Anonymous account
        print('Upload the image anonymously...')
        files = {'image': image_path}
        body, headers = encode_multipart_data(data, files)
        headers['Authorization'] = 'Client-ID {client_id}'.format(client_id=CLIENT_ID)
    else:
        read_tokens()
        if access_token is None or refresh_token is None:
            # If the tokens are empty, means this is the first time using this
            # tool, so call auth() to get tokens
            auth()
            if access_token is None or refresh_token is None:
                logging.error('Tokens should not be empty')
                sys.exit(1)

        if album_id is None:  # Means user doesn't specify the album
            albums_json = get_albums()
            if check_success(albums_json) is False:
                if albums_json['data']['error'] == 'Unauthorized':
                    update_token()
                    albums_json = get_albums()
                    if check_success(albums_json) is False:
                        sys.exit(1)
                else:
                    sys.exit(1)
            albums = albums_json['data']
            i = 1
            data_map = []
            no_album_msg = 'Do not upload to any album'

            if env == Env.KDE:
                arg = ['kdialog', '--menu', '"Choose the album"']
                for d in albums:
                    arg.append(str(i))
                    arg.append('{d[title]}({d[privacy]})'.format(d=d))
                    data_map.append(d)
                    i += 1
                arg.append(str(i))
                arg.append(no_album_msg)
                p1 = subprocess.Popen(arg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                n = p1.communicate()[0].strip()
                if n == '':
                    sys.exit(1)
                n = int(n)
            else:
                print('Enter the number of the album you want to upload: ')
                for d in albums:
                    print('{i}) {d[title]}({d[privacy]})'.format(i=i, d=d))
                    data_map.append(d)
                    i += 1
                print('{i}) {no_album_msg}'.format(i=i, no_album_msg=no_album_msg))
                n = int(input())

            if n != i:  # If the user doesn't choose 'Not belong to any album'
                data['album_id'] = data_map[n - 1]['id']  # number select start from 1, so minus 1
                logging.info('Upload the image to the album...')
            else:
                logging.info('Upload the image...')
        else:
            logging.info('Upload the image to the album...')
            data['album_id'] = album_id

        files = {'image': image_path}
        body, headers = encode_multipart_data(data, files)
        headers['Authorization'] = 'Bearer {access_token}'.format(access_token=access_token)

    connect.request('POST', url, body, headers)
    result = json.loads(connect.getresponse().read())
    if check_success(result) is False:
        if result['data']['error'] == 'Unauthorized':
            update_token()
            connect.request('POST', url, body, headers)
            result = json.loads(connect.getresponse().read())
            if check_success(result) is False:
                sys.exit(1)
        else:
            sys.exit(1)

    if env == Env.KDE:
        s = 'Link: {link}'.format(link=result['data']['link'].replace('\\', ''))
        s = s + '\n' + 'Delete link: http://imgur.com/delete/{delete}'.format(delete=result['data']['deletehash'])
        p1 = subprocess.Popen(['kdialog', '--msgbox', s], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p1.communicate()[0].strip()
    else:
        print('Link: {link}'.format(link=result['data']['link'].replace('\\', '')))
        print('Delete link: http://imgur.com/delete/{delete}'.format(delete=result['data']['deletehash']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f',
                        help='The image you want to upload',
                        metavar='<IMAGE_PATH>')
    parser.add_argument('-d', nargs='?',
                        default=None,
                        help='The album you want your image to be uploaded to',
                        metavar='<ALBUM_ID>')
    parser.add_argument('-g', action='store_true',
                        help='GUI mode')
    parser.add_argument('-n', action='store_true',
                        help='Anonymous')
    args = parser.parse_args()

    if args.g is True:
        global is_gui
        is_gui = True

    upload_image(args.f, args.n, args.d)


if __name__ == '__main__':
    main()
