from __future__ import unicode_literals

import pytest

import mock
from mock import call
from mock import patch
import httpretty
import pytest_httpretty

import io
import sys

import imgurup
from imgurup import CLIImgur
from imgurup import MacImgur
from imgurup import KDEImgur
from imgurup import ZenityImgur


def get_builtin_name(builtin_name):
    name = ('builtins.%s' if sys.version_info >= (3,) else '__builtin__.%s') % builtin_name
    return name


class TestImgurFactory:

    def setup(self):
        from imgurup import ImgurFactory
        self.ImgurFactory = ImgurFactory
        self.imgurFactory = ImgurFactory()

    def test_init(self):
        assert self.ImgurFactory

    @pytest.fixture(scope='function')
    def mock_sys(self, request):
        m = mock.patch('imgurup.sys')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_get_instance_cli(self, monkeypatch):
        monkeypatch.delenv('KDE_FULL_SESSION', raising=False)
        monkeypatch.delenv('DESKTOP_SESSION', raising=False)
        monkeypatch.setattr(imgurup.sys, 'platform', None)
        prefer_gui = True
        assert type(self.ImgurFactory.get_instance(prefer_gui)) == CLIImgur
        prefer_gui = False
        assert type(self.ImgurFactory.get_instance(prefer_gui)) == CLIImgur

    def test_get_instance_kde(self, monkeypatch):
        monkeypatch.setenv('KDE_FULL_SESSION', 'true')
        monkeypatch.setenv('DESKTOP_SESSION', '')
        monkeypatch.setattr(imgurup.sys, 'platform', 'linux2')
        prefer_gui = True
        assert type(self.ImgurFactory.get_instance(prefer_gui)) == KDEImgur

    def test_get_instance_mac(self, monkeypatch):
        monkeypatch.delenv('KDE_FULL_SESSION', raising=False)
        monkeypatch.delenv('DESKTOP_SESSION', raising=False)
        monkeypatch.setattr(imgurup.sys, 'platform', 'darwin')
        prefer_gui = True
        assert type(self.ImgurFactory.get_instance(prefer_gui) == MacImgur)

    def test_get_instance_gnome(self, monkeypatch):
        monkeypatch.delenv('KDE_FULL_SESSION', raising=False)
        monkeypatch.setenv('DESKTOP_SESSION', 'gnome')
        monkeypatch.setattr(imgurup.sys, 'platform', 'linux2')
        prefer_gui = True
        assert type(self.ImgurFactory.get_instance(prefer_gui)) == ZenityImgur

    def test_get_instance_pantheon(self, monkeypatch):
        monkeypatch.delenv('KDE_FULL_SESSION', raising=False)
        monkeypatch.setenv('DESKTOP_SESSION', 'pantheon')
        monkeypatch.setattr(imgurup.sys, 'platform', 'linux2')
        prefer_gui = True
        assert type(self.ImgurFactory.get_instance(prefer_gui)) == ZenityImgur


class TestCLIImgur:

    def setup(self):
        self.imgur = CLIImgur()
        self.imgur.connect()
        self._enter_token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg
        self._token_config = (
            '[Token]\n'
            'access_token = 0000000000000000000000000000000000000000\n'
            'refresh_token = 1111111111111111111111111111111111111111\n'
        )
        self._token_response = (
            '{"access_token":"2222222222222222222222222222222222222222",'
            '"expires_in":3600,'
            '"token_type":"bearer",'
            '"scope":null,'
            '"refresh_token":"3333333333333333333333333333333333333333",'
            '"account_username":"carlcarl"}'
        )
        self._token_json_response = {
            u'access_token': u'2222222222222222222222222222222222222222',
            u'expires_in': 3600,
            u'token_type': u'bearer',
            u'account_username': u'carlcarl',
            u'scope': None,
            u'refresh_token': u'3333333333333333333333333333333333333333'
        }
        self._album_response = (
            '{"data":[{"id":"XXXXX",'
            '"title":"temp",'
            '"description":null,'
            '"datetime":1352238500,'
            '"cover":"Oin6z",'
            '"cover_width":1891,'
            '"cover_height":967,'
            '"account_url":"carlcarl",'
            '"privacy":"hidden",'
            '"layout":"grid",'
            '"views":2,'
            '"link":"http:\/\/imgur.com\/a\/XXXXX",'
            '"favorite":false,'
            '"nsfw":null,'
            '"section":null,'
            '"deletehash":"000000000000000",'
            '"order":0}],'
            '"success":true,'
            '"status":200}'
        )
        self._album_fail_response = (
            '{"data":{"error": "fail"},'
            '"success":false,'
            '"status":200}'
        )
        self._album_json_response = {
            u'status': 200,
            u'data': [
                {
                    u'deletehash': u'000000000000000',
                    u'layout': u'grid',
                    u'description': None,
                    u'title': u'temp',
                    u'cover_height': 967,
                    u'views': 2,
                    u'privacy': u'hidden',
                    u'cover': u'Oin6z',
                    u'datetime': 1352238500,
                    u'account_url': u'carlcarl',
                    u'favorite': False,
                    u'cover_width': 1891,
                    u'link': u'http://imgur.com/a/XXXXX',
                    u'section': None,
                    u'nsfw': None,
                    u'order': 0,
                    u'id': u'XXXXX'
                }
            ],
            u'success': True
        }
        self._albums = [
            {
                'id': '1',
                'title': 'hello',
                'privacy': 'public'
            },
            {
                'id': '2',
                'title': 'hello2',
                'privacy': 'private'
            }
        ]
        self._image_link = 'http://i.imgur.com/xxxxxxx.jpg'
        self._delete_hash = 'xxxxxxxxxxxxxxx'

    @pytest.fixture(scope='function')
    def mock_HTTPSConnection(self, request):
        m = mock.patch('imgurup.httplib.HTTPSConnection')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_connect(self, mock_HTTPSConnection):
        _imgur = CLIImgur()
        _imgur.connect()
        mock_HTTPSConnection.assert_has_calls(
            [
                call('api.imgur.com')
            ]
        )

    def test_set_tokens_using_config(self, monkeypatch):

        with patch(get_builtin_name('open'), return_value=io.StringIO(self._token_config)):
            self.imgur.set_tokens_using_config()
            assert self.imgur._access_token == '0000000000000000000000000000000000000000'
            assert self.imgur._refresh_token == '1111111111111111111111111111111111111111'

    def test_is_success(self):
        response = {}
        response['success'] = True
        response['data'] = {}
        response['data']['error'] = 'error'
        assert self.imgur.is_success(response) is True
        response['success'] = False
        assert self.imgur.is_success(response) is False

    def test_write_tokens_to_config(self):
        from mock import mock_open
        self.imgur._access_token = '0000000000000000000000000000000000000000'
        self.imgur._refresh_token = '1111111111111111111111111111111111111111'
        with patch('imgurup.SafeConfigParser.read'):
            m = mock_open()
            with patch(get_builtin_name('open'), m, create=True):
                self.imgur.write_tokens_to_config()
                m.assert_called_once_with(self.imgur.CONFIG_PATH, 'w')
                handle = m()
                handle.write.assert_has_calls(
                    [
                        call('[Token]\n'),
                        call('access_token = 0000000000000000000000000000000000000000\n'),
                        call('refresh_token = 1111111111111111111111111111111111111111\n'),
                    ]
                )

    def test_get_error_dialog_args(self):
        assert self.imgur.get_error_dialog_args() is None

    def test_get_auth_msg_dialog_args(self):
        with pytest.raises(NotImplementedError):
            self.imgur.get_auth_msg_dialog_args(self._auth_msg, self._auth_url)

    def test_get_enter_pin_dialog_args(self):
        with pytest.raises(NotImplementedError):
            self.imgur.get_enter_pin_dialog_args(self._enter_token_msg)

    @pytest.mark.httpretty
    def test_request_album_list_me_success(self, monkeypatch):
        httpretty.register_uri(
            httpretty.GET,
            "https://api.imgur.com/3/account/me/albums",
            body=self._album_response,
            status=200
        )
        with patch(get_builtin_name('open'), return_value=io.StringIO(self._token_config)):
            json_response = self.imgur.request_album_list()
            assert len(json_response) == 1

    @pytest.mark.httpretty
    def test_request_album_list_carlcarl_success(self, monkeypatch):
        httpretty.register_uri(
            httpretty.GET,
            "https://api.imgur.com/3/account/carlcarl/albums",
            body=self._album_response,
            status=200
        )
        with patch(get_builtin_name('open'), return_value=io.StringIO(self._token_config)):
            json_response = self.imgur.request_album_list(account='carlcarl')
            assert len(json_response) == 1

    @pytest.mark.httpretty
    def test_request_album_list_me_fail(self, monkeypatch):
        httpretty.register_uri(
            httpretty.GET,
            "https://api.imgur.com/3/account/me/albums",
            body=self._album_fail_response,
            status=200
        )
        m = mock.Mock(return_value=None)
        monkeypatch.setattr(
            imgurup.CLIImgur,
            'request_new_tokens_and_update',
            m
        )
        monkeypatch.setattr(
            imgurup.CLIImgur,
            'write_tokens_to_config',
            m
        )
        monkeypatch.setattr(
            imgurup.time,
            'sleep',
            m
        )
        with pytest.raises(SystemExit):
            self.imgur.request_album_list()

    @pytest.mark.httpretty
    def test_request_new_token(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://api.imgur.com/oauth2/token",
            body=self._token_response,
            status=200
        )
        json_response = self.imgur.request_new_tokens()
        assert json_response == self._token_json_response

    @pytest.mark.httpretty
    def test_request_new_tokens_and_update(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://api.imgur.com/oauth2/token",
            body=self._token_response,
            status=200
        )
        # Fail case which without token values in config
        with patch(get_builtin_name('open'), return_value=io.StringIO('')):
            with pytest.raises(SystemExit):
                self.imgur.request_new_tokens_and_update()

        # Success case
        with patch(get_builtin_name('open'), return_value=io.StringIO(self._token_config)):
            self.imgur.request_new_tokens_and_update()
            assert self.imgur._access_token == '2222222222222222222222222222222222222222'
            assert self.imgur._refresh_token == '3333333333333333333333333333333333333333'

        self.imgur._refresh_token = '3333333333333333333333333333333333333333'
        with patch('imgurup.CLIImgur.request_new_tokens') as request_new_tokens:
            request_new_tokens.return_value = {
                'success': False,
                'data': {
                    'error': 'error'
                }
            }
            with pytest.raises(SystemExit):
                self.imgur.request_new_tokens_and_update()

    @pytest.fixture(scope='function')
    def mock_raw_input(self, request):
        m = mock.patch('imgurup.input')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_ask_pin(self, mock_raw_input):
        pin = '000000'
        mock_raw_input.return_value = pin
        assert self.imgur.ask_pin(
            self._auth_msg,
            self._auth_url,
            self._enter_token_msg) == pin

    @pytest.fixture(scope='function')
    def mock_ask_pin(self, request):
        m = mock.patch('imgurup.CLIImgur.ask_pin')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    @pytest.mark.httpretty
    def test_auth(self, mock_ask_pin):
        mock_ask_pin.return_value = '000000'
        httpretty.register_uri(
            httpretty.POST,
            'https://api.imgur.com/oauth2/token',
            body=(
                '{"success":false,'
                '"data":{"error":"error"} }'
            ),
            status=200
        )
        with pytest.raises(SystemExit):
            self.imgur.auth()

        httpretty.register_uri(
            httpretty.POST,
            'https://api.imgur.com/oauth2/token',
            body=(
                '{"success":true,'
                '"access_token":"1111111111111111111111111111111111111111",'
                '"refresh_token":"2222222222222222222222222222222222222222"}'
            ),
            status=200
        )
        self.imgur.auth()
        assert self.imgur._access_token == '1111111111111111111111111111111111111111'
        assert self.imgur._refresh_token == '2222222222222222222222222222222222222222'

    def test_get_ask_image_path_dialog_args(self):
        with pytest.raises(NotImplementedError):
            self.imgur.get_ask_image_path_dialog_args()

    def test_ask_image_path(self, mock_raw_input):
        path = '/home/test/test.jpg'
        mock_raw_input.return_value = path
        assert self.imgur.ask_image_path() == path

    def test_get_ask_album_id_dialog_args(self):
        with pytest.raises(NotImplementedError):
            self.imgur.get_ask_album_id_dialog_args(
                self._albums,
                self._no_album_msg
            )

    def test_ask_album_id(self):
        with patch('imgurup.input', return_value=1):
            assert self.imgur.ask_album_id(self._albums) == '1'

    def test_get_show_link_dialog_args(self):
        with pytest.raises(NotImplementedError):
            self.imgur.get_show_link_dialog_args({})

    @pytest.fixture(scope='function')
    def mock_print(self, request):
        m = mock.patch(get_builtin_name('print'))
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_show_link(self, mock_print):
        self.imgur.show_link(self._image_link, self._delete_hash)
        mock_print.assert_has_calls(
            [
                call('Link: http://i.imgur.com/xxxxxxx.jpg'),
                call('Delete link: http://imgur.com/delete/xxxxxxxxxxxxxxx')
            ]
        )

    @pytest.mark.httpretty
    def test_request_upload_image_success(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.imgur.com/3/image',
            body=self._album_response,
            status=200
        )
        json_response = self.imgur.request_upload_image(
            'https://api.imgur.com/3/image',
            body='',
            headers={}
        )
        assert len(json_response) == 1

    @pytest.mark.httpretty
    def test_request_upload_image_fail(self, monkeypatch):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.imgur.com/3/image',
            body=self._album_fail_response,
            status=200
        )
        m = mock.Mock(return_value=None)
        monkeypatch.setattr(
            imgurup.CLIImgur,
            'request_new_tokens_and_update',
            m
        )
        monkeypatch.setattr(
            imgurup.CLIImgur,
            'write_tokens_to_config',
            m
        )
        monkeypatch.setattr(
            imgurup.time,
            'sleep',
            m
        )
        with pytest.raises(SystemExit):
            self.imgur.request_upload_image(
                'https://api.imgur.com/3/image',
                body='',
                headers={}
            )


class TestZenityImgur:

    def setup(self):
        from imgurup import ZenityImgur
        self.imgur = ZenityImgur()
        self._enter_token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg
        self._albums = [
            {
                'id': '1',
                'title': 'hello',
                'privacy': 'public'
            },
            {
                'id': '2',
                'title': 'hello2',
                'privacy': 'private'
            }
        ]
        self._auth_msg_dialog_args = [
            'zenity',
            '--entry',
            (
                '--text=This is the first time you use this program, '
                'you have to visit this URL in your browser '
                'and copy the PIN code: \n'
            ),
            (
                '--entry-text=https://api.imgur.com/oauth2/authorize?'
                'client_id=55080e3fd8d0644&response_type=pin&state=carlcarl'
            )
        ]
        self._enter_pin_dialog_args = [
            'zenity',
            '--entry',
            '--text=Enter PIN code displayed in the browser: ',
        ]
        self._ask_album_id_dialog_args = [
            'zenity',
            '--list',
            '--text="Choose the album"',
            '--column=No.',
            '--column=Album name',
            '--column=Privacy',
            '1',
            'hello',
            'public',
            '2',
            'hello2',
            'private',
            '3',
            'Do not move to any album',
            'public'
        ]
        self._image_link = 'http://i.imgur.com/xxxxxxx.jpg'
        self._delete_hash = 'xxxxxxxxxxxxxxx'

    @pytest.fixture(scope='function')
    def mock_subprocess(self, request):
        m = mock.patch('imgurup.subprocess')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_show_error_and_exit(self, mock_subprocess):
        mock_subprocess.Popen.return_value.returncode = 0
        with pytest.raises(SystemExit):
            self.imgur.show_error_and_exit(1)

    def test_get_error_dialog_args(self):
        result = self.imgur.get_error_dialog_args()
        args = [
            'zenity',
            '--error',
            '--text=Error',
        ]
        assert result == args

    def test_get_auth_msg_dialog_args(self):
        result = self.imgur.get_auth_msg_dialog_args(self._auth_msg, self._auth_url)
        assert result == self._auth_msg_dialog_args

    def test_get_enter_pin_dialog_args(self):
        result = self.imgur.get_enter_pin_dialog_args(self._enter_token_msg)
        assert result == self._enter_pin_dialog_args


    @pytest.fixture(scope='function')
    def mock_get_auth_msg_dialog_args(self, request):
        m = mock.patch('imgurup.ZenityImgur.get_auth_msg_dialog_args')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_ask_pin(
            self,
            mock_get_auth_msg_dialog_args,
            mock_subprocess
    ):
        def _test_ask_pin(args, stdout, stderr):
            from mock import MagicMock
            m = MagicMock()
            if args == self._auth_msg_dialog_args:
                m.communicate = lambda: ['']
            elif args == self._enter_pin_dialog_args:
                m.communicate = lambda: ['XXXXXX']
            return m

        mock_get_auth_msg_dialog_args.return_value = self._auth_msg_dialog_args
        mock_subprocess.Popen.side_effect = _test_ask_pin
        pin = self.imgur.ask_pin(
            self._auth_msg,
            self._auth_url,
            self._enter_token_msg
        )
        assert pin == 'XXXXXX'
        mock_subprocess.Popen.assert_has_calls(
            [
                call(
                    self._auth_msg_dialog_args,
                    stdout=mock_subprocess.PIPE,
                    stderr=mock_subprocess.PIPE
                ),
                call(
                    self._enter_pin_dialog_args,
                    stdout=mock_subprocess.PIPE,
                    stderr=mock_subprocess.PIPE
                )
            ]
        )

    def test_get_ask_image_path_dialog_args(self):
        result = self.imgur.get_ask_image_path_dialog_args()
        args = [
            'zenity',
            '--file-selection',
        ]
        assert result == args

    def test_ask_image_path(self, mock_subprocess):
        # Fail case
        mock_subprocess.Popen.return_value.communicate = lambda: ['']
        with pytest.raises(SystemExit):
            self.imgur.ask_image_path()
        # Success case
        mock_subprocess.Popen.return_value.communicate = lambda: ['/tmp/test.jpg']
        image_path = self.imgur.ask_image_path()
        assert image_path == '/tmp/test.jpg'

    def test_get_ask_album_id_dialog_args(self):
        no_album_msg = self._no_album_msg
        result = self.imgur.get_ask_album_id_dialog_args(self._albums, no_album_msg)
        assert result == self._ask_album_id_dialog_args

    @pytest.fixture(scope='function')
    def mock_get_ask_album_id_dialog_args(self, request):
        m = mock.patch('imgurup.ZenityImgur.get_ask_album_id_dialog_args')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_ask_album_id(
            self,
            mock_get_ask_album_id_dialog_args,
            mock_subprocess
    ):
        mock_get_ask_album_id_dialog_args.return_value = self._ask_album_id_dialog_args
        mock_subprocess.Popen.return_value.communicate = lambda: ['1']
        result = self.imgur.ask_album_id(self._albums)
        assert result == '1'
        mock_subprocess.Popen.return_value.communicate = lambda: ['']
        with pytest.raises(SystemExit):
            self.imgur.ask_album_id(self._albums)

    def test_get_show_link_dialog_args(self):
        links = (
            'Link: http://i.imgur.com/xxxxxxx.jpg\n'
            'Delete link: http://imgur.com/delete/xxxxxxxxxxxxxxx'
        )
        result = self.imgur.get_show_link_dialog_args(links)
        args = [
            'zenity',
            '--info',
            (
                '--text=Link: http://i.imgur.com/xxxxxxx.jpg\n'
                'Delete link: http://imgur.com/delete/xxxxxxxxxxxxxxx'
            )
        ]
        assert result == args

    def test_show_link(self, mock_subprocess):
        self.imgur.show_link(self._image_link, self._delete_hash)
        mock_subprocess.Popen.assert_has_calls(
            [
                call(
                    [
                        'zenity',
                        '--info',
                        (
                            '--text=Link: http://i.imgur.com/xxxxxxx.jpg\n'
                            'Delete link: http://imgur.com/delete/xxxxxxxxxxxxxxx'
                        )
                    ],
                    stdout=mock_subprocess.PIPE,
                    stderr=mock_subprocess.PIPE
                )
            ]
        )


class TestKDEImgur:
    def setup(self):
        from imgurup import KDEImgur
        self.imgur = KDEImgur()
        self._enter_token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg

    def test_get_error_dialog_args(self):
        result = self.imgur.get_error_dialog_args()
        args = [
            'kdialog',
            '--error',
            'Error',
        ]
        assert result == args

    def test_get_auth_msg_dialog_args(self):
        result = self.imgur.get_auth_msg_dialog_args(self._auth_msg, self._auth_url)
        args = [
            'kdialog',
            '--msgbox',
            (
                'This is the first time you use this program, '
                'you have to visit this URL in your browser '
                'and copy the PIN code: \n'
                'https://api.imgur.com/oauth2/authorize?'
                'client_id=55080e3fd8d0644&response_type=pin&state=carlcarl'
            )
        ]
        assert result == args

    def test_get_enter_pin_dialog_args(self):
        result = self.imgur.get_enter_pin_dialog_args(self._enter_token_msg)
        args = [
            'kdialog',
            '--title',
            'Input dialog',
            '--inputbox',
            'Enter PIN code displayed in the browser: ',
        ]
        assert result == args

    def test_get_ask_image_path_dialog_args(self):
        result = self.imgur.get_ask_image_path_dialog_args()
        args = [
            'kdialog',
            '--getopenfilename',
            '.',
        ]
        assert result == args

    def test_get_ask_album_id_dialog_args(self):
        albums = []
        albums.append(
            {
                'title': 'hello',
                'privacy': 'public'
            }
        )
        albums.append(
            {
                'title': 'hello2',
                'privacy': 'private'
            }
        )
        no_album_msg = self._no_album_msg
        result = self.imgur.get_ask_album_id_dialog_args(albums, no_album_msg)
        args = [
            'kdialog',
            '--menu',
            '"Choose the album"',
            '1',
            'hello(public)',
            '2',
            'hello2(private)',
            '3',
            'Do not move to any album(public)',
        ]
        assert result == args

    def test_get_show_link_dialog_args(self):
        links = (
            'http://imgur.com/aaaaa\n'
            'Delete link: http://imgur.com/delete/bbbbb'
        )
        result = self.imgur.get_show_link_dialog_args(links)
        args = [
            'kdialog',
            '--msgbox',
            (
                'http://imgur.com/aaaaa\n'
                'Delete link: http://imgur.com/delete/bbbbb'
            )
        ]
        assert result == args


class TestMacImgur:

    def setup(self):
        from imgurup import MacImgur
        self.imgur = MacImgur()
        self._enter_token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg
        self._albums = [
            {
                'id': '1',
                'title': 'hello',
                'privacy': 'public'
            },
            {
                'id': '2',
                'title': 'hello2',
                'privacy': 'private'
            }
        ]
        self._image_link = 'http://i.imgur.com/xxxxxxx.jpg'
        self._delete_hash = 'xxxxxxxxxxxxxxx'

    def test_get_error_dialog_args(self):
        result = self.imgur.get_error_dialog_args()
        args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to display alert '
                '"Error" as warning'
            ),
        ]
        assert result == args

    def test_get_auth_msg_dialog_args(self):
        result = self.imgur.get_auth_msg_dialog_args(self._auth_msg, self._auth_url)
        args = [
            'osascript',
            '-e',
            (
                'tell app "SystemUIServer" to display dialog '
                '"This is the first time you use this program, '
                'you have to visit this URL in your browser '
                'and copy the PIN code: \n" '
                'default answer '
                '"https://api.imgur.com/oauth2/authorize?'
                'client_id=55080e3fd8d0644&response_type=pin&state=carlcarl" '
                'with icon 1'
            ),
        ]
        assert result == args

    def test_get_enter_pin_dialog_args(self):
        result = self.imgur.get_enter_pin_dialog_args(self._enter_token_msg)
        args = [
            'osascript',
            '-e',
            (
                'tell app "SystemUIServer" to display dialog '
                '"Enter PIN code displayed in the browser: " '
                'default answer "" with icon 1'
            ),
            '-e',
            'text returned of result',
        ]
        assert result == args

    def test_get_ask_image_path_dialog_args(self):
        result = self.imgur.get_ask_image_path_dialog_args()
        args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to POSIX path of '
                '(choose file with prompt "Choose Image:")'
            ),
        ]
        assert result == args

    def test_get_ask_album_id_dialog_args(self):
        albums = []
        no_album_msg = self._no_album_msg
        assert self.imgur.get_ask_album_id_dialog_args(albums, no_album_msg) is None

    @pytest.fixture(scope='function')
    def mock_subprocess(self, request):
        m = mock.patch('imgurup.subprocess')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_ask_album_id(self, mock_subprocess):
        mock_subprocess.Popen.return_value.communicate = lambda: ['1 Public(public)']
        assert self.imgur.ask_album_id(self._albums) == '1'
        mock_subprocess.Popen.return_value.communicate = lambda: ['1Public(public)']
        with pytest.raises(SystemExit):
            self.imgur.ask_album_id(self._albums)
        mock_subprocess.Popen.return_value.communicate = lambda: ['  Public(public)']
        with pytest.raises(SystemExit):
            self.imgur.ask_album_id(self._albums)

    def test_get_show_link_dialog_args(self):
        links = (
            'http://imgur.com/aaaaa\n'
            'Delete link: http://imgur.com/delete/bbbbb'
        )
        assert self.imgur.get_show_link_dialog_args(links) is None

    def test_show_link(self, mock_subprocess):
        show_link_args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to display dialog "Image Link" '
                'default answer "{link}" '
                'buttons {{"Show delete link", "OK"}} '
                'default button 2'.format(link=self._image_link)
            ),
        ]
        delete_link = 'http://imgur.com/delete/{delete}'.format(delete=self._delete_hash)
        delete_link_args = [
            'osascript',
            '-e',
            (
                'tell app "Finder" to display dialog "Delete link" '
                'default answer "{link}"'.format(link=delete_link)
            ),
        ]

        def _test_show_link(args, stdout, stderr):
            from mock import MagicMock
            m = MagicMock()
            if args == show_link_args:
                m.communicate = lambda: [
                    (
                        'button returned:Show delete link, '
                        'text returned:http://i.imgur.com/xxxxxxx.jpg'
                    )
                ]
            elif args == delete_link_args:
                m.communicate = lambda: ['']
            return m

        mock_subprocess.Popen.side_effect = _test_show_link
        self.imgur.show_link(self._image_link, self._delete_hash)
        mock_subprocess.Popen.assert_has_calls(
            [
                call(
                    show_link_args,
                    stdout=mock_subprocess.PIPE,
                    stderr=mock_subprocess.PIPE
                ),
                call(
                    delete_link_args,
                    stdout=mock_subprocess.PIPE,
                    stderr=mock_subprocess.PIPE
                )
            ]
        )

    @pytest.fixture(scope='function')
    def mock_copy2(self, request):
        m = mock.patch('imgurup.shutil.copy2')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    @pytest.fixture(scope='function')
    def mock_argparse(self, request):
        m = mock.patch('imgurup.argparse')
        ret = m.start()
        request.addfinalizer(m.stop)
        return ret

    def test_main(self, mock_argparse, mock_copy2):
        from argparse import Namespace
        n = Namespace()
        n.s = True
        mock_argparse.ArgumentParser.return_value.parse_args = lambda: n
        from imgurup import main
        main()
