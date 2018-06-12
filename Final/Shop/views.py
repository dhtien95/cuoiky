import  datetime
import  operator
import os
from functools import reduce

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import  HttpResponse, HttpResponseRedirect
from  django.shortcuts import render, redirect

#Create your views here
from  django.views.decorators.csrf import csrf_protect

from Shop import services
from  Shop.forms import UploadFileForm, SignUpForm, GetSignatureForm
from Shop.models import Song,Profile,User
from api import drive_api
from api.drive_api import  list_files,get_files,load_files_to_sqlite,downloadFile,uploadFile,createFolder,deleteFile

def home(request):
    user_id = request.session.get('user_id', None)
    user = User.objects.get(pk=user_id) if user_id else None
    user_name_songs = [song['name'] for song in user.profile.songs.values()] if user else []

    list_songs = list_files()
    songs = []
    for song in list_songs:
        s = Song.objects.get(pk=song['id'])
        if s.name in user_name_songs:           # Update song id if that song user archived
            s = user.profile.songs.values().get(name=s.name)
        songs.append(s)

    return render(request, 'index.html', {'songs': songs, 'user': user, 'user_name_songs': user_name_songs})


def download(request, song_id):
    song = Song.objects.get(pk=song_id)
    print("Start download file name: " + song.name)
    downloadFile(song_id, song.name + " - " + song.author + "." + song.extension)
    print("Downloaded")
    return HttpResponseRedirect(request.GET.get('return_url'))


@login_required()
def upload(request):
     # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():     # check whether it's valid
            name = form.cleaned_data['name']
            author = form.cleaned_data['author']
            price = form.cleaned_data['price']
            my_file = request.FILES['myFile']
            print(my_file.content_type)
            extension = my_file.name.rsplit('.', 1)[1]
            user = User.objects.get(pk=request.session['user_id'])
            if not user.is_superuser:                           # if normal user, upload to their own directory
                if user.profile.drive_folder_id:
                    folder_id = user.profile.drive_folder_id
                else:
                    folder_id = createFolder(user.username)
                    user.profile.drive_folder_id = folder_id
                    user.profile.save()
            else:                                       # if superuser upload to shiro store directory
                folder_id = drive_api.mp3_store_folder_id
            file_id = uploadFile(name + " - " + author + "." + extension, my_file.temporary_file_path(), my_file.content_type, folder_id=folder_id)

            new_song = Song(id=file_id, name=name, author=author, extension=extension, price=price)
            if not user.is_superuser:
                new_song.owner = user
                user.profile.songs.add(new_song)
                user.profile.save()
            new_song.save()

            return redirect('homepage')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            auth_login(request, user)
            messages.success(request, 'Register new account succeeded!')
            return redirect('homepage')
    else:
        form = SignUpForm()
    return render(request, 'sites/signup.html', {'form':form})


@login_required()
def buy_song(request, song_id):
    print("-------------Buy Song---------------")
    # Get user info
    user = User.objects.get(pk=request.session['user_id'])
    origin_song = Song.objects.get(pk=song_id)

    #Get Song From Drive
    print("Start buy music")
    file_path = os.path.expanduser(os.sep.join(["~", "Downloads"]))
    downloaded_file_name = "{0} - {1}.{2}".format(song_id, str(user.id), origin_song.extension)
    downloaded_file_path = downloadFile(file_id=song_id, file_name=downloaded_file_name, file_path=services.downloads_path)

    #Sign Signature To Song
    signature_message = "|Song [{2}] - Signed by user: \"{0}\" - {1}".format(request.session['username'], str(datetime.datetime.now()), origin_song.name)
    encoder = services.EncodeWAV()
    encoded_file_path = encoder.encode_file(file_path=downloaded_file_path, msg=signature_message, file_name=downloaded_file_name)


    #Upload Song to User Folder
    # decoder = services.DecodeWAV()
    # msg = decoder.decode_file(encoded_file_path)
    new_song_id = services.upload_new_song(user=user, song_id=song_id, file_path=encoded_file_path, signature=signature_message)

    #Delete on local
    os.remove(downloaded_file_path)
    print("Removed file: ", downloaded_file_path)
    # return signed_song
    # Save message to database
    messages.success(request, "Succeeded buy song {0}".format(origin_song.name))
    return redirect('info', username=user.username)


@login_required()
def info(request, username):
    if username != request.session['username']:
        return redirect('info', username=request.session['username'])
    print("User info: ")
    user = User.objects.get(username=username)
    print(user.profile)
    list_songs_id = [song['id'] for song in user.profile.songs.values()]
    print(list_songs_id)
    # songs = Song.objects.get(id__contains=[list_songs_id])
    # query = reduce(operator.and_, (Q(id__contains=item) for item in list_songs_id))
    # songs = Song.objects.filter(query)
    songs = user.profile.songs.all

    return render(request, 'sites/info.html', {'user': user, 'songs': songs})


def ajax_signature(request, song_id):
    song = Song.objects.get(pk=song_id)
    if song.signature:  # in case query from info page
        return HttpResponse(song.signature)
    else:               # in case query from index
        current_user = User.objects.get(pk=request.session['user_id'])
        song = current_user.profile.songs.get(name=song.name)
        return HttpResponse(song.signature)


@csrf_protect
def signature(request):
    """
    Get Signature from uploaded file
    :param request:
    :return:
    """
    if request.POST:
        form = GetSignatureForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['myFile']
            decoder = services.DecodeWAV()
            msg = decoder.decode_file(file_path=f.temporary_file_path())
            file_name = f.name
            print("file: ", f, "| Temporary path: ", f.temporary_file_path(), "| Msg: ", msg)
            return render(request, 'signature.html', {'form': form, 'msg': msg, 'file_name': file_name})
    else:
        form = GetSignatureForm()
    return render(request, 'signature.html', {'form': form})