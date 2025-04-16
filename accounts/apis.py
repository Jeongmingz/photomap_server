from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import Account, User
class LoginAPI(APIView):
	def post(self, request):
		profile = request.data.get('profile')
		provider = request.data.get('provider')
		if provider == 'kakao':
			provider_account_id = profile.get("id")
			email = profile.get("kakao_account").get("email")
			name = profile.get("properties").get("nickname")
			image = profile.get("properties").get("profile_image")
		else:
			return Response({})

		try:
			account = Account.objects.get(
				provider = provider,
				provider_account_id = provider_account_id,
				)
			user = account.user
		except Account.DoesNotExist:
			user = User.objects.create(
				email=email,
				email_verified=timezone.now(),
				name=name,
				image=image,
				is_active=True,
				last_login=timezone.now()
				)

			Account.objects.create(
				user=user,
				provider=provider,
				provider_account_id=provider_account_id,
				)

		refresh = RefreshToken.for_user(user)

		return Response({
			'access': str(refresh.access_token),
			'refresh': str(refresh),
			'access_expires': int(refresh.access_token['exp']),
			'user': {
				'id': user.id,
				'email': user.email,
				'name': user.name,
				'image': user.image,
				}
			}, status=status.HTTP_200_OK)



class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # access 토큰의 만료 시간 추출
        access_token = response.data.get('access')
        if access_token:
            from rest_framework_simplejwt.backends import TokenBackend
            from django.conf import settings
            token_backend = TokenBackend(algorithm='HS256', signing_key=settings.SECRET_KEY)
            decoded = token_backend.decode(access_token, verify=True)
            access_expires = decoded['exp']
            response.data['access_expires'] = access_expires
        return response
