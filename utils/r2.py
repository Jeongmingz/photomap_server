from typing import Dict

import boto3
import os
from botocore.config import Config
from selenium.common import TimeoutException

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from botocore.exceptions import ClientError

from accounts.models import User
from photo.models import Photo, PhotoBrand
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

def four_cut_photo_qr_download(site_id: int, url: str, id: str, user: User) -> Dict[str, any]:
	uploaded_files = list()
	files_dict = dict()

	userid = user.pk
	# 다운로드 완료 감지 함수 추가
	def wait_for_download_complete(timeout=30):
		def check_temp_files(driver):
			return all(not f.endswith('.crdownload') for f in os.listdir(download_directory))

		WebDriverWait(driver, timeout).until(
			lambda x: check_temp_files(x)
			)


	# 기본 값 처리
	# R2 버킷 설정
	bucket_name = return_env_value("CLOUDFLARE_R2_BUCKET_NAME")
	target_prefix = f"4cut/{userid}/{site_id}/{id}/"


	# 다운로드 및 업로드 프로세스
	download_directory = f"/tmp/{site_id}_{id}_downloads"
	os.makedirs(download_directory, exist_ok=True)

	# Chrome 옵션 설정
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
	match site_id:
		case 1:  #PHOTOGARY,
			try:
				WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.ID, "root"))
					)
				try:
					expired_message = "다운 가능한 기간이 만료되었습니다"
					try:
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

				button_texts = ["사진 다운", "영상 다운", "타임랩스 다운"]

				for text in button_texts:
					try:
						initial_files = set(os.listdir(download_directory))
						btn = WebDriverWait(driver, 10).until(
							EC.presence_of_element_located((By.XPATH, f"//button[.//span[text()='{text}']]"))
							)
						driver.execute_script("arguments[0].click();", btn)
						WebDriverWait(driver, 15).until(
							lambda d: len(os.listdir(download_directory)) > len(initial_files)
							)

						# 2. 다운로드 완료까지 대기 (최대 30초)
						wait_for_download_complete(30)

					except Exception as e:
						print(f"{text} 처리 실패: {e}")

				# R2 업로드
				admin_r2 = return_admin_r2_client()

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
							uploaded_files.append(f"{return_env_value('CLOUDFLARE_R2_PUBLIC_URL')}/{object_name}")
					except Exception as e:
						print(f"파일 업로드 실패: {e}")

				# 업로드 완료 표시
				admin_r2.put_object(
					Bucket=bucket_name,
					Key=f"{target_prefix}_SUCCESS",
					Body=b''
					)

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
				# 리소스 정리
				driver.quit()
				for file in os.listdir(download_directory):
					os.remove(os.path.join(download_directory, file))
				os.rmdir(download_directory)
		case 2:  #PHOTOLAP+
			try:
				WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.TAG_NAME, "body"))
					)

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

				admin_r2 = return_admin_r2_client()

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
							uploaded_files.append(f"{return_env_value('CLOUDFLARE_R2_PUBLIC_URL')}/{object_name}")
					except Exception as e:
						print(f"파일 업로드 실패: {e}")

				# 업로드 완료 표시
				admin_r2.put_object(
					Bucket=bucket_name,
					Key=f"{target_prefix}_SUCCESS",
					Body=b''
					)

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
				# 리소스 정리
				driver.quit()
				for file in os.listdir(download_directory):
					os.remove(os.path.join(download_directory, file))
				os.rmdir(download_directory)

				files_dict['video'] = list()
				for file in uploaded_files:
					if file.split('.')[-1].lower() in IMAGE_EXTENSIONS:
						files_dict['image'] = file
					elif file.split('.')[-1].lower() in VIDEO_EXTENSIONS:
						files_dict['video'].append(file)
				print(files_dict)
				print(uploaded_files)

