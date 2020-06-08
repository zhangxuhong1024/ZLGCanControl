# coding:utf-8
import sys
sys.path.append(r'..')  #ControlCAN库所在目录
from ControlCAN import VCI,CanObj,ZlgCan

if __name__ == "__main__":
    # 把USBCAN_2E_U的通道0和通道1连在一起,可以直接运行这段代码哟.
    print ('---start---')
    zlg = ZlgCan(VCI.USBCAN_2E_U, 0)    # 创建接口类
    zlg.OpenDevice()                    # 打开设备
    zlg.StartCan("500K",Chx=0)          # 开启CAN通讯通道
    zlg.StartCan("500K",Chx=1)
    msgs = (CanObj*10)()
    msgs[0].Load(0x123,(1,2,3,4,5,6,7,8))
    msgs[1].Load(0x123,(1,2,3,4,5,6))
    msgs[2].Load(0x12345678,(1,2,3,4,5,6,7,8),Ext=1)
    msgs[3].Load(0x12345678,(1,2,3,4,5,6),Ext=1)
    msgs[4].Load(0x12345678,(1,2,3,4,5,6,7,8,9,10,11,12),Ext=1)
    zlg.Send(msgs,Chx=0)               # 通道0发送报文
    count = 0
    while(count<8):
        num = zlg.Recv(Chx=1)          # 通道1接收报文
        if num!=0:
            count += num
            for i in range(num):
                print(zlg.ReceiveBuffer[i])
    zlg.CloseDevice()
    print ('---end---')
