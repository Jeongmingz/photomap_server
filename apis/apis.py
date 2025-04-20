from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from photo.models import Photo, PhotoBrand, PhotoFile
from photo.utils import create_photo_and_files
from utils.r2 import four_cut_photo_qr_download
from utils.share import qr_uri_brand_check

@permission_classes([IsAuthenticated])
@api_view(["POST"])
def qr_photo_check_api(request):
	user = request.user
	url = request.data.get('url', None)

	if user.is_anonymous:
		return Response(status=status.HTTP_401_UNAUTHORIZED)

	if url is None:
		return Response(status=status.HTTP_404_NOT_FOUND)
	site_id, photo_id = qr_uri_brand_check(url)

	if site_id == 0:
		return Response({"success": False, "message": "등록되지 않은 브랜드입니다. 문의해주세요"}, status=status.HTTP_200_OK)

	try:
		Photo.objects.get(code=photo_id)
		return Response({
			"success": False,
			"message": "이미 저장된 사진입니다",
			"files": []
			}, status=status.HTTP_200_OK)
	except Photo.DoesNotExist as e:
		pass

	response_data, url_dict = four_cut_photo_qr_download(site_id, url, photo_id, user)
	create_photo_and_files(user, url, site_id, photo_id, url_dict, response_data)
	return Response(response_data, status=status.HTTP_200_OK)


