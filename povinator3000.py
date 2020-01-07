#!/usr/bin/env python3

# Copyright (C) 2019, Daniele Parmeggiani <daniele.parmeggiani@studenti.unitn.it>
# Made by and for Ufficio 150ore, Povo, UniTN


import sys
import datetime
from pathlib import Path
import pickle
import click
import jinja2
import subprocess
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
google_mime_prefix = 'application/vnd.google-apps.'

drive_service = None
sheets_service = None


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


def download_folder(folder_id, prefix=Path.cwd()):
    info = drive_service.files().get(
        fileId=folder_id
    ).execute()
    if prefix == Path.cwd():
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


def upload_file(name, path, folder_id):
    f = drive_service.files().create(
        body={
            'name': name,
        },
        media_body=MediaFileUpload(path),
        fields='id',
    ).execute()
    move(f['id'], folder_id)
    return f['id']


def create_archive(folder):
    """ :param folder: Folder from which to create a ZIP file. """
    import shutil
    shutil.make_archive(folder, 'zip', folder)


def init_and_welcome():
    global drive_service, sheets_service
    
    drive_service, sheets_service = load_credentials()
    if drive_service is None or sheets_service is None:
        click.secho('Fatal Error! Could not load credentials.', fg='red')
        return False
    click.secho('Welcome to Povinator3000!', bold=True)
    return True


@click.group()
def cli():
    pass


@cli.command(help='Rename the submitted presentations and move them '
                  'to the right folder.')
def go():
    if not init_and_welcome():
        return 1
    url = click.prompt('Please, enter the "Lauree" folder')
    folder_id = url.split('/')[-1]
    ls = listdir(folder_id)
    tree = get_folder_structure(folder_id)
    responses_sheets = []
    for f in ls:
        if f['name'].endswith(responses_sheet_suffix) \
             and f['mimeType'] == google_sheet_mime:
            if click.confirm(f'Is "{f["name"]}" a responses sheet?', default='y'):
                responses_sheets.append(f)
    for sheet_file in responses_sheets:
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
            file_ext = Path()
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
                click.secho(f"[{i+1}/{len(values)}] Renamed \"{file_prev['name']}\" -> \"{new_name}\".")
            else:
                click.secho(f"[{i+1}/{len(values)}] Could not rename \"{file_prev['name']}\" -> \"{new_name}\".", fg='yellow')
            commission = row[7]
            for j in range(7, len(row)-1):
                if commission == '':
                    commission = row[j]
            try:
                dest_folder = tree[row[6]][commission]['metadata']['id']
                dest_folder_name = tree[row[6]][commission]['metadata']['name']
            except KeyError:  # "I don't know"
                dest_folder = tree[row[6]]['metadata']['id']
                dest_folder_name = tree[row[6]]['metadata']['name']
            if move(file_id, dest_folder):
                click.secho(f"[{i+1}/{len(values)}] Moved \"{new_name}\" into \"{dest_folder_name}\".")
            else:
                click.secho(f"[{i+1}/{len(values)}] Could not move \"{new_name}\" into \"{dest_folder_name}\".", fg='yellow')
    if not responses_sheets:
        click.secho('No responses sheets found.', fg='red')
        return 1
    if click.confirm('Would you like to download the presentations?', default='y'):
        click.secho('Downloading presentations... ', nl=False)
        path = download_folder(folder_id)
        if path:
            click.secho('Done.')
            if click.confirm('Would you like to make a ZIP archive of the presentations?', default='y'):
                create_archive(str(path))
        else:
            click.secho('Error while downloading presentations.\nMaybe a folder with the same name already exists?', fg='red')
    click.secho('Done. Bye :)', bold=True)
    return 0


@cli.command(help='Create a Google Form based on the given folder structure.')
def form():
    if not init_and_welcome():
        return 1
    url = click.prompt('Please, enter the "Lauree" folder')
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
        temp_path = Path().cwd() / uuid.uuid4().hex
        with open(temp_path, 'w') as f:
            f.write(out)
        upload_file(
            f"Create Form {'IT' if 'IT' in ff else 'EN'}",
            temp_path,
            folder_id
        )
        temp_path.unlink()  # os.remove equivalent
    click.secho('Important!', bold=True)
    click.secho("""Remember to:

  1. In the "Department / Faculty" question click on the menu and select "Go to Section based on Answer";
  2. Select the sections to go to, so as to match the options;
  3. In each "Commission" section, select "Go to section X (Your Presentation)" at the bottom, instead of "Continue to next section";
  4. In the last section ("Your Presentation") add a new question:
    4a. Set the type to "File Upload";
    4b. Name it "Upload your Presentation";
    4c. Select "Allow only specific file types" and select "Presentation" and "PDF";
    4d. Set the maximum number of files to 5;
    4e. Set the maximum file size to 1GB;
    4f. Enable "Required";
  5. Go to the top of the page and modify the settings (cogwheel icon);
    5a. In "General", select "Always" instead of "If respondent requests it";
    5b. Set the maximum size for all files uploaded to 100GB;
    5c. Click "Save";
  6. Pick Any Colour You Like c:
""")
    return 0


if __name__ == '__main__':
    sys.exit(
        cli()
    )

