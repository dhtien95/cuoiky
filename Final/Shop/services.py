import os
from mimetypes import MimeTypes

from django.contrib.auth.models import User
from Shop.models import Song
from api import drive_api
from api.drive_api import downloads_path,createFolder

from sys import  argv

downloads_path = os.path.expanduser((os.sep.join(["~","Downloads"])))

class EncodeWAV:

    def __init__(self):
        self.header_offset =44
        self.DELIMITER='$'
        self.error_msg=""
        self.encoded_file = ''
        self.processing_byte_ord = self.header_offset

def encode_file(self, file_path,msg,file_name):
    origin_file = open(file_path, 'rb').read()
    origin_file = bytearray(origin_file)
    self.encoded_file=origin_file

    #if b"WAE" in origin_file[8:11]:
    msg_len_str = str(len(msg)) #show check case len(msg) > file size
    self.hide(msg_len_str + self.DELIMITER) # Insert Len of Msg
    self.hide(msg)                          # Insert Msg

    full_path = downloads_path + os.sep + file_name
    fh = open(full_path,'wb')
    fh.write(self.encoded_file)
    fh.close()
    return  full_path

def hide(self,msg):
    for c in msg:
        c_in_binary = '{0:08b}'.format(ord(c))
        for b in  c_in_binary:
            new_value = self.encoded_file[self.processing_byte_ord] + self.encoded_file[
                self.processing_byte_ord] % 2 + int(b)
            self.encoded_file[self.processing_byte_ord] = new_value % 256
            self.processing_byte_ord += 1

        class DecodeWAV:

            def __init__(self):
                self.msg = ''
                self.header_offset = 44
                self.DELIMITER = '$'
                self.error_msg = ""
                self.len_hidden_msg = ""
                self.processing_byte_ord = self.header_offset

            def decode_file(self, file_path):
                encoded_file = open(file_path, 'rb').read()
                encoded_file = bytearray(encoded_file)
                processing_byte_ord = self.header_offset
                # if b"WAV" in encoded_file[8:11]:
                # get msg length
                temp_byte = ""
                while True:
                    for b in encoded_file[processing_byte_ord:processing_byte_ord + 8]:
                        temp_byte += (str(b % 2))

                    decrypted_char = chr(int(temp_byte, 2))
                    self.msg += decrypted_char
                    temp_byte = ""
                    processing_byte_ord += 8
                    if decrypted_char == '$':
                        try:
                            self.len_hidden_msg = int(self.msg[:-1])  # Ignore '$' char at the end
                            self.msg = ""
                            break
                        except ValueError:
                            return "This file has no Signature"
                for i in range(0, self.len_hidden_msg):
                    for b in encoded_file[processing_byte_ord:processing_byte_ord + 8]:
                        temp_byte += (str(b % 2))

                    decrypted_char = chr(int(temp_byte, 2))
                    self.msg += decrypted_char
                    temp_byte = ""
                    processing_byte_ord += 8
                return self.msg
                # endif

        def upload_new_song(user, song_id, file_path, signature=None):
            # Get song info
            print("Upload new song \nSong path: ", file_path)
            song = Song.objects.get(pk=song_id)
            name = song.name
            author = song.author
            price = song.price
            extension = song.extension = open(file_path).name.rsplit('.', 1)[1]
            print("Extension: ", extension)
            mime_type = MimeTypes()
            content_type = mime_type.guess_extension(file_path)
            print("Mime type: ", content_type)

            if not user.is_superuser:  # if normal user, upload to their own directory
                if user.profile.drive_folder_id:
                    folder_id = user.profile.drive_folder_id
                else:
                    folder_id = drive_api.createFolder(user.username)
                    user.profile.drive_folder_id = folder_id
                    user.profile.save()
            else:  # if superuser upload to shiro store directory
                folder_id = drive_api.shiro_store_folder_id

            output_filename = name + " - " + author + "." + extension
            file_id = drive_api.uploadFile(output_filename, file_path, content_type, folder_id=folder_id)

            # Build new song with info
            new_song = Song(id=file_id, name=name, author=author, extension=extension, price=price)
            if signature:
                new_song.signature = signature

            if not user.is_superuser:
                new_song.owner = user
                new_song.save()
                user.profile.songs.add(new_song)  # Update Archived Song to Profile
                user.profile.save()
            else:
                new_song.save()

            return file_id