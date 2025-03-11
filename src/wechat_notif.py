from wxauto import WeChat
import time

wx = WeChat()

# 给文件传输助手发送消息
listen_list = [
    '刘易千',
    '韩仪',
    'Five guys👻👻',
    '沟通无限'
]

# 调用AddListenChat方法添加监听对象，其中可选参数savepic为是否保存新消息图片
for i in listen_list:
    wx.AddListenChat(who=i, savepic=False)

# 最后调用GetListenMessage方法，实现消息监听，收到消息类型为friend的消息之后，调用SendMsg方法回复消息
# 持续监听消息，并且收到消息后回复“收到”
wait = 60  # 设置1秒查看一次是否有新消息
while True:
    msgs = wx.GetListenMessage()
    for chat in msgs:
        who = chat.who              # 获取聊天窗口名（人或群名）
        one_msgs = msgs.get(chat)   # 获取消息内容
        # 回复收到
        for msg in one_msgs:
            msgtype = msg.type       # 获取消息类型
            content = msg.content    # 获取消息内容，字符串类型的消息内容
            print(f'【{who}】：{content}')
        # ===================================================
        # 处理消息逻辑（如果有）
        # 
        # 处理消息内容的逻辑每个人都不同，按自己想法写就好了，这里不写了
        # 
        # ===================================================
        
        
            if msgtype == 'friend':
                chat.SendMsg('收到信息，这是来自python wxauto的一条自动回复')  # 回复收到
    time.sleep(wait)


# wx.SendMsg('或者周一上完课？', 'Five guys👻👻')