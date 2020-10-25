#!/usr/bin/env python3

# Copyright (C) 2019, Daniele Parmeggiani <daniele.parmeggiani@studenti.unitn.it>
# Made by and for Ufficio 150ore, Povo, UniTN
import json
import shutil
import sys
import datetime
import tempfile
from pathlib import Path
import pickle
import click
import jinja2
import io
import uuid
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]

file_upload_folder_suffix = '(File responses)'
responses_sheet_suffix = '(Responses)'
google_folder_mime = 'application/vnd.google-apps.folder'
google_sheet_mime = 'application/vnd.google-apps.spreadsheet'
google_script_mime = 'application/vnd.google-apps.script'
google_mime_prefix = 'application/vnd.google-apps.'

drive_service = None
sheets_service = None

DOWNLOADS_FOLDER = Path.cwd() / 'downloads'


def load_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = Path('token.pickle')
    credentials_path = Path('credentials.json')
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    return drive_service, sheets_service


def listdir(folder_id):
    children = drive_service.files().list(
        q=f"'{folder_id}' in parents"
    ).execute()
    return children.get('files', [])


def move(file_id, new_folder_id):
    old_parents = drive_service.files().get(
        fileId=file_id,
        fields='parents'
    ).execute().get('parents')
    old_parents = ','.join(old_parents)
    resp = drive_service.files().update(
        fileId=file_id,
        addParents=new_folder_id,
        removeParents=old_parents,
        fields='id, parents',
    ).execute()
    return resp['parents'] == [new_folder_id]


def get_folder_structure(root):
    """:param root: The ID of the folder root of the tree.
    Returns the tree structure from folder `root`, in the form:
        ```{
            'metadata': {
                'id': '...',
                'name': '...',
                'mimeType': '...'
            }
            'sub_1': {
                'metadata': {...},
                'sub_1_sub_1': {'metadata': {...}},
                'sub_1_sub_2': {'metadata': {...}},
            }
            'sub_2': {
                'metadata': {...}
            }
        }```
    """
    info = drive_service.files().get(
        fileId=root
    ).execute()
    tree = {
        'metadata': info
    }
    for child in listdir(root):
        if child['mimeType'] == google_folder_mime:
            tree[child['name']] = get_folder_structure(child['id'])
    return tree


def download_file(file_id, path):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        with open(path, 'wb') as f:
            f.write(fh.getvalue())


def download_folder(folder_id, prefix=DOWNLOADS_FOLDER):
    info = drive_service.files().get(
        fileId=folder_id
    ).execute()
    if prefix == DOWNLOADS_FOLDER:
        folder = prefix / (info['name'] + ' ' +
                           datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
    else:
        folder = prefix / info['name']
    if folder.exists():
        return False
    folder.mkdir()
    for child in listdir(folder_id):
        if child['mimeType'] == google_folder_mime:
            if not download_folder(child['id'], prefix=folder):
                return False
        else:
            if not child['mimeType'].startswith(google_mime_prefix):
                download_file(child['id'], folder / child['name'])
    return folder


def upload_file(name, path, folder_id, mime_type=None, media_mime_type=None):
    # https://github.com/googleapis/google-api-nodejs-client/issues/680
    f = drive_service.files().create(
        body={
            'name': name,
            'mimeType': mime_type,
        },
        media_body=MediaFileUpload(
            path, mimetype=media_mime_type),
        fields='id',
    ).execute()
    # f = drive_service.files().create(
    #     body={
    #         'name': name,
    #         'mimeType': 'application/vnd.google-apps.script',
    #     },
    #     media_body=MediaFileUpload(path, mimetype='application/vnd.google-apps.script+json'),
    #     fields='id',
    # ).execute()
    move(f['id'], folder_id)
    return f['id']


def create_archive(folder):
    """ :param folder: Folder from which to create a ZIP file. """
    import shutil
    return shutil.make_archive(folder, 'zip', folder)


def init():
    global drive_service, sheets_service
    drive_service, sheets_service = load_credentials()
    if drive_service is None or sheets_service is None:
        return False
    return True


def get_sheets(folder_url):
    if not init():
        raise GoogleAPIInitializationError
    folder_id = folder_url.split('/')[-1]
    ls = listdir(folder_id)
    resp_sheets = []
    for f in ls:
        if f['name'].endswith(responses_sheet_suffix) \
                and f['mimeType'] == google_sheet_mime:
            resp_sheets.append(f['name'])
    return resp_sheets


class GoogleAPIInitializationError(Exception):
    pass


class NoResponsesSheetsError(Exception):
    pass


def go(folder_url, responses_sheets, download, make_zip):
    if not init():
        raise GoogleAPIInitializationError
    folder_id = folder_url.split('/')[-1]
    ls = listdir(folder_id)
    tree = get_folder_structure(folder_id)
    resp_sheets = []
    for f in ls:
        if f['name'].endswith(responses_sheet_suffix) \
                and f['mimeType'] == google_sheet_mime:
            if f['name'] in responses_sheets:
                resp_sheets.append(f)
    for sheet_file in resp_sheets:
        sheet = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_file['id'],
            range='Form Responses 1!A2:Z'
        ).execute()
        values = sheet.get('values', [])
        for i, row in enumerate(values):
            # Last element of each row is (or should be) in the form
            # https://drive.google.com/open?id=1jkKGUUuyEUoHJM6affR46Y9UI98zwlNf
            file_id = row[-1].split('id=')[-1]
            file_prev = drive_service.files().get(
                fileId=file_id,
            ).execute()
            extension = Path(file_prev['name']).suffix
            new_name = '_'.join([row[2], row[3]])
            new_name = new_name.replace(' ', '_')
            new_name += extension
            updated = drive_service.files().update(
                fileId=file_id,
                body={
                    'name': new_name,
                },
            ).execute()
            if updated['name'] == new_name:
                yield 'renamed', file_prev['name'], new_name, True
            else:
                yield 'renamed', file_prev['name'], new_name, False
            commission = row[7]
            for j in range(7, len(row) - 1):
                if commission == '':
                    commission = row[j]
            try:
                dest_folder = tree[row[6]][commission]['metadata']['id']
                dest_folder_name = tree[row[6]][commission]['metadata']['name']
            except KeyError:  # "I don't know"
                dest_folder = tree[row[6]]['metadata']['id']
                dest_folder_name = tree[row[6]]['metadata']['name']
            if move(file_id, dest_folder):
                yield 'moved', new_name, dest_folder_name, True
            else:
                yield 'moved', new_name, dest_folder_name, True
    if not responses_sheets:
        raise NoResponsesSheetsError
    if download:
        yield 'downloading'
        path = download_folder(folder_id)
        if path:
            yield 'download_done', path
            if make_zip:
                yield 'zipping'
                archive_path = Path(
                    create_archive(str(path))
                ).relative_to(DOWNLOADS_FOLDER)
                shutil.rmtree(path)
                yield 'zip_done', archive_path
        else:
            yield 'download_error'


def form(url):
    if not init():
        raise GoogleAPIInitializationError
    folder_id = url.split('/')[-1]
    tree = get_folder_structure(folder_id)
    deps = [ x for x in tree.keys() if x != 'metadata' ]
    coms = {}
    for dep in deps:
        coms[dep] = [ x for x in tree[dep].keys() if x != 'metadata' ]
    for ff in ['create_form_template_IT.gs', 'create_form_template_EN.gs']:
        with open(ff, 'r') as f:
            template = jinja2.Template(f.read())
        out = template.render(
            dt=str(datetime.datetime.now()),
            title=tree['metadata']['name'],
            departments=deps,
            commissions=coms,
        )
        with tempfile.NamedTemporaryFile(suffix='.gs') as f:
            f.write(out.encode())
            f.flush()
            upload_file(
                f"Create Form {'IT' if 'IT' in ff else 'EN'}",
                f.name,
                folder_id,
                mime_type=google_script_mime,
                media_mime_type=google_script_mime + '+json',
            )
        # temp_path = Path().cwd() / uuid.uuid4().hex
        # with open(temp_path, 'w') as f:
        #     f.write(out)
        # upload_file(
        #     f"Create Form {'IT' if 'IT' in ff else 'EN'}",
        #     temp_path,
        #     folder_id,
        #     mime_type=google_script_mime,
        # )
        # temp_path.unlink()  # os.remove equivalent
