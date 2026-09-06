from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .serializers import UserSerializer
from .models import Profiles

from rest_framework import status
from .serializers import UserSerializer, RegisterSerializer


class DevelopmentPasswordResetView(auth_views.PasswordResetView):
    def form_valid(self, form):
        users = list(form.get_users(form.cleaned_data["email"]))
        response = super().form_valid(form)

        if settings.DEBUG and users:
            user = users[0]
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_path = reverse(
                "password_reset_confirm",
                kwargs={"uidb64": uid, "token": token},
            )
            self.request.session["development_reset_link"] = self.request.build_absolute_uri(reset_path)

        return response


class DevelopmentPasswordResetDoneView(auth_views.PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.DEBUG:
            context["development_reset_link"] = self.request.session.pop(
                "development_reset_link",
                None,
            )
        return context


def password_reset_set_password(request, uidb64):
    view = auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
    )
    return view(request, uidb64=uidb64, token="set-password")


def register(request):
    
    if request.method == 'POST':
        
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            return render(request, 'accounts/register.html', {'error': 'Passwords do not match'})
        
        if User.objects.filter(username=username).exists():
            return render(request,'accounts/register.html',{'error': 'Username already exists'})
        
        user = User.objects.create_user(
            username = username,
            email = email,
            password = password
        )
        Profiles.objects.create(user=user)
        
        return redirect('login')
    
    return render(request,'accounts/register.html')

def user_login(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            matching_user = User.objects.filter(email__iexact=identifier).first()
            if matching_user:
                user = authenticate(
                    request,
                    username=matching_user.username,
                    password=password,
                )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request,'accounts/login.html', {'error': 'Invalid username or password'})

    return render(request, 'accounts/login.html')

@login_required
def home(request):
    profile, _ = Profiles.objects.get_or_create(user=request.user)
    users = User.objects.exclude(id=request.user.id).order_by("username")
    for user in users:
        user_profile = getattr(user, 'profiles', None)
        user.profile_picture_url = user_profile.profile_picture.url if user_profile and user_profile.profile_picture else ""
    return render(request, 'accounts/home.html', {
        'profile': profile,
        'chat_users': users,
    })


@login_required
def profile_update(request):
    profile, _ = Profiles.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        profile.bio = request.POST.get('bio', '').strip()
        profile.save()
    return redirect('home')

def user_logout(request):
    logout(request)
    return redirect('login')

@api_view(['GET'])
def user_list(request):
    
    users = User.objects.select_related('profiles').all()
    
    serializer = UserSerializer(users, many=True)
    
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    
    serializer = RegisterSerializer(data= request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        Profiles.objects.get_or_create(user=user)
        
        return Response(
            {
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED
                        
        )
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )