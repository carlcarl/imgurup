#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import argparse
import logging
import subprocess

import random
import mimetypes
import json
from abc import ABCMeta
from abc import abstractmethod
import time
import shutil

if sys.version_info >= (3,):
    import http.client as httplib
    from urllib.parse import urlencode
    from configparser import SafeConfigParser
    from configparser import NoOptionError, NoSectionError
    from string import ascii_letters
else:
    import httplib
    from urllib import urlencode
    from ConfigParser import SafeConfigParser
    from ConfigParser import NoOptionError, NoSectionError
    from string import letters as ascii_letters

# To flake8, raw_input is a undefined name in python3
# So we need to use the try except method to make compatibility
try:
    input = raw_input
except NameError:
    pass

logger = logging.getLogger(__name__)


class ImgurFactory:
    """Used to produce imgur instance.
    ex: `imgur = ImgurFactory.get_imgur(ImgurFactory.detect_env(is_gui))`
    """

    def __init__(self):
        pass

    @staticmethod
    def get_instance(prefer_gui=True, **kwargs):
        """Detect environment

        :param prefer_gui: If False, choose CLI,
         otherwise detect settings and choose a GUI mode
        :type prefer_gui: bool
        :param kwargs: remaining keyword arguments passed to Imgur
        :tpe kwargs: dict
        :return: Subclass of Imgur
        :rtype: Imgur
        """
        if prefer_gui and os.environ.get('KDE_FULL_SESSION') == 'true':
            return KDEImgur(**kwargs)
        elif prefer_gui and sys.platform == 'darwin':
            return MacImgur(**kwargs)
        elif prefer_gui and os.environ.get('DESKTOP_SESSION') == 'gnome':
            return ZenityImgur(**kwargs)
        elif prefer_gui and os.environ.get('DESKTOP_SESSION') == 'pantheon':
            return ZenityImgur(**kwargs)
        else:
            return CLIImgur(**kwargs)


class ImgurError(Exception):
    pass


class Imgur:
    __metaclass__ = ABCMeta
    CONFIG_PATH = os.path.expanduser("~/.imgurup.conf")

    def __init__(self,
                 client_id='55080e3fd8d0644',
                 client_secret='d021464e1b3244d6f73749b94d17916cf361da24'):
        """Initialize connection, client_id and client_secret
        Users can use their own client_id to make requests
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = None
        self._refresh_token = None
        self._api_url = None
        self._connect = None
        self._request = None

        self._auth_url = (
            'https://api.imgur.com/oauth2/authorize?'
            'client_id={c_id}&response_type=pin&state=carlcarl'.format(
                c_id=self._client_id
            )
        )
        self._auth_msg = ('This is the first time you use this program, '
                          'you have to visit this URL in your browser '
                          'and copy the PIN code: \n')
        self._auth_msg_with_url = self._auth_msg + self._auth_url
        self._enter_token_msg = 'Enter PIN code displayed in the browser: '
        self._no_album_msg = 'Do not move to any album'

    def connect(self, url='api.imgur.com'):
        self._api_url = url
        self._connect = httplib.HTTPSConnection(url)
        self._request = self._connect.request

    def retry(errors=(ImgurError, httplib.BadStatusLine)):
        """Retry calling the decorated function using an exponential backoff.

        http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
        original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
        """
        tries = 2
        delay = 1

        def deco_retry(f):
            def f_retry(self, *args, **kwargs):
                for attempt in range(tries):
                    try:
                        result = f(self, *args, **kwargs)
                        return result['data']
                    except errors:
                        logger.info('reauthorize...')
                        self.request_new_tokens_and_update()
                        self.write_tokens_to_config()
                        time.sleep(delay)
                else:
                    self.show_error_and_exit(
                        'Error in {function}'.format(function=f.__name__)
                    )
            return f_retry  # true decorator
        return deco_retry

    @abstractmethod
    def get_error_dialog_args(self, msg='Error'):
        """Return the subprocess args of display error dialog

        :param msg: Error message
        :type msg: str
        :return: A list include dialog command,
         ex: ['kdialog', '--msgbox', 'hello']
        :rtype: list
        """

    def show_error_and_exit(self, msg='Error'):
        """Display error message and exit the program

        :param msg: Error message
        :type msg: str
        """
        args = self.get_error_dialog_args(msg)
        if args:
            p = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            p.communicate()
        logger.error(msg)
        sys.exit(1)

    def set_tokens_using_config(self):
        """Read the token value from the config file
        Set tokens to None if can't be found in config
        """
        parser = SafeConfigParser()
        try:
            fp = open(self.CONFIG_PATH)
        except IOError:
            logger.error('.imgurup.conf not exists, create the file...')
            fp = open(self.CONFIG_PATH, 'w+')
        parser.readfp(fp)

        try:
            self._access_token = parser.get('Token', 'access_token')
        except (NoOptionError, NoSectionError):
            logger.warning('Can\'t find access token, set to empty')
            self._access_token = None
        try:
            self._refresh_token = parser.get('Token', 'refresh_token')
        except (NoOptionError, NoSectionError):
            logger.warning('Can\'t find refresh token, set to empty')
            self._refresh_token = None
        fp.close()

    def _get_json_response(self):
        """Get the json response of request

        :return: Json response
        :rtype: dict
        """
        response = self._connect.getresponse().read()
        return json.loads(response.decode('utf-8'))

    @retry()
    def request_album_list(self, account='me'):
        """Request album list with the account

        :param account: The account name, 'me' means yourself
        :type account: str
        :return: Response of requesting albums list (json)
        :rtype: list of dict
        """
        url = '/3/account/{account}/albums'.format(account=account)

        if account == 'me':
            if self._access_token is None:
                # If without assigning a value to access_token,
                # then just read the value from config file
                self.set_tokens_using_config()
            logger.info('Get album list with access token')
            logger.debug(
                'Access token: %s',
                self._access_token
            )
            headers = {
                'Authorization': 'Bearer {token}'.format(
                    token=self._access_token
                )
            }
        else:
            logger.info('Get album list without a access token')
            headers = {
                'Authorization': 'Client-ID {_id}'.format(_id=self._client_id)
            }

        self._request('GET', url, None, headers)
        json_response = self._get_json_response()
        if not self.is_success(json_response):
            raise ImgurError
        return json_response

    def request_new_tokens(self):
        """Request new tokens

        :return: json tokens
        :rtype: dict
        """
        url = '/oauth2/token'
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        params = urlencode(
            {
                'refresh_token': self._refresh_token,
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'grant_type': 'refresh_token'
            }
        )
        self._request('POST', url, params, headers)
        return self._get_json_response()

    def request_new_tokens_and_update(self):
        """Request and update the access token and refresh token
        """

        if self._refresh_token is None:
            self.set_tokens_using_config()
        if self._refresh_token is None:
            self.show_error_and_exit(
                'Can\'t read the value of refresh_token, '
                'you may have to authorize again'
            )

        response = self.request_new_tokens()
        if self.is_success(response):
            self._access_token = response['access_token']
            self._refresh_token = response['refresh_token']
        else:
            self.show_error_and_exit('Update tokens fail')

    @abstractmethod
    def get_auth_msg_dialog_args(self, auth_msg, auth_url):
        """Return the subprocess args of show authorization message dialog

        :param auth_msg: Authorization message
        :type auth_msg: str
        :param auth_url: Authorization url
        :type auth_url: str
        :return: A list include dialog command
        :rtype: list
        """

    @abstractmethod
    def get_enter_pin_dialog_args(self, token_msg):
        """Return the subprocess args of enter pin dialog

        :param token_msg: Enter token message
        :type token_msg: str
        :return: A list include dialog command
        :rtype: list
        """

    def ask_pin(self, auth_msg, auth_url, enter_token_msg):
        """Ask user for pin code

        :param auth_msg: Authorization message
        :type auth_msg: str
        :param auth_url: Authorization url
        :type auth_url: str
        :param enter_token_msg: Prompt token message
        :type enter_token_msg: str
        :return: pin code
        :rtype: str
        """
        args = self.get_auth_msg_dialog_args(
            auth_msg,
            auth_url
        )
        auth_msg_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        auth_msg_dialog.communicate()

        args = self.get_enter_pin_dialog_args(enter_token_msg)
        ask_pin_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pin = ask_pin_dialog.communicate()[0].strip()
        return pin

    def auth(self):
        """Authorization
        """
        token_url = '/oauth2/token'

        pin = self.ask_pin(
            self._auth_msg,
            self._auth_url,
            self._enter_token_msg
        )
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        self._request(
            'POST',
            token_url,
            urlencode(
                {
                    'client_id': self._client_id,
                    'client_secret': self._client_secret,
                    'grant_type': 'pin',
                    'pin': pin
                }
            ),
            headers
        )
        result = self._get_json_response()
        if self.is_success(result):
            self._access_token = result['access_token']
            self._refresh_token = result['refresh_token']
        else:
            self.show_error_and_exit('Authorization error')

    def is_success(self, response):
        """Check the value of the result is success or not

        :param response: The result return from the server
        :type response: dict
        :return: True if success, else False
        :rtype: bool
        """
        if ('success' in response) and (not response['success']):
            logger.info(response['data']['error'])
            logger.debug(json.dumps(response))
            return False
        return True

    def write_tokens_to_config(self):
        """Write token value to the config
        """
        logger.debug('Access token: %s', self._access_token)
        logger.debug('Refresh token: %s', self._refresh_token)

        parser = SafeConfigParser()
        parser.read(self.CONFIG_PATH)
        if not parser.has_section('Token'):
            parser.add_section('Token')
        parser.set('Token', 'access_token', self._access_token)
        parser.set('Token', 'refresh_token', self._refresh_token)
        with open(self.CONFIG_PATH, 'w') as f:
            parser.write(f)

    @abstractmethod
    def get_ask_image_path_dialog_args(self):
        """Return the subprocess args of file dialog

        :return: A list include dialog command,
         ex: ['kdialog', '--msgbox', 'hi']
        :rtype: list
        """

    def ask_image_path(self):
        """Display a file dialog and prompt the user to select a image

        :return: image path
        :rtype: str
        """
        args = self.get_ask_image_path_dialog_args()
        ask_image_path_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        image_path = ask_image_path_dialog.communicate()[0].strip()
        if image_path == '':  # Cancel dialog
            sys.exit(1)

        return image_path

    def _get_album_id(self, data_map, album_number):
        """Get the album id from the list

        :param data_map: Albums list
        :type data_map: list of dict
        :param album_number: The album NO.
        :type album_number: int
        :return: Album id
        :rtype: str
        """
        return data_map[album_number - 1]['id']

    @abstractmethod
    def get_ask_album_id_dialog_args(self, albums, no_album_msg):
        """Return the subprocess args of choose album dialog

        :param albums: Albums list
        :type albums: list of dict
        :param no_album_msg: `Not belong to any album` message
        :return: A list include dialog command
        :rtype: list
        """

    def ask_album_id(self, albums):
        """Ask user to choose a album to upload or not belong to any album

        :param albums: Albums list
        :type albums: list of dict
        :return: The id of the album
        :rtype: str
        """
        args = self.get_ask_album_id_dialog_args(albums, self._no_album_msg)
        choose_album_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        album_number = choose_album_dialog.communicate()[0].strip()
        if album_number == '':
            self.show_error_and_exit('Album number should not be empty')
        album_number = int(album_number)
        data_map = []
        for album in albums:
            data_map.append(album)
        return self._get_album_id(data_map, album_number)

    @abstractmethod
    def get_show_link_dialog_args(self, links):
        """Return the subprocess args of show link dialog

        :param links: String of the image link and delete link
        :type links: str
        :return: A list include dialog command
        :rtype: list
        """

    def show_link(self, image_link, delete_hash):
        """Show image link

        :param image_link: Image link
        :type image_link: str
        :param delete_hash: Image delete hash string
        :type delete_hash: str
        """
        link = 'Link: {link}'.format(link=image_link.replace('\\', ''))
        links = (
            link + '\nDelete link: http://imgur.com/delete/' +
            '{delete}'.format(delete=delete_hash)
        )
        args = self.get_show_link_dialog_args(links)
        show_link_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        show_link_dialog.communicate()

    def _encode_multipart_data(self, data, files):
        """From http://stackoverflow.com/questions/68477
        """

        def random_string(length):
            return ''.join(
                random.choice(ascii_letters) for ii in range(length + 1)
            )

        def get_content_type(filename):
            return (
                mimetypes.guess_type(filename)[0] or
                'application/octet-stream'
            )

        def encode_field(field_name):
            return (
                ('--' + boundary).encode('utf-8'),
                ('Content-Disposition: form-data; name="%s"' % (
                    field_name
                )).encode('utf-8'),
                b'', data[field_name].encode('utf-8')
            )

        def encode_file(field_name):
            filename = files[field_name]
            return (
                ('--' + boundary).encode('utf-8'),
                ('Content-Disposition: form-data; name="%s"; filename="%s"' % (
                    field_name, filename
                )).encode('utf-8'),
                ('Content-Type: %s' % (
                    get_content_type(filename)
                )).encode('utf-8'),
                b'', open(filename, 'rb').read()
            )

        boundary = random_string(30)
        lines = []
        for name in data:
            lines.extend(encode_field(name))
        for name in files:
            lines.extend(encode_file(name))
        lines.extend((('--%s--' % boundary).encode('utf-8'), b''))
        body = '\r\n'.encode('utf-8').join(lines)

        headers = {
            'content-type': 'multipart/form-data; boundary=' + boundary,
            'content-length': str(len(body))
        }

        return body, headers

    @retry()
    def request_upload_image(self, url, body, headers):
        """Request upload image

        :param url: Upload url
        :type url: str
        :param body: The content string of the request
        :type body: str
        :param headers: The headers of the request
        :type headers: dict
        :return: Response of upload image
        :rtype: dict
        """
        self._request('POST', url, body, headers)
        json_response = self._get_json_response()
        if not self.is_success(json_response):
            raise ImgurError
        return json_response

    def upload(self, image_path=None, meta=None):
        """Upload a image

        :param image_path: The path of the image you want to upload
        :type image_path: str
        :param meta: Meta information of anonymous and album id
        :type meta: dict
        :return:
        """
        url = '/3/image'
        post_data = {}
        headers = {}
        files = {'image': image_path}

        if image_path is None:
            image_path = self.ask_image_path()
        if meta['image_name_as_title']:
            post_data['title'] = image_path.split(os.sep)[-1]
        if meta['anonymous']:  # Anonymous account
            print('Upload the image anonymously...')
            body, headers = self._encode_multipart_data(post_data, files)
            headers['Authorization'] = 'Client-ID {client_id}'.format(
                client_id=self._client_id
            )
        else:
            self.set_tokens_using_config()
            if self._access_token is None or self._refresh_token is None:
                # If the tokens are empty, means this is the first time
                # using this tool, so call auth() to get tokens
                self.auth()
                self.write_tokens_to_config()
            if (meta['album_id'] is None) or meta['ask']:
                # Means user doesn't specify the album
                albums = self.request_album_list()
                meta['album_id'] = self.ask_album_id(albums)
                if meta['album_id'] is not None:
                    post_data['album_id'] = meta['album_id']
                    logger.info('Upload the image to the album...')
                else:
                    # If it's None, means user doesn't want to
                    # upload to any album
                    logger.info('Upload the image...')
            else:
                logger.info('Upload the image to the album...')
                post_data['album_id'] = meta['album_id']

            body, headers = self._encode_multipart_data(post_data, files)
            headers['Authorization'] = 'Bearer {access_token}'.format(
                access_token=self._access_token
            )

        result = self.request_upload_image(url, body, headers)
        self.show_link(result['link'], result['deletehash'])


class CLIImgur(Imgur):

    def get_error_dialog_args(self, msg='Error'):
        return None

    def get_auth_msg_dialog_args(self, auth_msg, auth_url):
        raise NotImplementedError()

    def get_enter_pin_dialog_args(self, token_msg):
        raise NotImplementedError()

    def ask_pin(self, auth_msg, auth_url, enter_token_msg):
        print(auth_msg + auth_url)
        pin = input(enter_token_msg)
        return pin

    def get_ask_image_path_dialog_args(self):
        raise NotImplementedError()

    def ask_image_path(self):
        image_path = input('Enter your image location: ')
        return image_path

    def get_ask_album_id_dialog_args(self, albums, no_album_msg):
        raise NotImplementedError()

    def ask_album_id(self, albums):
        i = 1
        data_map = []
        print('Enter the number of the album you want to upload: ')
        for album in albums:
            print(
                '{i}) {album[title]}({album[privacy]})'.format(
                    i=i, album=album
                )
            )
            data_map.append(album)
            i += 1
        print('{i}) {msg}'.format(i=i, msg=self._no_album_msg))
        data_map.append({'id': None})
        album_number = int(input())
        # Get [album_number-1] from the list
        return self._get_album_id(data_map, album_number)

    def get_show_link_dialog_args(self, links):
        raise NotImplementedError()

    def show_link(self, image_link, delete_hash):
        print('Link: {link}'.format(link=image_link.replace('\\', '')))
        print(
            'Delete link: http://imgur.com/delete/{delete}'.format(
                delete=delete_hash
            )
        )


class KDEImgur(Imgur):

    def get_error_dialog_args(self, msg='Error'):
        args = [
            'kdialog',
            '--error',
            msg,
        ]
        return args

    def get_auth_msg_dialog_args(self, auth_msg, auth_url):
        args = [
            'kdialog',
            '--msgbox',
            auth_msg + auth_url,
        ]
        return args

    def get_enter_pin_dialog_args(self, token_msg):
        args = [
            'kdialog',
            '--title',
            'Input dialog',
            '--inputbox',
            token_msg,
        ]
        return args

    def get_ask_image_path_dialog_args(self):
        args = [
            'kdialog',
            '--getopenfilename',
            '.',
        ]
        return args

    def get_ask_album_id_dialog_args(self, albums, no_album_msg):
        i = 1
        args = ['kdialog', '--menu', '"Choose the album"']
        for album in albums:
            args.append(str(i))
            args.append('{album[title]}({album[privacy]})'.format(album=album))
            i += 1
        args.append(str(i))
        args.append(no_album_msg + '(public)')

        return args

    def get_show_link_dialog_args(self, links):
        args = [
            'kdialog',
            '--msgbox',
            links,
        ]
        return args


class MacImgur(Imgur):

    def get_error_dialog_args(self, msg='Error'):
        args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to display alert '
                '"{msg}" as warning'.format(msg=msg)
            ),
        ]
        return args

    def get_auth_msg_dialog_args(self, auth_msg, auth_url):
        args = [
            'osascript',
            '-e',
            (
                'tell app "SystemUIServer" to display dialog '
                '"{msg}" default answer "{link}" '
                'with icon 1'.format(msg=auth_msg, link=auth_url)
            ),
        ]
        return args

    def get_enter_pin_dialog_args(self, token_msg):
        args = [
            'osascript',
            '-e',
            (
                'tell app "SystemUIServer" to display dialog '
                '"{msg}" default answer "" with icon 1'.format(msg=token_msg)
            ),
            '-e',
            'text returned of result',
        ]
        return args

    def get_ask_image_path_dialog_args(self):
        args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to POSIX path of '
                '(choose file with prompt "Choose Image:")'
            ),
        ]
        return args

    def get_ask_album_id_dialog_args(self, albums, no_album_msg):
        pass

    def ask_album_id(self, albums):
        i = 1
        data_map = []
        list_str = ''
        for album in albums:
            list_str = (
                list_str +
                '"{i} {album[title]}({album[privacy]})",'.format(
                    i=i, album=album
                )
            )
            data_map.append(album)
            i += 1
        args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to choose from list {{{l}}} '
                'with title "Choose From The List" with prompt "PickOne" '
                'OK button name "Select" cancel button name "Quit"'.format(
                    l=list_str[:-1]
                )
            ),
        ]
        choose_album_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        album_number = choose_album_dialog.communicate()[0].strip()
        album_number_end = album_number.find(' ')
        if album_number_end == -1:
            self.show_error_and_exit(
                'Return string format error: {{s}}'.format(s=album_number)
            )
        album_number = album_number[:album_number_end]
        album_number = int(album_number)
        return self._get_album_id(data_map, album_number)

    def get_show_link_dialog_args(self, links):
        pass

    def show_link(self, image_link, delete_hash):
        link = image_link.replace('\\', '')
        args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to display dialog "Image Link" '
                'default answer "{link}" '
                'buttons {{"Show delete link", "OK"}} '
                'default button 2'.format(link=link)
            ),
        ]
        show_link_dialog = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        response = show_link_dialog.communicate()[0].strip()
        response = response[response.find(':') + 1:response.find(',')]
        if response == 'Show delete link':
            delete_link = 'http://imgur.com/delete/{delete}'.format(
                delete=delete_hash
            )
            args2 = [
                'osascript',
                '-e',
                (
                    'tell app "Finder" to display dialog "Delete link" '
                    'default answer "{link}"'.format(link=delete_link)
                ),
            ]
            show_delete_link_dialog = subprocess.Popen(
                args2,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            show_delete_link_dialog.communicate()


class ZenityImgur(Imgur):

    def get_error_dialog_args(self, msg='Error'):
        args = [
            'zenity',
            '--error',
            '--text={text}'.format(text=msg),
        ]
        return args

    def get_auth_msg_dialog_args(self, auth_msg, auth_url):
        args = [
            'zenity',
            '--entry',
            '--text={msg}'.format(msg=auth_msg),
            '--entry-text={link}'.format(link=auth_url),
        ]
        return args

    def get_enter_pin_dialog_args(self, token_msg):
        args = [
            'zenity',
            '--entry',
            '--text={msg}'.format(msg=token_msg),
        ]
        return args

    def get_ask_image_path_dialog_args(self):
        args = [
            'zenity',
            '--file-selection',
        ]
        return args

    def get_ask_album_id_dialog_args(self, albums, no_album_msg):
        i = 1
        args = [
            'zenity',
            '--list',
            '--text="Choose the album"',
            '--column=No.',
            '--column=Album name',
            '--column=Privacy',
        ]
        for album in albums:
            args.append(str(i))
            args.append('{album[title]}'.format(album=album))
            args.append('{album[privacy]}'.format(album=album))
            i += 1
        args.append(str(i))
        args.append(no_album_msg)
        args.append('public')
        return args

    def get_show_link_dialog_args(self, links):
        args = [
            'zenity',
            '--info',
            '--text={links}'.format(links=links),
        ]
        return args


def main():
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        nargs='*',
        default=[None],
        help='The images you want to upload',
        metavar='<image path>'
    )
    parser.add_argument(
        '-d',
        nargs='?',
        default=None,
        help='The album id you want your image to be uploaded to',
        metavar='<album id>'
    )
    parser.add_argument(
        '-q',
        action='store_true',
        help='Choose album with each file'
    )
    parser.add_argument(
        '-g',
        action='store_true',
        help='GUI mode'
    )
    parser.add_argument(
        '-n',
        action='store_true',
        help='Anonymous upload'
    )
    parser.add_argument(
        '-s',
        action='store_true',
        help='Add command in the context menu of file manager'
        '(Support KDE and Gnome)'
    )
    parser.add_argument(
        '-t',
        action='store_true',
        help='Use image name as the title'
    )
    args = parser.parse_args()

    if args.s:
        shutil.copy2(os.path.dirname(__file__) + '/data/imgurup.desktop',
                     os.path.expanduser('~/.local/share/applications/'))
        return

    imgur = ImgurFactory.get_instance(args.g)
    imgur.connect()
    meta = {
        'album_id': args.d,
        'ask': args.q,
        'anonymous': args.n,
        'image_name_as_title': args.t,
    }
    for f in args.f:
        imgur.upload(f, meta)


if __name__ == '__main__':
    main()
