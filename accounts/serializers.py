from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profiles


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id','username','email']
        
class RegisterSerializer(serializers.Serializer):
    
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password= serializers.CharField(write_only=True, min_length= 8)
    
    
    def create(self, validated_data):
        
        user = User.objects.create_user(
            username = validated_data['username'],
            email = validated_data['email'],
            password = validated_data['password']
        )
        Profiles.objects.create(user=user)
        
        return user