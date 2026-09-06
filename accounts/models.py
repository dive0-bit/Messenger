from django.db import models
from django.contrib.auth.models import User

class Profiles(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE)
    bio = models.TextField(blank=True, max_length=500)
    profile_picture = models.ImageField(upload_to= 'profile_pictures/',blank= True, null= True)
    created_at = models.DateTimeField(auto_now_add= True)
    
    def __str__(self):
        return self.user.username