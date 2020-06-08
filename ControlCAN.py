#!/usr/bin/python
#coding: utf-8

"""\
"""

__author__ = "北极的企鹅1024 <zhangxuhong1024@qq.com>"
__version__ = "V1.0.0"


import ctypes
from  ctypes import *
from enum import Enum,IntEnum,unique
import platform
from os import path
import logging


dll = None


class VCI (Enum):
    PCI5121      =  1
    PCI9810      =  2
    USBCAN1      =  3
    USBCAN2      =  4
    USBCAN2A     =  4
    PCI9820      =  5
    CAN232       =  6
    PCI5110      =  7
    CANLITE      =  8
    ISA9620      =  9
    ISA5420      =  10
    PC104CAN     =  11
    CANETUDP     =  12
    CANETE       =  12
    DNP9810      =  13
    PCI9840      =  14
    PC104CAN2    =  15
    PCI9820I     =  16
    CANETTCP     =  17
    PEC9920      =  18
    PCIE_9220    =  18
    PCI5010U     =  19
    USBCAN_E_U   =  20
    USBCAN_2E_U  =  21
    PCI5020U     =  22
    EG20T_CAN    =  23
    PCIE9221     =  24
    WIFICAN_TCP  =  25
    WIFICAN_UDP  =  26
    PCIe9120     =  27
    PCIe9110     =  28
    PCIe9140     =  29
    USBCAN_4E_U  =  31
    CANDTU_200UR =  32
    CANDTU_MINI  =  33
    USBCAN_8E_U  =  34
    CANREPLAY    =  35
    CANDTU_NET   =  36
    CANDTU_100UR =  37

_ErrStrMap =  {
        0          : "DLL无响应",
        0x0001     : "CAN控制器内部FIFO溢出",
        0x0002     : "CAN控制器错误报警",
        0x0004     : "CAN控制器消极错误",
        0x0008     : "CAN控制器仲裁丢失",
        0x0010     : "CAN控制器总线错误",
        0x0020     : "总线关闭错误",
        0x0040     : "CAN控制器内部BUFFER溢出",
        0x0100     : "设备已经打开",
        0x0200     : "打开设备错误",
        0x0400     : "设备没有打开",
        0x0800     : "缓冲区溢出",
        0x1000     : "此设备不存在",
        0x2000     : "装载动态库失败",
        0x4000     : "执行命令失败错误码",
        0x8000     : "内存不足",
        0x00010000 : "端口已经被打开",
        0x00020000 : "设备索引号已经被占用",
        0x00030000 : "SetReference或GetReference传递的RefType不存在",
        0x00030002 : "创建Socket失败",
        0x00030003 : "打开Socket的连接时失败，可能设备连接已经存在",
        0x00030004 : "设备没启动",
        0x00030005 : "设备无连接",
        0x00030006 : "只发送了部分的CAN帧",
        0x00030007 : "数据发得太快，Socket缓冲区满了"   }

class CanObj(Structure):
    _fields_ = [("ID", c_uint),
            ("TimeStamp", c_uint),
            ("TimeFlag", c_byte),
            ("SendType", c_byte),
            ("RemoteFlag", c_byte),#是否是远程帧
            ("ExternFlag", c_byte),#是否是扩展帧
            ("DataLen", c_ubyte),
            ("Data",  c_ubyte*8),
            ("Reserved", c_ubyte*3) ]

    def __str__(self):
        TimeStamp = self.TimeStamp
        if self.TimeFlag==0:
            TimeStamp = 0xFFFFFFFF
        datastr = ''
        for i in range(self.DataLen):
            datastr += format(self.Data[i],'02X')+" "
        ExternFlag = {0:'STD',1:'EXT'}.get(self.ExternFlag)
        s = 'TIME:0x{:<8x}, ID: {}-0x{:<8x},  DATA: {}'
        return s.format(TimeStamp, ExternFlag, self.ID, datastr)

    def Load(self,ID,Data,Ext=None,Remote=None):
        self.ID = ID
        Data = Data[:8]
        self.DataLen = len(Data)
        self.Data = tuple(Data)
        self.ExternFlag = {0:0,1:1}.get(Ext,0)
        self.RemoteFlag = {0:0,1:1}.get(Remote,0)

class _VCI_INIT_CONFIG(Structure):
    """ 初始化CAN的数据类型 """
    _fields_ = [("AccCode", c_ulong),
            ("AccMask", c_ulong),
            ("Reserved", c_ulong),
            ("Filter", c_ubyte),
            ("Timing0", c_ubyte),
            ("Timing1", c_ubyte),
            ("Mode", c_ubyte) ]

class _VCI_BOARD_INFO(Structure):
    """ZLGCAN系列接口卡信息的数据类型 """
    _fields_ = [ ("hw_Version", c_ushort),
            ("fw_Version", c_ushort),
            ("dr_Version", c_ushort),
            ("in_Version", c_ushort),
            ("irq_Num", c_ushort),
            ("can_Num", c_ubyte),
            ("str_Serial_Num", c_char*20),
            ("str_hw_Type", c_char*40),
            ("Reserved", c_ushort*4) ]

    def __str__(self):
        return '硬件版本号：%s,固件版本号：%s,驱动程序版本号：%s,接口库版本号：%s,中断号：%s,共有%s路CAN，序列号：%s,硬件类型：%s' % (
            self.hw_Version, self.fw_Version, self.dr_Version, self.in_Version, self.irq_Num, self.can_Num,
            self.str_Serial_Num, self.str_hw_Type)

class _VCI_ERR_INFO(Structure):
    _fields_ = [("ErrCode", c_uint),     # 是否为扩展帧
            ("Passive_ErrData", c_byte*3),
            ("ArLost_ErrData", c_byte) ]

class _VCI_FILTER_RECORD(Structure):
    """报文过滤记录"""
    _fields_ = [("ExtFrame", c_ulong),     # 是否为扩展帧
            ("Start", c_ulong),
            ("End", c_ulong) ]

class _VCI_AUTO_SEND_OBJ(Structure):
    """定时自动发送帧结构"""
    _fields_ = [("Enable", c_byte), # 使能本条报文 0:禁能 1:使能
            ("Index", c_byte),      # 报文编号     最大支持32条报文
            ("Interval", c_ulong),  # 定时发送时间 1ms为单位
            ("obj", CanObj) ]  # 报文

class ZlgCan (object):
    _DeviceType  = 0
    _DeviceIndex = 0
    _DeviceNet = {}
    BaudRate = None      # 波特率定义
    BoardInfo = None
    logger = None
    _ReceiveBuffer = None # 接收缓冲区

    def __init__(self, DeviceType, Index=None,Net=None,loggerName=None):
        # logging设置
        if isinstance(loggerName,str) or loggerName==None:
            self.logger = logging.getLogger(loggerName)
        else:
            raise Exception("loggerNome用于logging.getLogger,必须是字符串类型.")
        # dll初始化.
        global dll
        if dll==None:
            current_path = path.abspath(path.dirname(__file__))
            if (platform.architecture()[0]=='64bit'):
                p = path.join(current_path, "ControlCANx64\ControlCAN.dll")
            elif (platform.architecture()[0]=='32bit'):
                p = path.join(current_path, "ControlCANx86\ControlCAN.dll")
            else:
                p = '.' #无效文件路径
                self.logger.exception("未能识别当前Windows平台!")
            try:
                dll = ctypes.WinDLL(p)
            except:
                self.logger.exception("未能正确打开DLL文件!")
        # 其他参数初始化
        self._DeviceType  = DeviceType.value
        if Index not None:
            self._DeviceIndex = Index
        if Net not None:
            self._DeviceNet = Net
            pass
        self._ReceiveBuffer = (CanObj*100)()
        self.BaudRate= {
                "5k"    : {"BTR0_Nor":0xBF, "BTR1_Nor":0xFF, "BTR_2eu":0x1C01C1, "BTR_4eu":5000   },
                "10k"   : {"BTR0_Nor":0x31, "BTR1_Nor":0x1C, "BTR_2eu":0x1C00E0, "BTR_4eu":10000  },
                "20k"   : {"BTR0_Nor":0x18, "BTR1_Nor":0x1C, "BTR_2eu":0x1600B3, "BTR_4eu":20000  },
                "50k"   : {"BTR0_Nor":0x09, "BTR1_Nor":0x1C, "BTR_2eu":0x1C002C, "BTR_4eu":50000  },
                "100k"  : {"BTR0_Nor":0x04, "BTR1_Nor":0x1C, "BTR_2eu":0x160023, "BTR_4eu":100000 },
                "125k"  : {"BTR0_Nor":0x03, "BTR1_Nor":0x1C, "BTR_2eu":0x1C0011, "BTR_4eu":125000 },
                "250k"  : {"BTR0_Nor":0x01, "BTR1_Nor":0x1C, "BTR_2eu":0x1C0008, "BTR_4eu":250000 },
                "500k"  : {"BTR0_Nor":0x00, "BTR1_Nor":0x1C, "BTR_2eu":0x060007, "BTR_4eu":500000 },
                "800k"  : {"BTR0_Nor":0x00, "BTR1_Nor":0x16, "BTR_2eu":0x060004, "BTR_4eu":800000 },
                "1000k" : {"BTR0_Nor":0x00, "BTR1_Nor":0x14, "BTR_2eu":0x060003, "BTR_4eu":1000000} }

    def OpenDevice (self):
        rst = dll.VCI_OpenDevice(self._DeviceType, self._DeviceIndex, 0)
        if rst == 0:
            self.logger.warning("打开设备失败!")
            self._GetDLLErrCode(-1)
            return
        self.BoardInfo = _VCI_BOARD_INFO()
        rst = dll.VCI_ReadBoardInfo(self._DeviceType, self._DeviceIndex, byref(self.BoardInfo))
        if rst == 0:
            self.BoardInfo = None
            self.logger.warning("读取版本号失败!")
        else:
            self.logger.debug("成功打开CAN接口卡")

    def CloseDevice (self):
        rst = dll.VCI_CloseDevice(self._DeviceType, self._DeviceIndex, 0)
        if rst == 0:
            self.logger.warning("关闭设备失败!")
            self._GetDLLErrCode(-1)
        else:
            self.logger.debug("成功关闭CAN接口卡")

    def StartCan (self, Chx, BaudRate, Filter=None, mode=None):
        self.logger.debug("正在打开通道{},波特率为{}!".format(Chx,BaudRate))
        rst = None
        if mode==None:
            mode = 0
        if BaudRate.lower() not in self.BaudRate:
            self.logger.warning("配置波特率失败,请检查设置的波特率是否被支持!")
            s = "被支持的波特率有: "
            for i in self.BaudRate.keys():
                s += i+' '
            self.logger.warning(s)
            return
        SpcDevice1 = [VCI.PCI5010U, VCI.USBCAN_E_U, VCI.USBCAN_2E_U, VCI.PCI5020U]
        SpcDevice2 = [VCI.USBCAN_4E_U]
        SpcDevice3 = [VCI.CANDTU_200UR, VCI.CANDTU_MINI, VCI.CANDTU_NET, VCI.CANDTU_100UR]

        if self._DeviceType in [i.value for i in SpcDevice1]:
            baud = self.BaudRate.get(BaudRate.lower()).get("BTR_2eu")
            rst = dll.VCI_SetReference(self._DeviceType, self._DeviceIndex, Chx,0, byref(c_int(baud)))
            if rst == 0:
                self.logger.warning("配置波特率失败!")
                self._GetDLLErrCode(Chx)
                self.CloseDevice()
                return
        elif self._DeviceType in [i.value for i in SpcDevice2]:
            baud = self.BaudRate.get(BaudRate.lower()).get("BTR_4eu")
            rst = dll.VCI_SetReference(self._DeviceType, self._DeviceIndex, Chx,0, byref(c_int(baud)))
            if rst == 0:
                self._GetDLLErrCode(Chx)
                self.logger.warning("配置波特率失败!")
                self.CloseDevice()
                return
        elif self._DeviceType in [i.value for i in SpcDevice3]:
            self.logger.warning("设置有点小麻烦,手头又没有硬件可以测试.心情好了再做支持哈~~~!")
            return
        vci = _VCI_INIT_CONFIG()
        vci.AccCode = 0x00000000
        vci.AccMask = 0xffffffff
        vci.Filter = 1
        vci.Timing0 = self.BaudRate.get(BaudRate.lower()).get("BTR0_Nor")
        vci.Timing1 = self.BaudRate.get(BaudRate.lower()).get("BTR1_Nor")
        vci.Mode = mode
        rst = dll.VCI_InitCAN(self._DeviceType, self._DeviceIndex, Chx,byref(vci))
        if rst == 0:
            self.logger.warning("初始化CAN卡失败！")
            self._GetDLLErrCode(Chx)
            return
        rst = dll.VCI_StartCAN(self._DeviceType, self._DeviceIndex, Chx)
        if rst == 0:
            self.logger.warning("打开CAN失败！")
            self._GetDLLErrCode(Chx)
            return

    def StopCan (self, Chx):
        self.logger.debug("正在复位通道{}!".format(Chx))
        rst = dll.VCI_StartCAN(self._DeviceType, self._DeviceIndex, Chx)
        if rst == 0:
            self.logger.warning("复位CAN失败！")
            self._GetDLLErrCode(Chx)

    def Send(self, Chx, objs):
        """发送报文."""
        if isinstance(objs,CanObj):
            msgs = (CanObj*1)()
            msgs[0].Load(objs.ID,objs.Data,Ext=objs.ExternFlag)
        else:
            msgs = objs
        self.logger.debug("通道{},正在发送{}个报文!".format(Chx,len(msgs)))
        rst = dll.VCI_Transmit(self._DeviceType, self._DeviceIndex, Chx, byref(msgs), len(msgs))
        if rst == 0:
            self.logger.warning("通道{},发送报文失败！".format(Chx))
            self._GetDLLErrCode(Chx)

    def Recv(self, Chx, Filter=None, WaitTime=None):
        """读取报文,返回读取到的报文,没有读取到报文则返回空元组."""
        if Filter==None:
            Filter = lambda msg: True
        if WaitTime==None:
            WaitTime = 200
        RecvSize = dll.VCI_GetReceiveNum(self._DeviceType, self._DeviceIndex, Chx)
        if RecvSize==0:
            return tuple()
        rst = dll.VCI_Receive(self._DeviceType, self._DeviceIndex, Chx, \
                byref(self._ReceiveBuffer), len(self._ReceiveBuffer), WaitTime)
        if rst == 0xFFFFFFFF:
            self.logger.warning("通道{},接收报文失败！".format(Chx))
            self._GetDLLErrCode(Chx)
            return tuple()
        self.logger.debug("通道{},接收到{}个报文!".format(Chx,rst))
        return tuple(i for i in self._ReceiveBuffer[:rst] if Filter(i))

    def ClearRecvBuffer (self, Chx):
        self.logger.debug("通道{}, 正在清除发送缓存区!".format(Chx))
        rst = dll.VCI_ClearBuffer(self._DeviceType, self._DeviceIndex, Chx)
        if rst == 0:
            self.logger.warning("清除CAN缓存区失败!")
            self._GetDLLErrCode(Chx)

    def _GetDLLErrCode(self, Chx):
        err = _VCI_ERR_INFO()
        dll.VCI_ReadErrInfo(self._DeviceType, self._DeviceIndex, Chx, byref(err))
        s = "DLL故障码:{} - {}".format(hex(err.ErrCode), _ErrStrMap.get(err.ErrCode),"未知故障码")
        self.logger.warning(s)

    def GetReference(self, argType):
        pass

    def SetReference(self, argType **args):
        pass

    def __del__(self):
        self.CloseDevice()
