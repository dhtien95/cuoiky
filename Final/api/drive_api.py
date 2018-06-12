import io
import os

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from httplib2 import Http
from oauth2client import file
import apiclient

from  Shop.models import Song

from api.auth import  Auth

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('credentials.json')
auth = Auth(SCOPES, store)
creds = auth.getCrendentials()
mp3_store_folder_id = '1__kTvAFCeI7GOT_mT7qCb02BWow-OQLq'
mp3_store_user_folder_id = '1ckC47yjY6QFIOPrbZRmtQJk_RMgwPy1E'
service = apiclient.discovery.build('drive', 'v3', http=creds.authorize(Http()))

downloads_path = os.path.expanduser(os.sep.join(["~","Downloads"]))

def list_files(size=10, folder_id= mp3_store_folder_id):
    results = service.files().list(
        pageSize=10, fields="nextPageToken,files(id,name)", q="'{0}' in parents".format(folder_id)).execute()
    items = results.get('files',[])
    if not items:
        print('No files found.')
    for item in items:
        print('{0} ({1})'.format(item['name'], item['id']))
    return items


def get_files(fileID):
    results = service.files().get(fileId=fileID).execute()
    return results

def load_files_to_sqlite():
    Song.objects.all().delete()
    results = service.files().list(
        pageSize=10,fields="nextPageToken, files(id,name)", q="'{0}' in parents".format(mp3_store_folder_id)).execute()
    items = results.get('files',[])
    if not items:
        print('No files found.')
    else:
        print('Files.')
        for item in items:
            print('{0} ({1})'.format(item['name'], items['id']))
            id = item['id']
            name = item['name'].rsplit(' - ')[0]
            author, extension = item['name'].rsplit(' - ')[1].rsplit('.',1)
            song = Song(name = name, id = id, author = author, extension = extension)
            song.save()
            print('Save to database')
def uploadFile(filename,filepath, mimetype,folder_id=mp3_store_folder_id):
    file_metadata = {'name':filename, 'parents': ['%s' % folder_id]}
    media = MediaFileUpload(filepath,
                            mimetype=mimetype)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print("Upload file", file.get('id'))
    return file.get('id')

def downloadFile(file_id,file_name,file_path=downloads_path):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    full_path = file_path + os.sep + file_name if file_name else file_id
    while done is False:
        status,done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    with io.open(full_path,'wb') as  f:
        fh.seek(0)
        f.write(fh.read())
    print("Download success: " + full_path)
    return full_path

def createFolder(name):
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [mp3_store_user_folder_id],
    }
    user_permission = {
        'role': 'reader',
        'type': 'anyone'
    }
    file = service.files().create(body=file_metadata, fields='id').execute()

    def callback(request_id, response, exception):
        if exception:
            # Handle error
            print
            exception
        else:
            print
            "Permission Id: %s" % response.get('id')

    batch = service.new_batch_http_request(callback=callback)
    batch.add(service.permissions().create(
        fileId=file.get('id'),
        body=user_permission,
        fields='id',
    ))
    batch.execute()
    # permission = service.permissions().create(fileId=file.get('id'),body=file_metadata,fields='id').execute()
    print('Folder ID: %s' % file.get('id'))
    return file.get('id')


def searchFile(size, query):
    results = service.files().list(
        pageSize=size, fields="nextPageToken, files(id, name, kind, mimeType)", q=query).execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(item)
            print('{0} ({1})'.format(item['name'], item['id']))


def deleteFile(file_id):
    try:
        results = service.files().delete(fileId=file_id).execute()
    except HttpError as e:
        print(e.content)
    print("Removed file ", file_id)