import pywhatkit
import time
import pyautogui

my_phone_number = '+16728665961'
to_phone_number = '+17786800983'

pywhatkit.sendwhatmsg_instantly(to_phone_number, "test message from python", wait_time=0)

# 添加显式的发送操作
time.sleep(5)  # 等待页面加载
pyautogui.press('enter')  # 模拟按下回车键发送消息
time.sleep(2)  # 等待发送完成