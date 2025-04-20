from typing import Dict, Tuple

import boto3
import os
from botocore.config import Config
from selenium.common import TimeoutException

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from accounts.models import User
from utils.env import return_env_value
IMAGE_EXTENSIONS = [
    "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "avif", "heif", "heic", "svg"
]
VIDEO_EXTENSIONS = [
    "mp4", "m4v", "mov", "avi", "wmv", "mkv", "webm", "flv", "f4v", "mpg", "mpeg", "3gp", "3g2", "ogv"
]


def return_admin_r2_client():
	return boto3.client(
	's3',
		endpoint_url=return_env_value("CLOUDFLARE_R2_ENDPOINT"),
		aws_access_key_id=return_env_value("CLOUDFLARE_R2_ACCESS_ADMIN_KEY_ID"),
		aws_secret_access_key=return_env_value("CLOUDFLARE_R2_ACCESS_ADMIN_KEY_SECRET"),
		config=Config(signature_version='s3v4'),
		region_name='auto'
		)


def upload_files_to_r2(download_directory, target_prefix, uploaded_files, files_dict):
	admin_r2 = return_admin_r2_client()
	bucket_name = return_env_value("CLOUDFLARE_R2_BUCKET_NAME")
	public_url = return_env_value('CLOUDFLARE_R2_PUBLIC_URL')

	for file_name in os.listdir(download_directory):
		file_path = os.path.join(download_directory, file_name)
		object_name = f"{target_prefix}{file_name}"

		try:
			with open(file_path, "rb") as f:
				admin_r2.upload_fileobj(
					f,
					bucket_name,
					object_name,
					ExtraArgs={"ContentType": "application/octet-stream"}
				)
				uploaded_files.append(f"{public_url}/{object_name}")
		except Exception as e:
			print(f"파일 업로드 실패: {e}")

	# 업로드 완료 표시
	admin_r2.put_object(
		Bucket=bucket_name,
		Key=f"{target_prefix}_SUCCESS",
		Body=b''
	)

	# files_dict 구성
	files_dict['video'] = []
	for file in uploaded_files:
		ext = file.split('.')[-1].lower()
		if ext in IMAGE_EXTENSIONS:
			files_dict['image'] = file
		elif ext in VIDEO_EXTENSIONS:
			files_dict['video'].append(file)
	if 'video' in files_dict and not files_dict['video']:
		del files_dict['video']

def four_cut_photo_qr_download(site_id: int, url: str, id: str, user: User) -> Tuple[Dict, Dict]:
	uploaded_files = list()
	files_dict = dict()

	userid = user.pk

	def wait_for_download_complete(timeout=30):
		def check_temp_files(_):
			return all(
				not (f.endswith('.crdownload') or f.startswith('.com.google.Chrome'))
				for f in os.listdir(download_directory)
			)
		WebDriverWait(driver, timeout).until(check_temp_files)

	bucket_name = return_env_value("CLOUDFLARE_R2_BUCKET_NAME")
	target_prefix = f"4cut/{userid}/{site_id}/{id}/"

	download_directory = f"/tmp/{site_id}_{id}_downloads"
	os.makedirs(download_directory, exist_ok=True)

	options = webdriver.ChromeOptions()
	options.add_argument("--headless")
	options.add_argument("--disable-gpu")
	options.add_argument("--no-sandbox")
	options.add_argument("--window-size=1920,1080")

	prefs = {
		"download.default_directory": download_directory,
		"download.prompt_for_download": False,
		"download.directory_upgrade": True,
		"safebrowsing.enabled": False,
		"profile.default_content_settings.popups": 0,
		"profile.content_settings.exceptions.automatic_downloads.*.setting": 1
	}
	options.add_experimental_option("prefs", prefs)

	driver = webdriver.Chrome(options=options)
	driver.get(url)
	try:
		match site_id:
			case 1:  # PHOTOGARY
				try:
					WebDriverWait(driver, 10).until(
						EC.presence_of_element_located((By.ID, "root"))
					)
					try:
						expired_message = "다운 가능한 기간이 만료되었습니다"
						expired_element = WebDriverWait(driver, 5).until(
							EC.presence_of_element_located((By.XPATH, f"//div[.//p[contains(text(), '{expired_message}')]]"))
						)
						return {
							"success": False,
							"message": "다운로드 기간이 만료되었습니다.",
							"files": []
						}, {}
					except TimeoutException:
						pass
					except Exception as e:
						print(f"만료 확인 오류: {e}")

					button_texts = ["사진 다운", "영상 다운", "타임랩스 다운"]
					for text in button_texts:
						try:
							initial_files = set(os.listdir(download_directory))
							btn = WebDriverWait(driver, 10).until(
								EC.presence_of_element_located((By.XPATH, f"//button[.//span[text()='{text}']]"))
							)
							driver.execute_script("arguments[0].click();", btn)
							wait_for_download_complete(30)
						except Exception as e:
							print(f"{text} 처리 실패: {e}")

					upload_files_to_r2(download_directory, target_prefix, uploaded_files, files_dict)
					return {
						"success": True,
						"message": f"{len(uploaded_files)}개의 사진을 등록했습니다.",
						"files": uploaded_files
					}, files_dict

				except Exception as e:
					return {
						"success": False,
						"message": f"처리 중 오류 발생: {str(e)}",
						"files": []
					}, {}

			case 2:  # PHOTOLAP+
				try:
					WebDriverWait(driver, 10).until(
						EC.presence_of_element_located((By.TAG_NAME, "body"))
					)

					try:
						expired_message = "다운로드 기간이 지나"
						expired_element = WebDriverWait(driver, 5).until(
							EC.presence_of_element_located((By.XPATH, f"//p[contains(text(), '{expired_message}')]"))
						)
						return {
							"success": False,
							"message": "다운로드 기간이 만료되었습니다.",
							"files": []
						}, {}
					except TimeoutException:
						pass
					except Exception as e:
						print(f"만료 확인 오류: {e}")

					download_buttons = []
					for img_src in ["picko.png", "vidko.png"]:
						try:
							btn = WebDriverWait(driver, 10).until(
								EC.presence_of_element_located((
									By.XPATH,
									f"//a[@download and .//img[contains(@src, '{img_src}')]]"
								))
							)
							download_buttons.append(btn)
						except Exception as e:
							print(f"{img_src} 버튼 탐색 실패: {e}")

					for btn in download_buttons:
						initial_files = set(os.listdir(download_directory))
						driver.execute_script("arguments[0].click();", btn)
						WebDriverWait(driver, 15).until(
							lambda d: len(os.listdir(download_directory)) > len(initial_files)
						)
						wait_for_download_complete(30)

					upload_files_to_r2(download_directory, target_prefix, uploaded_files, files_dict)
					return {
						"success": True,
						"message": f"{len(uploaded_files)}개의 사진을 등록했습니다.",
						"files": uploaded_files
					}, files_dict

				except Exception as e:
					return {
						"success": False,
						"message": f"처리 중 오류 발생: {str(e)}",
						"files": []
					}, {}

			case 3:  # Monomansion
				button_texts = ["Photo Download", "Video Download"]
				try:
					try:
						expired_message = "다운로드 기간이 만료되었습니다"
						expired_element = WebDriverWait(driver, 5).until(
							EC.presence_of_element_located((By.XPATH, f"//p[contains(text(), '{expired_message}')]"))
							)
						return {
							"success": False,
							"message": "다운로드 기간이 만료되었습니다.",
							"files": []
							}, {}
					except TimeoutException:
						pass
					except Exception as e:
						print(f"만료 확인 오류: {e}")

					for text in button_texts:
						try:
							initial_files = set(os.listdir(download_directory))
							a = WebDriverWait(driver, 10).until(
								EC.presence_of_element_located((By.XPATH, f"//a[text()='{text}']"))
								)
							driver.execute_script("arguments[0].click();", a)
							wait_for_download_complete()
						except Exception as e:
							print(f"{text} 처리 실패: {e}")

					upload_files_to_r2(download_directory, target_prefix, uploaded_files, files_dict)
					return {
						"success": True,
						"message": f"{len(uploaded_files)}개의 사진을 등록했습니다.",
						"files": uploaded_files
						}, files_dict

				except Exception as e:
					return {
						"success": False,
						"message": f"처리 중 오류 발생: {str(e)}",
						"files": []
						}, {}
			case 4:  # PHOTOISM
				button_texts = ["사진 다운로드", "영상 다운로드"]
				try:
					try:
						expired_message = "다운로드 기간이 만료되었습니다"
						expired_element = WebDriverWait(driver, 5).until(
							EC.presence_of_element_located((By.XPATH, f"//p[contains(text(), '{expired_message}')]"))
							)
						return {
							"success": False,
							"message": "다운로드 기간이 만료되었습니다.",
							"files": []
							}, {}
					except TimeoutException:
						pass
					except Exception as e:
						print(f"만료 확인 오류: {e}")

					for text in button_texts:
						try:
							initial_files = set(os.listdir(download_directory))
							a = WebDriverWait(driver, 10).until(
								EC.presence_of_element_located((By.XPATH, f"//button[.//div[contains(text(), '{text}')]]"))
							)
							driver.execute_script("arguments[0].click();", a)
							wait_for_download_complete()
						except Exception as e:
							print(f"{text} 처리 실패: {e}")

					upload_files_to_r2(download_directory, target_prefix, uploaded_files, files_dict)
					return {
						"success": True,
						"message": f"{len(uploaded_files)}개의 사진을 등록했습니다.",
						"files": uploaded_files
						}, files_dict

				except Exception as e:
					return {
						"success": False,
						"message": f"처리 중 오류 발생: {str(e)}",
						"files": []
						}, {}
	finally:
		driver.quit()
		for file in os.listdir(download_directory):
			os.remove(os.path.join(download_directory, file))
		os.rmdir(download_directory)
