import json
import random
import cv2
import numpy as np
import pytesseract
import aiohttp
import base64
import os
from bs4 import BeautifulSoup

API = "https://ulearn.nfu.edu.tw"
URL = "https://identity.nfu.edu.tw/auth/realms/nfu/protocol/cas/login?service=https://ulearn.nfu.edu.tw/login"
Agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
#pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

if not os.path.exists('./userimg/'):
    os.makedirs('./userimg/')

async def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    adaptive_threshold = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 17, 7.5)
    kernel = np.ones((4, 3), np.uint8)
    dilated = cv2.dilate(adaptive_threshold, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    return eroded

async def codeImg(session):
    captcha_url = 'https://identity.nfu.edu.tw/auth/realms/nfu/captcha/code'
    async with session.get(captcha_url) as response:
        if response.status != 200:
            response.raise_for_status()
        data = await response.json()
        base64_data = data['image'].split(',')[1]
        img_data = base64.b64decode(base64_data)
        img_array = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img, data['key']

async def Logout(session):
    try:
        await session.get("https://ulearn.nfu.edu.tw/logout")
        await session.get("https://identity.nfu.edu.tw/auth/realms/nfu/protocol/cas/logout?service=https%3A//ulearn.nfu.edu.tw&locale=zh_TW")
    except:
        pass

async def Ulearn(username, password, position):
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, headers=Agent) as response:
            body = BeautifulSoup(await response.text(), 'html.parser')
            action_url = body.find('form', class_='form-signin form-login')['action']
            img, key = await codeImg(session)
            processed_img = await preprocess_image(img)
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            code = text.replace(" ", "").strip()

            login_pay = {
                'username': username,
                'password': password,
                'captchaCode': code,
                'captchaKey': key
            }

            async with session.post(action_url, data=login_pay, headers=Agent) as login_response:
                if login_response.status != 200:
                    return "登入失敗"

                response_body = BeautifulSoup(await login_response.text(), 'html.parser')
                logout_links = response_body.find_all('a', string="登出")
                ch_name = response_body.find('root-scope-variable', {'name': 'currentUserName'})
                
                try:
                    header_div = response_body.find('div', class_='header header-autocollapse wg-header')
                    if header_div is not None:
                        ng_init_content = header_div.get('ng-init', '')
                        start = ng_init_content.find("avatarSmallUrl = '") + len("avatarSmallUrl = '")
                        end = ng_init_content.find("';", start)
                        avatar_small_url = ng_init_content[start:end]
                        avatar_url = avatar_small_url.replace('?thumbnail=32x32', '?thumbnail=300x300')
                        async with session.get(avatar_url) as avatar_response:
                            img_data = await avatar_response.read()
                            img_path = f'./userimg/{username}.png'
                            with open(img_path, 'wb') as handler:
                                handler.write(img_data)
                    else:
                        img_path = None
                except:
                    img_path = None
                
                if logout_links:
                    if position == False:
                        await Logout(session)
                    elif isinstance(position, str):
                        latitude, longitude = position.replace(" ", "").split(",")
                        async with session.get(f"{API}/api/rollcalls?api_version=1.1.2") as rollcalls_response:
                            print(rollcalls_response)
                            rollcalls = await rollcalls_response.json()
                            try:
                                result = []
                                for rollcall in rollcalls["rollcalls"]:
                                    result.append({
                                        "course_title": rollcall["course_title"],
                                        "created_by_name": rollcall["created_by_name"],
                                        "rollcall_id": rollcall["rollcall_id"],
                                        "is_number": rollcall["is_number"],
                                        "source": rollcall["source"],
                                        "status": rollcall["status"]
                                    })
                                    class_id = rollcall["rollcall_id"]
                                answer_pay = {
                                    "speed": -1,
                                    "longitude": float(longitude),
                                    "latitude": float(latitude),
                                    "accuracy": 100,
                                    "heading": -1,
                                    "altitude": float(f"30.{''.join([str(random.randint(0, 9)) for _ in range(15)])}"),
                                    "altitudeAccuracy": float(f"1{random.randint(0, 9)}.{''.join([str(random.randint(0, 9)) for _ in range(15)])}"),
                                }
                                if not result:
                                    await Logout(session)
                                    return "暫無點名"
                            except:
                                await Logout(session)
                                return "意外錯誤"
                            
                            async with session.put(f"{API}/api/rollcall/{class_id}/answer?api_version=1.1.0", json=answer_pay, headers=Agent) as rollcall_response:
                                global CH_username
                                _rollcall = await rollcall_response.json()
                                await Logout(session)
                                CH_username = ch_name["value"]
                                if _rollcall['status'] == "on_call":
                                    return True, ch_name["value"]
                                else:
                                    return False, ch_name["value"]
                    
                    return ch_name["value"], img_path
                else:
                    info = response_body.find('span', {'style': 'color:red'})
                    if info:
                        message_content = info.get_text()
                        return message_content
                    else:
                        return "未知的錯誤"