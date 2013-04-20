#! /usr/bin/env python
# -*- coding: utf-8 -*-

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


class Env:
    CLI = 0
    KDE = 1

    @staticmethod
    def detect_env(is_gui):
        if is_gui is True and os.environ.get('KDE_FULL_SESSION') == 'true':
            return Env.KDE
        else:
            return Env.CLI


class Imgur(object):
    CLIENT_ID = '55080e3fd8d0644'
    CLIENT_SECRET = 'd021464e1b3244d6f73749b94d17916cf361da24'
    CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + '/imgur.conf'
    connect = None
    access_token = None
    refresh_token = None
    env = Env.CLI

    def __init__(self):
        pass

    def fatal_error(self, msg='Error'):
        if self.env == Env.KDE:
            p1 = subprocess.Popen(['kdialog', '--error', msg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p1.communicate()[0].strip()
        else:
            logging.error(msg)
        sys.exit(1)

    def set_tokens_using_config(self):
        '''
        Read the token valuse from the config file
        Set tokens to None if can't be found in config
        '''
        parser = SafeConfigParser()
        parser.read(self.CONFIG_PATH)

        try:
            self.access_token = parser.get('Token', 'access_token')
        except:
            logging.warning('Can\'t find access token, set to empty')
            self.access_token = None

        try:
            self.refresh_token = parser.get('Token', 'refresh_token')
        except:
            logging.warning('Can\'t find refresh token, set to empty')
            self.refresh_token = None

    def get_album_list(self, account='me'):
        '''
        Return albums list of the account
        Returns:
            albums(json)
        '''
        url = '/3/account/{account}/albums'.format(account=account)

        if account == 'me':
            if self.access_token is None:
                # If without assigning a value to access_token,
                # then just read the value from config file
                self.set_tokens_using_config()
            logging.info('Get album list with access token')
            logging.debug('Access token: {access_token}'.format(access_token=self.access_token))
            headers = {'Authorization': 'Bearer {access_token}'.format(access_token=self.access_token)}
        else:
            logging.info('Get album list without a access token')
            headers = {'Authorization': 'Client-ID {client_id}'.format(client_id=self.CLIENT_ID)}

        self.connect.request('GET', url, None, headers)
        result = json.loads(self.connect.getresponse().read())
        return result

    def update_tokens(self):
        '''
        Update the access token and refresh token
        '''
        url = '/oauth2/token'

        if self.refresh_token is None:
            self.set_tokens_using_config()
        if self.refresh_token is None:
            self.fatal_error('Can\'t read the value of refresh_token, you may have to authorize again')

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        params = urllib.urlencode({'refresh_token': self.refresh_token, 'client_id': self.CLIENT_ID,
                                   'client_secret': self.CLIENT_SECRET, 'grant_type': 'refresh_token'})
        self.connect.request('POST', url, params, headers)
        result = json.loads(self.connect.getresponse().read())
        if self.check_success(result) is True:
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']
        else:
            self.fatal_error('Update tokens fail')

    def ask_pin_code(self):
        '''
        Ask user for pin code
        Returns:
            pin code
        '''
        auth_url = 'https://api.imgur.com/oauth2/authorize?\
client_id={client_id}&response_type=pin&state=carlcarl'.format(client_id=self.CLIENT_ID)
        auth_msg = 'This is the first time you use this program, you have to visit this URL in your browser and copy the PIN code: ' + auth_url
        token_msg = 'Enter PIN code displayed in the browser: '

        if self.env == Env.KDE:
            p1 = subprocess.Popen(['kdialog', '--msgbox', auth_msg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p1.communicate()[0].strip()

            p1 = subprocess.Popen(['kdialog', '--title', 'Input dialog', '--inputbox', token_msg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pin = p1.communicate()[0].strip()
        else:
            print(auth_msg)
            pin = raw_input(token_msg)

        return pin

    def auth(self):
        '''
        Authorization
        '''
        token_url = '/oauth2/token'

        pin = self.ask_pin_code()
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.connect.request('POST', token_url, urllib.urlencode({'client_id': self.CLIENT_ID, 'client_secret': self.CLIENT_SECRET,
                                                                  'grant_type': 'pin', 'pin': pin}), headers)
        result = json.loads(self.connect.getresponse().read())
        if (self.check_success(result) is True) and (result['access_token'] is not None) and (result['refresh_token'] is not None):
            self.access_token = result['access_token']
            self.refresh_token = result['refresh_token']
        else:
            self.fatal_error('Authorization error')

    def check_success(self, result):
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

    def write_tokens_to_config(self):
        '''
        Write token value to the config
        There will be maybe more setting needed to be written to config
        So I just pass `result`
        Args:
            result: the result return from the server
            config: the name of the config file
        '''
        logging.debug('Access token: %s', self.access_token)
        logging.debug('Refresh token: %s', self.refresh_token)

        parser = SafeConfigParser()
        parser.read(self.CONFIG_PATH)
        if not parser.has_section('Token'):
            parser.add_section('Token')
        parser.set('Token', 'access_token', self.access_token)
        parser.set('Token', 'refresh_token', self.refresh_token)
        with open(self.CONFIG_PATH, 'wb') as f:
            parser.write(f)

    def random_string(self, length):
        '''
        From http://stackoverflow.com/questions/68477
        '''
        return ''.join(random.choice(string.letters) for ii in range(length + 1))

    def encode_multipart_data(self, data, files):
        '''
        From http://stackoverflow.com/questions/68477
        '''
        boundary = self.random_string(30)

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

    def ask_image_path(self):
        if self.env == Env.KDE:
            p1 = subprocess.Popen(['kdialog', '--getopenfilename', '.'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            image_path = p1.communicate()[0].strip()
            if image_path == '':  # Cancel dialog
                sys.exit(1)
        else:
            image_path = input('Enter your image location: ')
        return image_path

    def ask_album_id(self):
        '''
        Ask user to choose a album to upload or not belong to any album
        Returns:
            album_id: the id of the album
        '''
        albums_json = self.get_album_list()
        if self.check_success(albums_json) is False:
            if albums_json['data']['error'] == 'Unauthorized':
                self.update_tokens()
                self.write_tokens_to_config()
                albums_json = self.get_album_list()
                if self.check_success(albums_json) is False:
                    self.fatal_error('Get albums error(auth)')
            else:
                self.fatal_error('Get albums unknown error')
        albums = albums_json['data']
        i = 1
        data_map = []
        no_album_msg = 'Do not move to any album'
        album_id = None

        if self.env == Env.KDE:
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
            album_id = data_map[n - 1]['id']  # number select start from 1, so minus 1
            logging.info('Upload the image to the album...')
        else:
            logging.info('Upload the image...')
        return album_id

    def show_link(self, result):
        '''
        Show image link
        Args:
            result: image upload response(json)
        '''
        if self.env == Env.KDE:
            s = 'Link: {link}'.format(link=result['data']['link'].replace('\\', ''))
            s = s + '\n' + 'Delete link: http://imgur.com/delete/{delete}'.format(delete=result['data']['deletehash'])
            p1 = subprocess.Popen(['kdialog', '--msgbox', s], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p1.communicate()[0].strip()
        else:
            print('Link: {link}'.format(link=result['data']['link'].replace('\\', '')))
            print('Delete link: http://imgur.com/delete/{delete}'.format(delete=result['data']['deletehash']))

    def upload_image(self, image_path=None, anonymous=True, album_id=None, is_gui=False):
        '''
        Upload a image
        Args:
            image_path: the path of the image you want to upload
            anonymous: True or False
            album_id: the id of the album
        '''
        url = '/3/image'
        self.connect = httplib.HTTPSConnection('api.imgur.com')
        data = {}
        headers = {}
        self.env = Env.detect_env(is_gui)
        if image_path is None:
            image_path = self.ask_image_path()
        if anonymous:  # Anonymous account
            print('Upload the image anonymously...')
            files = {'image': image_path}
            body, headers = self.encode_multipart_data(data, files)
            headers['Authorization'] = 'Client-ID {client_id}'.format(client_id=self.CLIENT_ID)
        else:
            self.set_tokens_using_config()
            if self.access_token is None or self.refresh_token is None:
                # If the tokens are empty, means this is the first time using this
                # tool, so call auth() to get tokens
                self.auth()
                self.write_tokens_to_config()
            if album_id is None:  # Means user doesn't specify the album
                album_id = self.ask_album_id()
                if album_id is not None:
                    data['album_id'] = album_id
                else:
                    pass  # If it's None, means user doesn't want to upload to any album
            else:
                logging.info('Upload the image to the album...')
                data['album_id'] = album_id

            files = {'image': image_path}
            body, headers = self.encode_multipart_data(data, files)
            headers['Authorization'] = 'Bearer {access_token}'.format(access_token=self.access_token)

        self.connect.request('POST', url, body, headers)
        result = json.loads(self.connect.getresponse().read())
        if self.check_success(result) is False:
            if result['data']['error'] == 'Unauthorized':
                self.update_tokens()
                self.write_tokens_to_config()
                self.connect.request('POST', url, body, headers)
                result = json.loads(self.connect.getresponse().read())
                if self.check_success(result) is False:
                    self.fatal_error('Upload image error(auth)')
            else:
                self.fatal_error('Upload image error')
        self.show_link(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f',
                        help='The image you want to upload',
                        metavar='<image path>')
    parser.add_argument('-d', nargs='?',
                        default=None,
                        help='The album id you want your image to be uploaded to',
                        metavar='<album id>')
    parser.add_argument('-g', action='store_true',
                        help='GUI mode')
    parser.add_argument('-n', action='store_true',
                        help='Anonymous upload')
    args = parser.parse_args()

    imgur = Imgur()
    imgur.upload_image(args.f, args.n, args.d, args.g)


if __name__ == '__main__':
    main()
