from urllib import parse


def qr_uri_brand_check(url: str) -> int:
	if "photogary" in url or 'pgshort.aprd.io' in url:
		print('PhotoGary')
		return 1 , url.split("/")[-1]
	elif "t9.pixpixlink.com" in url:
		print('PhotoLAB+')
		return 2, parse.parse_qs(parse.urlparse(url).query)['id'][0]
	return 0, None

