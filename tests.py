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

    def test_set_tokens_using_config(self):
        import io
        with mock.patch('__builtin__.open', return_value=io.BytesIO(self._token_config)):
            self.imgur.set_tokens_using_config()
            self.assertEqual(
                self.imgur._access_token,
                '0000000000000000000000000000000000000000'
            )
            self.assertEqual(
                self.imgur._refresh_token,
                '1111111111111111111111111111111111111111'
            )

    @httpretty.activate
    def test_request_album_list(self):
        import io
        httpretty.register_uri(
            httpretty.GET,
            "https://api.imgur.com/3/account/me/albums",
            body=self._album_response,
            status=200
        )
        with mock.patch('__builtin__.open', return_value=io.BytesIO(self._token_config)):
            json_response = self.imgur.request_album_list()
            self.assertEqual(len(json_response), 1)

        httpretty.register_uri(
            httpretty.GET,
            "https://api.imgur.com/3/account/carlcarl/albums",
            body=self._album_response,
            status=200
        )
        with mock.patch('__builtin__.open', return_value=io.BytesIO(self._token_config)):
            json_response = self.imgur.request_album_list(account='carlcarl')
            self.assertEqual(len(json_response), 1)

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
        # Fail case which without token values in config
        with mock.patch('__builtin__.open', return_value=io.BytesIO('')):
            self.assertRaises(SystemExit, self.imgur.request_new_tokens_and_update)

        # Success case
        with mock.patch('__builtin__.open', return_value=io.BytesIO(self._token_config)):
            self.imgur.request_new_tokens_and_update()
            self.assertEqual(
                self.imgur._access_token,
                '2222222222222222222222222222222222222222'
            )
            self.assertEqual(
                self.imgur._refresh_token,
                '3333333333333333333333333333333333333333'
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
        self.imgur._access_token = '0000000000000000000000000000000000000000'
        self.imgur._refresh_token = '1111111111111111111111111111111111111111'
        with mock.patch('imgurup.ConfigParser.SafeConfigParser.read'):
            m = mock_open()
            with mock.patch('__builtin__.open', m, create=True):
                self.imgur.write_tokens_to_config()
                m.assert_called_once_with(self.imgur.CONFIG_PATH, 'wb')
                handle = m()
                handle.write.assert_has_calls(
                    [
                        call('[Token]\n'),
                        call('access_token = 0000000000000000000000000000000000000000\n'),
                        call('refresh_token = 1111111111111111111111111111111111111111\n'),
                    ]
                )

    def test_get_error_dialog_args(self):
        self.failUnless(self.imgur.get_error_dialog_args() is None)

    def test_get_auth_msg_dialog_args(self):
        self.assertRaises(
            NotImplementedError,
            self.imgur.get_auth_msg_dialog_args,
            self._auth_msg,
            self._auth_url
        )

    def test_get_enter_pin_dialog_args(self):
        self.assertRaises(
            NotImplementedError,
            self.imgur.get_enter_pin_dialog_args,
            self._token_msg
        )

    def test_ask_pin(self):
        pin = '000000'
        with mock.patch('__builtin__.raw_input', return_value=pin):
            self.assertEqual(self.imgur.ask_pin(self._auth_msg, self._auth_url, self._token_msg), pin)

    def test_get_ask_image_path_dialog_args(self):
        self.assertRaises(
            NotImplementedError,
            self.imgur.get_ask_image_path_dialog_args
        )

    def test_ask_image_path(self):
        path = '/home/test/test.jpg'
        with mock.patch('__builtin__.raw_input', return_value=path):
            self.assertEqual(self.imgur.ask_image_path(), path)

    def test_get_show_link_dialog_args(self):
        self.assertRaises(
            NotImplementedError,
            self.imgur.get_show_link_dialog_args,
            {}
        )

    def test_show_link(self):
        image_link = 'http://i.imgur.com/xxxxxxx.jpg'
        delete_hash = 'xxxxxxxxxxxxxxx'
        from mock import call
        with mock.patch('__builtin__.print') as p:
            self.imgur.show_link(image_link, delete_hash)
            p.assert_has_calls(
                [
                    call('Link: http://i.imgur.com/xxxxxxx.jpg'),
                    call('Delete link: http://imgur.com/delete/xxxxxxxxxxxxxxx')
                ]
            )

    @httpretty.activate
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
        self.assertEqual(len(json_response), 1)

    @httpretty.activate
    def test_request_upload_image_fail(self):
        httpretty.register_uri(
            httpretty.POST,
            'https://api.imgur.com/3/image',
            body=self._album_fail_response,
            status=200
        )
        with mock.patch(
            'imgurup.CLIImgur.request_new_tokens_and_update',
            return_value=None
        ):
            with mock.patch(
                'imgurup.CLIImgur.write_tokens_to_config',
                return_value=None
            ):
                self.assertRaises(
                    SystemExit,
                    self.imgur.request_upload_image,
                    'https://api.imgur.com/3/image',
                    body='',
                    headers={}
                )


class TestZenityImgur(unittest.TestCase):

    def setUp(self):
        from imgurup import ZenityImgur
        self.imgur = ZenityImgur()
        self._token_msg = self.imgur._enter_token_msg
        self._auth_url = self.imgur._auth_url
        self._auth_msg = self.imgur._auth_msg
        self._no_album_msg = self.imgur._no_album_msg

    def test_show_error_and_exit(self):
        with mock.patch('imgurup.subprocess') as subprocess:
            subprocess.Popen.return_value.returncode = 0
            self.assertRaises(SystemExit, self.imgur.show_error_and_exit, 1)

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

    def test_ask_image_path(self):
        with mock.patch('imgurup.subprocess') as subprocess:
            def communicate_data():
                return ['/tmp/test.jpg']

            def communicate_empty():
                return ['']
            # Fail case
            subprocess.Popen.return_value.communicate = communicate_empty
            self.assertRaises(SystemExit, self.imgur.ask_image_path)
            # Success case
            subprocess.Popen.return_value.communicate = communicate_data
            image_path = self.imgur.ask_image_path()
            self.assertEqual(image_path, '/tmp/test.jpg')

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
        self.assertListEqual(result, args)

    def test_show_link(self):
        image_link = 'http://i.imgur.com/xxxxxxx.jpg'
        delete_hash = 'xxxxxxxxxxxxxxx'
        from mock import call
        with mock.patch('imgurup.subprocess') as subprocess:
            self.imgur.show_link(image_link, delete_hash)
            subprocess.Popen.assert_has_calls(
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
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                ]
            )


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
