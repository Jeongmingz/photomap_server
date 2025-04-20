from urllib import parse


def qr_uri_brand_check(url: str) -> int:
	if "photogary" in url or 'pgshort.aprd.io' in url:
		print('PhotoGary')
		return 1 , url.split("/")[-1]
	elif "t9.pixpixlink.com" in url:
		print('PhotoLAB+')
		return 2, parse.parse_qs(parse.urlparse(url).query)['id'][0]
	elif "kor1.monomansion.net" in url:
		print('Monomansion')
		return 3, parse.parse_qs(parse.urlparse(url).query)['qrcode'][0]
	elif "qr.seobuk.kr" in url:
		print("Photoism")
		return 4, url.split("/")[-1]
	return 0, None