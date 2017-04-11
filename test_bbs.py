import os
import requests
import wsgi_intercept
from wsgi_intercept import requests_intercept, add_wsgi_intercept
from wsgi_intercept.interceptor import RequestsInterceptor
import bottle
from bbs_app.bbs import app


class TestRequest(object):
    @classmethod
    def setup_class(cls):
        # wsgi-interceptでBottleをテストする場合、デフォルトではテンプレートディレクトリを認識しない
        # そのため、以下に従い、mod_wsgiと同じくディレクトリを指定すること
        # http://bottlepy.org/docs/dev/faq.html#template-not-found-in-mod-wsgi-mod-python
        current_dir = os.path.abspath(os.path.dirname(__file__))
        template_dir = os.path.join(current_dir, 'bbs_app/views')
        bottle.TEMPLATE_PATH.insert(0, template_dir)

    def teardown_method(self):
        """テストごとにpickleファイルができるため、お互いに影響を与えないよう削除する"""
        if os.path.exists('bbs.pickle'):
            os.remove('bbs.pickle')


    def get_app(self):
        # wsgi_interceptがimportしたappでは動作しないので、appを返すメソッドを作った
        return app


    def test_get(self):
        """GETのテスト"""
        with RequestsInterceptor(self.get_app, host='localhost', port=8080) as url:
            actual = requests.get(url)

        assert actual.status_code == 200
        assert actual.headers['content-type'] == 'text/html; charset=UTF-8'
        assert 'テスト掲示板' in actual.text


    def test_post_using_add_wsgi_intercept(self):
        """POSTのテスト(add_wsgi_intercept利用版)"""
        host = 'localhost'
        port = 8081
        url = f'http://{host}:{port}'

        requests_intercept.install()
        add_wsgi_intercept(host, port, self.get_app)

        form = {
            'title': 'タイトル1',
            'handle': 'ハンドル名1',
            'message': 'メッセージ1',
        }
        actual = requests.post(url, data=form)

        assert actual.status_code == 200
        assert actual.headers['content-type'] == 'text/html; charset=UTF-8'
        assert 'タイトル1' in actual.text
        assert 'ハンドル名1' in actual.text
        assert 'メッセージ1' in actual.text

        requests_intercept.uninstall()


    def test_post_using_RequestsInterceptor(self):
        """POSTのテスト(RequestsInterceptor利用版)
        POSTとリダイレクトを検証する
        """
        form = {
            'title': 'タイトル2',
            'handle': 'ハンドル名2',
            'message': 'メッセージ2',
        }
        with RequestsInterceptor(self.get_app, host='localhost', port=8082) as url:
            # リダイレクト付
            actual = requests.post(url, data=form)

        # リダイレクト先の検証
        assert actual.status_code == 200
        assert actual.headers['content-type'] == 'text/html; charset=UTF-8'
        assert 'タイトル2' in actual.text
        assert 'ハンドル名2' in actual.text
        assert 'メッセージ2' in actual.text

        # リダイレクト元の検証
        assert len(actual.history) == 1
        history = actual.history[0]
        assert history.status_code == 302
        assert history.headers['content-type'] == 'text/html; charset=UTF-8'
        # bottleでredirect()を使った場合、bodyは''になる
        assert history.text == ''


    def test_redirect_using_RequestsInterceptor(self):
        """POSTでリダイレクト元のみをテスト(RequestsInterceptor利用版)
        requestsでリダイレクトしないように設定してテスト
        """
        form = {
            'title': 'タイトル3',
            'handle': 'ハンドル名3',
            'message': 'メッセージ3',
        }
        with RequestsInterceptor(self.get_app, host='localhost', port=8082) as url:
            # リダイレクトさせない
            actual = requests.post(url, data=form, allow_redirects=False)

        assert len(actual.history) == 0
        assert actual.status_code == 302
        assert actual.headers['content-type'] == 'text/html; charset=UTF-8'
        # bottleでredirect()を使った場合、bodyは''になる
        assert actual.text == ''
