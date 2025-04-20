from photo.models import Photo, PhotoBrand, PhotoFile


def create_photo_and_files(user, url, site_id, photo_id, url_dict, response_data):
    status = 0

    if not response_data.get("success") and response_data.get("message") == "다운로드 기간이 만료되었습니다.":
        status = 1

    photo_instance = Photo.objects.create(
        user=user,
        url=url,
        brand=PhotoBrand.objects.get(pk=site_id),
        code=photo_id,
        status=status
    )
    files_list = []
    for i, (k, v) in enumerate(url_dict.items(), start=1):
        files_list.append(PhotoFile(
            photo=photo_instance,
            url=v,
            type=k,
            order=i
        ))
    PhotoFile.objects.bulk_create(files_list)
    return photo_instance
