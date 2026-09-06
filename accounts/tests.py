from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Profiles


class RegistrationViewTests(TestCase):
	def test_profile_picture_upload_is_saved_and_rendered(self):
		user = User.objects.create_user(
			username="picture-user",
			password="a-strong-password",
		)
		Profiles.objects.create(user=user)
		self.client.login(username="picture-user", password="a-strong-password")
		image = SimpleUploadedFile(
			"avatar.png",
			b"\x89PNG\r\n\x1a\n",
			content_type="image/png",
		)

		response = self.client.post("/profile/update/", {
			"bio": "Available for a chat",
			"profile_picture": image,
		})

		self.assertRedirects(response, "/home/")
		profile = Profiles.objects.get(user=user)
		self.assertTrue(profile.profile_picture.name.startswith("profile_pictures/avatar"))
		home_response = self.client.get("/home/")
		self.assertEqual(home_response.status_code, 200)
		self.assertEqual(home_response.context["profile"].pk, profile.pk)
		self.assertContains(home_response, profile.profile_picture.url)
	def test_login_accepts_email_address(self):
		User.objects.create_user(
			username="login-user",
			email="login@example.com",
			password="a-strong-password",
		)

		response = self.client.post(reverse("login"), {
			"username": "login@example.com",
			"password": "a-strong-password",
		})

		self.assertRedirects(response, "/home/")

	def test_registration_creates_user_and_redirects(self):
		response = self.client.post(reverse("register"), {
			"username": "new-user",
			"email": "new@example.com",
			"password": "a-strong-password",
			"confirm_password": "a-strong-password",
		})

		self.assertRedirects(response, reverse("login"))
		self.assertTrue(User.objects.filter(username="new-user").exists())

	def test_registration_rejects_mismatched_passwords(self):
		response = self.client.post(reverse("register"), {
			"username": "new-user",
			"email": "new@example.com",
			"password": "a-strong-password",
			"confirm_password": "different-password",
		})

		self.assertContains(response, "Passwords do not match")
		self.assertFalse(User.objects.filter(username="new-user").exists())

	def test_registration_api_is_public(self):
		response = self.client.post("/api/register/", {
			"username": "api-user",
			"email": "api@example.com",
			"password": "a-strong-password",
		}, content_type="application/json")

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.json()["user"]["username"], "api-user")

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_password_reset_generates_email_with_reset_link(self):
		User.objects.create_user(
			username="reset-user",
			email="reset@example.com",
			password="a-strong-password",
		)

		response = self.client.post("/forgot-password/", {"email": "reset@example.com"})

		self.assertRedirects(response, "/reset-password/done/")
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("/reset-password/", mail.outbox[0].body)

	def test_password_reset_confirmation_accepts_fresh_link(self):
		user = User.objects.create_user(
			username="confirm-user",
			email="confirm@example.com",
			password="old-password-123",
		)
		uid = urlsafe_base64_encode(force_bytes(user.pk))
		token = default_token_generator.make_token(user)
		initial_url = reverse("password_reset_confirm", args=[uid, token])

		redirect_response = self.client.get(initial_url)
		self.assertRedirects(
			redirect_response,
			f"/reset-password/{uid}/set-password/",
		)

		confirm_url = redirect_response["Location"]
		self.assertContains(self.client.get(confirm_url), "Set New Password")
		response = self.client.post(confirm_url, {
			"new_password1": "new-password-123",
			"new_password2": "new-password-123",
		})

		self.assertRedirects(response, reverse("password_reset_complete"))
		self.assertTrue(self.client.login(username="confirm-user", password="new-password-123"))
