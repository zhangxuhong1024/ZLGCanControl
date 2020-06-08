# coding:utf-8
import sys
import threading
import time
sys.path.append(r'..')  #ControlCAN库所在目录
from ControlCAN import VCI,CanObj,ZlgCan


import logging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(message)s')

def SendMsg(zlg,msgs):
    while(True):
        zlg.Send(msgs,Chx=0)           # 通道0发送报文
        time.sleep(1)

if __name__ == "__main__":
    # 把USBCAN_2E_U的通道0和通道1连在一起,可以直接运行这段代码哟.
    print ('---start---')
    zlg = ZlgCan(VCI.USBCAN_2E_U, 0)    # 创建接口类
    zlg.OpenDevice()                    # 打开设备
    zlg.StartCan("250K",Chx=0)          # 开启CAN通讯通道
    zlg.StartCan("250K",Chx=1)
    msgs = (CanObj*3)()
    msgs[0].Load(0x123,(1,2,3,4,5,6,7,8))
    msgs[1].Load(0x13,(1,2,3,4,5,6,7,8))
    msgs[2].Load(0x12,(1,2,3,4,5,6,7,8))

    # Send
    t = threading.Thread(target=SendMsg, args=[zlg, msgs])
    t.start()
    # Recv
    while(True):
        num = zlg.Recv(Chx=1, Filter=lambda msg:msg.ID==0x123)          # 通道1接收报文
        for i in num:
            print(i)
    zlg.CloseDevice()
    print ('---end---')
