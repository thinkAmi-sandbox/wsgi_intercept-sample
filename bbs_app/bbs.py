# -*- coding: utf-8 -*-
import datetime
import pickle
from pathlib import Path
import bottle
from bottle import Bottle, run, redirect, request, response, jinja2_template


class Message(object):
    def __init__(self, title, handle, message):
        self.title = title
        self.handle = handle
        self.message = message
        self.created_at = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

# テストコードで扱えるよう、変数appにインスタンスをセット
app = Bottle()

@app.get('/')
def get_form():
    handle = request.cookies.getunicode('handle', default='')
    messages = read_messages()
    return jinja2_template('bbs.html', handle=handle, messages=messages)

@app.post('/foo')
def post_foo():
    return "Hello World!"


@app.post('/')
def post_form():
    response.set_cookie('handle', request.forms.get('handle'))

    message = Message(
        title=request.forms.getunicode('title'),
        handle=request.forms.getunicode('handle'),
        message=request.forms.getunicode('message'),
    )
    messages = read_messages()
    messages.append(message)
    with open('bbs.pickle', mode='wb') as f:
        pickle.dump(messages, f)

    redirect('/')


@app.get('/delete_cookie')
def delete_cookie():
    response.delete_cookie('handle')
    redirect('/')


def read_messages():
    if Path('bbs.pickle').exists():
        with open('bbs.pickle', mode='rb') as f:
            return pickle.load(f)
    return []


if __name__ == "__main__":
    run(app, host="localhost", port=8080, debug=True, reloader=True)