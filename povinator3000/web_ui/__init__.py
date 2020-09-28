#!/usr/bin/env python3

import flask
import json
from .. import core
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


@app.route('/presentations', methods=['GET'])
def presentations():
    return flask.render_template(
        'presentations.html'
    )


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
    sheets = core.get_sheets(url)
    if sheets:
        return flask.render_template(
            'responses_sheets.html',
            sheets=sheets
        )
    else:
        return flask.render_template(
            'error.html',
            error_code=401,
            error_message="No responses sheets found in the selected folder.<br>"
                          "A valid responses sheet is a Google Sheets file with "
                          "\"(Responses)\" as a suffix.<br>"
                          "Please make sure that at least one such file is "
                          "present in the selected folder and that you have "
                          "granted Povinator sufficient privileges to navigate "
                          "that folder."
        ), 401


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
    log = ''
    pres_folder = None
    zip_path = None
    try:
        for step in core.go(url, sheets, download, zip):
            if type(step) == str:
                title = step
            else:
                title, *_ = step
            if title == 'renamed':
                _, old_name, new_name, success = step
                if success:
                    log += f'Renamed "{old_name}" -> "{new_name}".\n'
                else:
                    log += f'<b>Could not rename</b> "{old_name}" -> ' \
                           f'"{new_name}".\n'
            elif title == 'moved':
                _, file_name, folder, success = step
                if success:
                    log += f'Moved "{file_name}" into "{folder}".\n'
                else:
                    log += f'<b>Could not move</b> "{file_name}" into ' \
                           f'"{folder}".\n'
            elif title == 'downloading':
                log += 'Downloading presentations... '
            elif title == 'download_done':
                log += 'done.\n'
                _, pres_folder = step
            elif title == 'download_error':
                log += '<b>Error</b> while downloading presentations.\n' \
                       'Maybe a folder with the same name already exists?\n'
            elif title == 'zipping':
                log += 'Creating zip archive of presentations... '
            elif title == 'zip_done':
                log += 'done.\n'
                _, zip_path = step
            else:
                log += step + '\n'
        log += '\nDone. Bye :)'
    except core.GoogleAPIInitializationError:
        log = '<b>Fatal Error! Could not load credentials.</b>'
    except core.NoResponsesSheetsError:
        log = '<b>No responses sheets found.</b>'
    return flask.render_template(
        'go_done.html',
        output=log,
        pres_folder=pres_folder,
        zip_path=zip_path,
    )


@app.route('/form', methods=['GET'])
def form():
    return flask.render_template(
        "form.html"
    )


@app.route('/create-form', methods=['GET'])
def create_form():
    url = flask.request.args.get('url', None)
    if url is None:
        return flask.render_template(
            "error.html",
            error_code=401,
            error_message="Please supply a URL.",
        ), 401
    try:
        core.form(url)
    except core.GoogleAPIInitializationError:
        return flask.render_template(
            "error.html",
            error_code=510,
            error_message="Could not correctly initialize Google APIs."
        ), 510
    return flask.render_template(
        "form_done.html",
    )


@app.route('/dummy', methods=['GET'])
def dummy():
    return flask.render_template('upload.html')


@app.errorhandler(404)
def error_page_404(error):
    return flask.render_template(
        "error.html",
        error_message="Page not found.",
        error_code=404,
    ), error.code


@app.errorhandler(500)
def error_page_500(error):
    return flask.render_template(
        "error.html",
        error_message="Povinator encountered an unexpected internal error.<br>"
                      "Please contact "
                      "<a href=\"mailto:daniele.parmeggiani@unitn.it\">"
                      "daniele.parmeggiani@unitn.it</a>.",
        error_code=500,
    ), error.code


def main():
    app.run(host='localhost', port=3000)


if __name__ == '__main__':
    main()
