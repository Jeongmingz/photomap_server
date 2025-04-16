from django.db import models

from accounts.models import User



class PhotoBrand(models.Model):
	name = models.CharField(
		max_length=100
		)

	patten = models.CharField(
		max_length=1000
		)


class Photo(models.Model):
	user = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		db_column='userId'
		)

	code = models.CharField(
		max_length=1000
		)

	url = models.URLField()

	brand = models.ForeignKey(
		PhotoBrand,
		on_delete=models.SET_NULL,
		db_column='brandId',
		null=True,
		blank=True,
		)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		indexes = [
			models.Index(fields=['code'], name="photo_code_idx")
			]

class PhotoFile(models.Model):
	photo = models.ForeignKey(
		Photo,
		db_column='photoId',
		on_delete=models.CASCADE,
		)
	url = models.URLField()
	type = models.CharField(
		max_length=20
		)
	order = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)

