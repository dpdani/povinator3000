#!/usr/bin/env python3

import flask
import json
import pov3000com
import os


in_povinator = 'povinator3000.py' in os.listdir(os.getcwd())

app = flask.Flask(
    __name__,
    template_folder='web_ui/templates' if in_povinator else 'templates',
    static_folder='web_ui/static' if in_povinator else 'static'
)


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('index.html')


@app.route('/sheets', methods=['GET'])
def sheets():
    url = flask.request.args.get('url', '')
    download = flask.request.args.get('download', False)
    zip = flask.request.args.get('zip', False)
    if not url:
        return flask.render_template(
            'error.html',
            error_code=400,
            error_message="Please supply a URL."
        ), 400
    return flask.render_template(
        'responses_sheets.html',
        sheets=pov3000com.get_sheets(url)
    )


@app.route('/go', methods=['GET'])
def go():
    download = flask.request.args.get('download', False)
    zip = flask.request.args.get('zip', False)
    url = flask.request.args.get('url', '')
    sheets = flask.request.args.get('sheets', [])
    if type(sheets) == str:
        sheets = sheets.replace("'", '"')
        sheets = json.loads(sheets)
    if not download:
        zip = False
    povinator, success = pov3000com.go(
        url, sheets, download, zip
    )
    return flask.render_template(
        'go_done.html',
        output=pov3000com.log[povinator],
    )


@app.route('/dummy', methods=['GET'])
def dummy():
    return flask.render_template('responses_sheets.html',
                                 sheets=['a', 'b'])


if __name__ == '__main__':
    app.run(host='localhost', port=3000)

