# coding:utf-8
import sys
sys.path.append(r'..')  #ControlCAN库所在目录
from ControlCAN import VCI,CanObj,ZlgCan

if __name__ == "__main__":
    print ('---start---')
    zlg = ZlgCan(VCI.USBCAN_2E_U, 0)    # 创建接口类
    zlg.OpenDevice()                    # 打开设备
    zlg.StartCan("500K",Chx=0)          # 开启CAN通讯通道
    f = open('x.txt','w')
    count = 0
    while(1):                           # 接收报文并写入到文件中.
        num = zlg.Recv(Chx=0)
        if num!=0:
            count += num
            for i in range(num):
                f.write(zlg.ReceiveBuffer[i])
                f.write('\n')
            print (count)
        f.flush()
        if count>=100000 :
            break
    zlg.CloseDevice()
    f.close()
    print ('---end---')

