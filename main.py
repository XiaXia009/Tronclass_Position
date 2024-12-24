from ulearn import Ulearn
import asyncio

#23.70213663906112, 120.42895980953193
#經緯度請直接到google map, 對你想點名的地方點擊右鍵, 然後左鍵經緯度得以複製
username = "學號"
password = "密碼"

#僅登入
async def test_1():
    print("[start trying login]")
    message = await Ulearn(username, password, position=False)
    print(message)
    while message == "驗證碼錯誤":
        message = await Ulearn(username, password, position=False)
        print(message)

#登入跟點名
async def test_2():
    position = input("經緯度:")
    print("[start trying login and rollcall]")
    message = await Ulearn(username, password, position=position)
    print(message)
    while message == "驗證碼錯誤":
        message = await Ulearn(username, password, position=position)
        print(message)

asyncio.run(test_2())