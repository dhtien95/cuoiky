from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver


class Song(models.Model):
    id = models.CharField(max_length=20, primary_key=True, unique=True)
    name = models.CharField('Song Name', null=True, blank=True, max_length=100)
    link = models.CharField(null=True, blank=True, max_length=200)
    author = models.CharField('Author', null=True, blank=True, max_length=100)
    extension = models.CharField(null=True, blank=True, max_length=20)
    price = models.FloatField('Price', default=0)
    signature = models.CharField(blank=True, max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        if self.author is None:
            self.author = " "
        owner = ""
        if self.owner:
            owner = "||| =====>Owner: " + (self.owner.username)
        return self.name + " - " + self.author + " | " + self.id + owner

    def save(self, *args, **kargs):
        if self.link is None:
            self.link = "https://docs.google.com/uc?export=open&id="+self.id
        super(Song, self).save(*args, **kargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    songs = models.ManyToManyField(Song, blank=True)
    drive_folder_id = models.CharField(max_length=60, null=True, blank=True)

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=User)
    def update_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)
        instance.profile.save()

    def get_list_songs(self):
        return " | ".join([song.name for song in self.songs.all()])
