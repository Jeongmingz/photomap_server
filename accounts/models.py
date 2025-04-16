from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


class User(AbstractBaseUser, PermissionsMixin):
	name = models.CharField(max_length=255, null=True, blank=True)
	email = models.EmailField(unique=True, null=True, blank=True)
	email_verified = models.DateTimeField(null=True, blank=True)
	image = models.URLField(max_length=500, null=True, blank=True)
	last_login = models.DateTimeField(null=True, blank=True)  # AbstractBaseUser 기본 필드
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# 필수 필드
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = [email, name, id]

	class Meta:
		db_table = 'User'

	def __str__(self):
		return self.email or self.id


class Account(models.Model):
	user = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='accounts',
		db_column='userId'
		)
	provider = models.CharField(max_length=255)
	provider_account_id = models.CharField(
		max_length=255,
		db_column='providerAccountId'
		)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'Account'
		constraints = [
			models.UniqueConstraint(
				fields=['provider', 'provider_account_id'],
				name='unique_provider_account'
				)
			]
