import unittest
import mock
import httpretty


class TestImgurFactory(unittest.TestCase):

    def setUp(self):
        from imgurup import ImgurFactory
        self.ImgurFactory = ImgurFactory
        self.imgurFactory = ImgurFactory()

    def test_init(self):
        self.failUnless(self.imgurFactory is not None)

    def test_get_imgur(self):
        from imgurup import CLIImgur
        imgur_class = CLIImgur
        self.assertEqual(
            CLIImgur,
            type(self.ImgurFactory.get_imgur(imgur_class))
        )
        from imgurup import MacImgur
        imgur_class = MacImgur
        self.assertEqual(
            MacImgur,
            type(self.ImgurFactory.get_imgur(imgur_class))
        )
        from imgurup import KDEImgur
        imgur_class = KDEImgur
        self.assertEqual(
            KDEImgur,
            type(self.ImgurFactory.get_imgur(imgur_class))
        )

    def test_detect_env(self):
        is_gui = True
        from imgurup import KDEImgur
        from imgurup import CLIImgur
        from imgurup import ZenityImgur
        with mock.patch.dict('imgurup.os.environ', {'KDE_FULL_SESSION': 'true'}):
            self.assertEqual(
                self.ImgurFactory.detect_env(is_gui),
                KDEImgur
            )
        with mock.patch.dict('imgurup.os.environ', {'KDE_FULL_SESSION': 'false'}):
            with mock.patch('imgurup.sys') as sys:
                from imgurup import MacImgur
                type(sys).platform = mock.PropertyMock(return_value='darwin')
                self.assertEqual(
                    self.ImgurFactory.detect_env(is_gui),
                    MacImgur
                )
                type(sys).platform = mock.PropertyMock(return_value='')
                self.assertEqual(
                    self.ImgurFactory.detect_env(is_gui),
                    CLIImgur
                )
                with mock.patch.dict('imgurup.os.environ', {'DESKTOP_SESSION': 'gnome'}):
                    self.assertEqual(
                        self.ImgurFactory.detect_env(is_gui),
                        ZenityImgur
                    )

                is_gui = False
                self.assertEqual(
                    self.ImgurFactory.detect_env(is_gui),
                    CLIImgur
                )


class TestCLIImgur(unittest.TestCase):

    def setUp(self):
        from imgurup import CLIImgur
        self.imgur = CLIImgur()
        self._token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._token_config = (
            '[Token]\n'
            'access_token = 0d44238a038afb846d0fb6ce017b1eef001016cb\n'
            'refresh_token = 6dd8382a53a1f56cafe36d5fd51e16c2e13bbb0c\n'
        )
        self._token_response = (
            '{"access_token":"3590141a38a3b34d27c9933ba96d914bc42c7ecc",'
            '"expires_in":3600,'
            '"token_type":"bearer",'
            '"scope":null,'
            '"refresh_token":"fbbc33fb77cfbfa3aa4bf9bf14907d6d76f0e055",'
            '"account_username":"carlcarl"}'
        )
        self._token_json_response = {
            u'access_token': u'3590141a38a3b34d27c9933ba96d914bc42c7ecc',
            u'expires_in': 3600,
            u'token_type': u'bearer',
            u'account_username': u'carlcarl',
            u'scope': None,
            u'refresh_token': u'fbbc33fb77cfbfa3aa4bf9bf14907d6d76f0e055'
        }

    def test_show_error_and_exit(self):
        with mock.patch('imgurup.subprocess') as subprocess:
            subprocess.Popen.return_value.returncode = 0
            self.assertRaises(SystemExit, self.imgur.show_error_and_exit, 1)

    def test_set_tokens_using_config(self):
        import io
        with mock.patch('__builtin__.open', return_value=io.BytesIO(self._token_config)):
            self.imgur.set_tokens_using_config()
            self.assertEqual(
                self.imgur._access_token,
                '0d44238a038afb846d0fb6ce017b1eef001016cb'
            )
            self.assertEqual(
                self.imgur._refresh_token,
                '6dd8382a53a1f56cafe36d5fd51e16c2e13bbb0c'
            )

    @httpretty.activate
    def test_request_new_token(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://api.imgur.com/oauth2/token",
            body=self._token_response,
            status=200
        )
        json_response = self.imgur.request_new_tokens()
        self.assertDictEqual(json_response, self._token_json_response)

    @httpretty.activate
    def test_request_new_tokens_and_update(self):
        httpretty.register_uri(
            httpretty.POST,
            "https://api.imgur.com/oauth2/token",
            body=self._token_response,
            status=200
        )
        import io
        with mock.patch('__builtin__.open', return_value=io.BytesIO(self._token_config)):
            self.imgur.request_new_tokens_and_update()
            self.assertEqual(
                self.imgur._access_token,
                '3590141a38a3b34d27c9933ba96d914bc42c7ecc'
            )
            self.assertEqual(
                self.imgur._refresh_token,
                'fbbc33fb77cfbfa3aa4bf9bf14907d6d76f0e055'
            )

    def test_is_success(self):
        response = {}
        response['success'] = True
        response['data'] = {}
        response['data']['error'] = 'error'
        self.assertEqual(self.imgur.is_success(response), True)

        response['success'] = False
        self.assertEqual(self.imgur.is_success(response), False)

    def test_write_tokens_to_config(self):
        from mock import mock_open
        from mock import call
        self.imgur._access_token = '0d44238a038afb846d0fb6ce017b1eef001016cb'
        self.imgur._refresh_token = '6dd8382a53a1f56cafe36d5fd51e16c2e13bbb0c'
        with mock.patch('imgurup.ConfigParser.SafeConfigParser.read'):
            m = mock_open()
            with mock.patch('__builtin__.open', m, create=True):
                self.imgur.write_tokens_to_config()
                m.assert_called_once_with(self.imgur.CONFIG_PATH, 'wb')
                handle = m()
                handle.write.assert_has_calls(
                    [
                        call('[Token]\n'),
                        call('access_token = 0d44238a038afb846d0fb6ce017b1eef001016cb\n'),
                        call('refresh_token = 6dd8382a53a1f56cafe36d5fd51e16c2e13bbb0c\n'),
                    ]
                )

    def test_get_error_dialog_args(self):
        self.failUnless(self.imgur.get_error_dialog_args() is None)

    def test_ask_pin(self):
        pin = '000000'
        with mock.patch('__builtin__.raw_input', return_value=pin):
            self.assertEqual(self.imgur.ask_pin(self._auth_msg, self._auth_url, self._token_msg), pin)

    def test_ask_image_path(self):
        path = '/home/test/test.jpg'
        with mock.patch('__builtin__.raw_input', return_value=path):
            self.assertEqual(self.imgur.ask_image_path(), path)


class TestZenityImgur(unittest.TestCase):

    def setUp(self):
        from imgurup import ZenityImgur
        self.imgur = ZenityImgur()
        self._token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg

    def test_get_error_dialog_args(self):
        result = self.imgur.get_error_dialog_args()
        args = [
            'zenity',
            '--error',
            '--text=Error',
        ]
        self.assertListEqual(result, args)

    def test_get_auth_msg_dialog_args(self):
        result = self.imgur.get_auth_msg_dialog_args(self._auth_msg, self._auth_url)
        args = [
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
        self.assertListEqual(result, args)

    def test_get_enter_pin_dialog_args(self):
        result = self.imgur.get_enter_pin_dialog_args(self._token_msg)
        args = [
            'zenity',
            '--entry',
            '--text=Enter PIN code displayed in the browser: ',
        ]
        self.assertListEqual(result, args)

    def test_get_ask_image_path_dialog_args(self):
        result = self.imgur.get_ask_image_path_dialog_args()
        args = [
            'zenity',
            '--file-selection',
        ]
        self.assertListEqual(result, args)

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
        self.assertListEqual(result, args)

    def test_get_show_link_dialog_args(self):
        links = (
            'http://imgur.com/aaaaa\n'
            'Delete link: http://imgur.com/delete/bbbbb'
        )
        result = self.imgur.get_show_link_dialog_args(links)
        args = [
            'zenity',
            '--info',
            (
                '--text=http://imgur.com/aaaaa\n'
                'Delete link: http://imgur.com/delete/bbbbb'
            )
        ]
        self.assertListEqual(result, args)


class TestKDEImgur(unittest.TestCase):

    def setUp(self):
        from imgurup import KDEImgur
        self.imgur = KDEImgur()
        self._token_msg = self.imgur._enter_token_msg
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
        self.assertListEqual(result, args)

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
        self.assertListEqual(result, args)

    def test_get_enter_pin_dialog_args(self):
        result = self.imgur.get_enter_pin_dialog_args(self._token_msg)
        args = [
            'kdialog',
            '--title',
            'Input dialog',
            '--inputbox',
            'Enter PIN code displayed in the browser: ',
        ]
        self.assertListEqual(result, args)

    def test_get_ask_image_path_dialog_args(self):
        result = self.imgur.get_ask_image_path_dialog_args()
        args = [
            'kdialog',
            '--getopenfilename',
            '.',
        ]
        self.assertListEqual(result, args)

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
        self.assertListEqual(result, args)

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
        self.assertListEqual(result, args)


class TestMacImgur(unittest.TestCase):

    def setUp(self):
        from imgurup import MacImgur
        self.imgur = MacImgur()
        self._token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg

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
        self.assertListEqual(result, args)

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
        self.assertListEqual(result, args)

    def test_get_enter_pin_dialog_args(self):
        result = self.imgur.get_enter_pin_dialog_args(self._token_msg)
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
        self.assertListEqual(result, args)

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
        self.assertListEqual(result, args)

    def test_get_ask_album_id_dialog_args(self):
        albums = []
        no_album_msg = self._no_album_msg
        self.failUnless(
            self.imgur.get_ask_album_id_dialog_args(albums, no_album_msg) is None
        )

    def test_get_show_link_dialog_args(self):
        links = (
            'http://imgur.com/aaaaa\n'
            'Delete link: http://imgur.com/delete/bbbbb'
        )
        self.failUnless(
            self.imgur.get_show_link_dialog_args(links) is None
        )
