import  json

from django.contrib.auth import  user_logged_in,user_logged_out
from  django.contrib.auth.models import  User
from django.core import serializers
from django.contrib import  messages
from django.db.models.signals import post_save,post_delete,pre_delete
from  django.dispatch import  receiver
from  django.forms import  model_to_dict
from  Shop.models import  Song
from api.drive_api import deleteFile

@receiver(user_logged_in, sender=User)
def update_session(request, user, **kwargs):
    # print("Save session")
    # data = serializers.serialize("json", [user])
    # # data = model_to_dict(User, exclude=['groups'])
    # print(data)
    request.session['user_id'] = user.id
    request.session['username'] = user.username
    request.session['fullname'] = user.get_full_name()
    messages.success(request, 'Login Successfully')


@receiver(pre_delete, sender=Song)
def delete_on_drive(instance, using, **kwargs):
    print("Signal delete_on_drive")
    deleteFile(instance.id)


@receiver(user_logged_out, sender=User)
def message_logged_out(request, user, **kwargs):
    messages.warning(request, 'Logged out!')


@receiver(pre_delete, sender=User)
def delete_on_drive(instance, using, **kwargs):
    print("Signal delete_on_drive")
    if hasattr(instance, 'profile') and instance.profile.drive_folder_id:
            deleteFile(instance.profile.drive_folder_id)