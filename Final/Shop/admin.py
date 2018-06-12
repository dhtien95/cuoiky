from django.contrib import admin
from .models import Song,Profile


# Register your models here.
class SongAdmin(admin.ModelAdmin):
    list_display = ('id','name','link','author','price','signature','owner')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user','get_list_songs','drive_folder_id')

admin.site.register(Song, SongAdmin)
admin.site.register(Profile,ProfileAdmin)