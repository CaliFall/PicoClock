import machine
from machine import Timer
from utime import sleep, sleep_ms
from ssd1306 import SSD1306_I2C
import ds3231
import sht30
import random
import framebuf
from math import *

'''
尽量优化程序
同时展现树莓派pico的全部实力

注释:
1-字符都是8x8大小,自定义小字符大小为3x5
2-屏幕左上角为(0,0),0号屏幕为主屏[128x64],1号屏幕为副屏[128x32]
3-eval与pc版python出入较大,尽量避免使用
4-当前涉及的技术:1)树莓派pico 2)OLED显示屏SSD1306 3)温度湿度传感器SHT-31 4)时钟元件DS3231
'''


class PicoClock:
    def __init__(self):
        self.sht30 = sht30.SHT30()  # 初始化温度湿度传感器
        self.init_i2c()  # 初始化i2c
        self.init_button()  # 初始化物理按钮
        self.setting_control(mode='read')  # 从文件读取设置
        self.init_pin()  # 初始化PIN
        self.init_var()  # 初始化全局变量
        self.init_icon()  # 定义符号
        self.fun_MainMenu()  # 进入主界面

    # 基础函数部分
    def init_i2c(self):
        # 定义0和1号i2c引脚
        sda_0 = machine.Pin(0)
        scl_0 = machine.Pin(1)
        sda_1 = machine.Pin(14)
        scl_1 = machine.Pin(15)

        # 定义0和1号i2c
        i2c_0 = machine.I2C(0, sda=sda_0, scl=scl_0, freq=400000)
        i2c_1 = machine.I2C(1, sda=sda_1, scl=scl_1, freq=400000)

        # 测试用,打印0和1号i2c检测到的设备地址
        print('i2c_0 addr:' + str(i2c_0.scan()))
        print('i2c_1 addr:' + str(i2c_1.scan()))

        # 定义oled显示屏
        self.oled_0 = SSD1306_I2C(128, 64, i2c_0, addr=0x3c)
        self.oled_1 = SSD1306_I2C(128, 32, i2c_1, addr=0x3c)

    def init_button(self):
        self.button_u = machine.Pin(3, machine.Pin.IN, machine.Pin.PULL_DOWN)
        self.button_d = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_DOWN)
        self.button_l = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_DOWN)
        self.button_r = machine.Pin(6, machine.Pin.IN, machine.Pin.PULL_DOWN)
        self.button_y = machine.Pin(7, machine.Pin.IN, machine.Pin.PULL_DOWN)
        self.button_n = machine.Pin(8, machine.Pin.IN, machine.Pin.PULL_DOWN)

    def init_switch(self):
        self.switch_fps = True
        self.switch_ShowSleepTime = True
        self.switch_ShowBootLogo = True

    def init_pin(self):
        self.inner_rgb = machine.Pin(29, machine.Pin.OUT)

    def init_var(self):
        self.is_init_fps = 0  # fps计数器是否初始化
        self.button_gap = 0  # 按钮防抖
        self.is_button_ready = 0  # 按钮是否准备就绪
        self.refresh_scale = 3  # 副屏幕刷新速度控制,是几就代表是主屏幕的几分之一
        self.sleep_time_learning = 0  # 可变的睡眠时间
        self.fps_limit = 10  # 帧率限制

    def init_icon(self):
        self.icon_dic = {'icon_little_a': ['010', '101', '111', '101', '101'],
                         'icon_little_b': ['110', '101', '110', '101', '110'],
                         'icon_little_c': ['011', '100', '100', '100', '011'],
                         'icon_little_d': ['110', '101', '101', '101', '110'],
                         'icon_little_e': ['111', '100', '111', '100', '111'],
                         'icon_little_f': ['111', '100', '111', '100', '100'],
                         'icon_little_g': ['111', '100', '101', '101', '111'],
                         'icon_little_h': ['101', '101', '111', '101', '101'],
                         'icon_little_i': ['111', '010', '010', '010', '111'],
                         'icon_little_j': ['011', '001', '001', '101', '111'],
                         'icon_little_k': ['101', '110', '100', '110', '101'],
                         'icon_little_l': ['100', '100', '100', '100', '111'],
                         'icon_little_m': ['101', '111', '101', '101', '101'],
                         'icon_little_n': ['000', '100', '111', '101', '101'],
                         'icon_little_o': ['111', '101', '101', '101', '111'],
                         'icon_little_p': ['110', '101', '110', '100', '100'],
                         'icon_little_q': ['011', '101', '011', '001', '001'],
                         'icon_little_r': ['110', '101', '110', '101', '101'],
                         'icon_little_s': ['011', '100', '011', '001', '110'],
                         'icon_little_t': ['111', '010', '010', '010', '010'],
                         'icon_little_u': ['101', '101', '101', '101', '111'],
                         'icon_little_v': ['101', '101', '101', '101', '010'],
                         'icon_little_w': ['101', '101', '101', '111', '101'],
                         'icon_little_x': ['101', '101', '010', '101', '101'],
                         'icon_little_y': ['101', '101', '011', '001', '011'],
                         'icon_little_z': ['111', '001', '010', '100', '111'],

                         'icon_little_0': ['010', '101', '101', '101', '010'],
                         'icon_little_1': ['110', '010', '010', '010', '111'],
                         'icon_little_2': ['111', '001', '111', '100', '111'],
                         'icon_little_3': ['110', '001', '011', '001', '110'],
                         'icon_little_4': ['101', '101', '111', '001', '001'],
                         'icon_little_5': ['111', '100', '110', '001', '110'],
                         'icon_little_6': ['010', '100', '111', '101', '011'],
                         'icon_little_7': ['111', '101', '001', '010', '010'],
                         'icon_little_8': ['010', '101', '010', '101', '010'],
                         'icon_little_9': ['010', '101', '011', '001', '010'],

                         'icon_little_ ': ['000', '000', '000', '000', '000'],
                         'icon_focus_now': ['010', '101'],

                         'icon_little_!': ['010', '010', '010', '000', '010'],
                         'icon_little_"': ['101', '101'],
                         'icon_little_%': ['101', '001', '010', '100', '101'],
                         'icon_little_&': ['010', '100', '010', '101', '011'],
                         'icon_little_\'': ['010', '010'],
                         'icon_little_(': ['001', '010', '010', '010', '001'],
                         'icon_little_)': ['100', '010', '010', '010', '100'],
                         'icon_little_*': ['000', '010', '111', '101', '000'],
                         'icon_little_+': ['000', '010', '111', '010', '000'],
                         'icon_little_,': ['000', '000', '000', '010', '100'],
                         'icon_little_-': ['000', '000', '111', '000', '000'],
                         'icon_little_.': ['000', '000', '000', '000', '010'],
                         'icon_little_/': ['001', '001', '010', '100', '100'],
                         'icon_little_:': ['000', '010', '000', '010', '000'],
                         'icon_little_;': ['000', '010', '000', '010', '100'],
                         'icon_little_<': ['000', '011', '100', '011', '000'],
                         'icon_little_=': ['000', '111', '000', '111', '000'],
                         'icon_little_>': ['000', '110', '001', '110', '000'],
                         'icon_little_?': ['111', '101', '011', '000', '010'],
                         'icon_little_[': ['011', '010', '010', '010', '011'],
                         'icon_little_\\': ['100', '100', '010', '001', '001'],
                         'icon_little_]': ['110', '010', '010', '010', '110'],
                         'icon_little_^': ['010', '101'],
                         'icon_little__': ['000', '000', '000', '000', '000'],
                         'icon_little_`': ['10', '01'],
                         'icon_little_{': ['001', '010', '110', '010', '001'],
                         'icon_little_|': ['01', '01', '01', '01', '01'],
                         'icon_little_}': ['100', '010', '011', '010', '100'],

                         'icon_°': ['111', '101', '111']}
        self.icon_dic_keys = list(self.icon_dic.keys())
        self.icon_dic_keys.sort()

    # 自定义绘制方法
    def draw_border(self, id=0):
        if id == 0:
            self.oled_0.rect(0, 0, 128, 64, 1)
        elif id == 1:
            self.oled_1.rect(0, 0, 128, 32, 1)

    def draw_vline(self, x, id=0, leng=0):
        if id == 0:
            if leng == 0:
                leng = 64
            self.oled_0.vline(x, int((64 - leng) / 2), leng, 1)
        elif id == 1:
            if leng == 0:
                leng = 32
            self.oled_1.vline(x, int((32 - leng) / 2), leng, 1)

    def draw_hline(self, y, id=0, leng=0):
        if id == 0:
            if leng == 0:
                leng = 128
            self.oled_0.hline(int((128 - leng) / 2), y, leng, 1)
        elif id == 1:
            if leng == 0:
                leng = 128
            self.oled_1.hline(int((128 - leng) / 2), y, leng, 1)

    def clear(self, id=0):
        if id == 0:
            self.oled_0.fill(0)
        elif id == 1:
            self.oled_1.fill(0)
        else:
            self.oled_0.fill(0)
            self.oled_1.fill(0)

    def show(self, id=0):
        if id == 0:
            self.oled_0.show()
        elif id == 1:
            self.oled_1.show()
        else:
            self.oled_0.show()
            self.oled_1.show()

    def draw_icon(self, lis, x0, y0, id=0):
        for y in range(len(lis)):
            for x in range(len(lis[y])):
                if lis[y][x] == '1' and id == 0:
                    self.oled_0.pixel(x0 + x, y0 + y, 1)
                elif lis[y][x] == '1' and id == 1:
                    self.oled_1.pixel(x0 + x, y0 + y, 1)

    # 自定义文本方法
    def text_l(self, text, y, border=3, id=0):
        text = str(text)
        if id == 0:
            self.oled_0.text(text, 0 + border, y)
        elif id == 1:
            self.oled_1.text(text, 0 + border, y)
        else:
            return 1

    def text_lc(self, text, y, border=3, id=0):
        text = str(text)
        leng = len(text) * 8
        if id == 0:
            self.oled_0.fill_rect(0 + border, y, leng, 8, 0)
        elif id == 1:
            self.oled_1.fill_rect(0 + border, y, leng, 8, 0)
        else:
            return 1

    def text_r(self, text, y, border=3, id=0):
        text = str(text)
        leng = len(text) * 8
        if id == 0:
            self.oled_0.text(text, 128 - border - leng, y)
        elif id == 1:
            self.oled_1.text(text, 128 - border - leng, y)
        else:
            return 1

    def text_rc(self, text, y, id=0):
        text = str(text)
        leng = len(text) * 8
        if id == 0:
            self.oled_0.fill_rect(128 - leng, y, leng, 8, 0)
        elif id == 1:
            self.oled_1.fill_rect(128 - leng, y, leng, 8, 0)
        else:
            return 1

    def text_m(self, text, y, id=0):
        text = str(text)
        leng = len(str(text)) * 8
        if id == 0:
            self.oled_0.text(text, int((128 - leng) / 2), y)
        elif id == 1:
            self.oled_1.text(text, int((128 - leng) / 2), y)
        else:
            return 1

    def text_mc(self, text, y, id=0):
        text = str(text)
        leng = len(str(text)) * 8
        if id == 0:
            self.oled_0.fill_rect(int((128 - leng) / 2), y, leng, 8, 0)
        elif id == 1:
            self.oled_1.fill_rect(int((128 - leng) / 2), y, leng, 8, 0)
        else:
            return 1

    def text_clear(self, x, y, length, height=8, id=0):
        if id == 0:
            self.oled_0.fill_rect(x, y, length, height, 0)
        if id == 1:
            self.oled_1.fill_rect(x, y, length, height, 0)

    def simple_bar(self, y, leng, index, id=0):
        text = '{' + index * '-' + '=' + (leng - index - 1) * '-' + '}'
        self.text_m(text, y, id=id)

    def text_little(self, text, x, y, id=0):
        text = str(text).lower()
        for i in range(len(text)):
            self.draw_icon(lis=self.icon_dic.get("icon_little_" + text[i]), x0=x + 4 * i, y0=y + 2, id=id)

    # 关键函数部分
    def button_sign(self):
        if self.button_u.value() == 1:
            self.sleep_button()
            if self.button_u.value() == 1:
                self.inner_rgb.value(1)
                return 'u'
        elif self.button_d.value() == 1:
            self.sleep_button()
            if self.button_d.value() == 1:
                self.inner_rgb.value(1)
                return 'd'
        elif self.button_l.value() == 1:
            self.sleep_button()
            if self.button_l.value() == 1:
                self.inner_rgb.value(1)
                return 'l'
        elif self.button_r.value() == 1:
            self.sleep_button()
            if self.button_r.value() == 1:
                self.inner_rgb.value(1)
                return 'r'
        elif self.button_y.value() == 1:
            self.sleep_button()
            if self.button_y.value() == 1:
                self.inner_rgb.value(1)
                return 'y'
        elif self.button_n.value() == 1:
            self.sleep_button()
            if self.button_n.value() == 1:
                self.inner_rgb.value(1)
                return 'n'

        else:
            self.inner_rgb.value(0)
            return 0

    def show_fps(self, s, id=0, switch=1):
        if self.is_init_fps == 0:
            self.sec_buffer = '0'  # 用于记录当前秒数
            self.frame_counter = 0  # 记帧器
            self.fps = 0  # 一秒帧数
            self.is_init_fps = 1

        if self.sec_buffer != s:
            self.sec_buffer = s
            self.fps = self.frame_counter
            self.frame_counter = 0
        else:
            self.frame_counter += 1

        if self.switch_fps and switch:
            leng = len(str(self.fps)) * 8 + 32  # 32=4*8
            if id == 0:
                self.text_clear(0, 0, length=leng)
                self.text_l("fps=" + str(self.fps), 0, border=0, id=0)

        if self.switch_ShowSleepTime and switch:
            leng = len(str(self.sleep_time_learning)) * 8 + 32
            self.text_clear(128 - leng, 0, leng)
            self.text_r("stl=" + str(self.sleep_time_learning), 0, border=0)

    def sleep_button(self):
        sleep_ms(self.button_gap)

    def fps_limiter(self, limit, frame_count=0, fps=60):
        if frame_count > limit + 1:
            self.sleep_time_learning += 1
        elif fps < limit - 1 and self.sleep_time_learning > 0:
            if random.randint(0, 1):  # 减缓延时下降速度
                self.sleep_time_learning -= 1
        sleep_ms(self.sleep_time_learning)

    def setting_control(self, mode):
        file_name = 'setting.ini'
        # 读
        if mode == 'read':
            try:
                with open(file_name, 'r') as f:
                    self.setting_dic = eval(f.read())
                # 从字典读取设置
                self.switch_fps = self.setting_dic.get('Show FPS')
                self.switch_ShowSleepTime = self.setting_dic.get('Show STL')
                self.switch_ShowBootLogo = self.setting_dic.get('Boot Logo')
                print(file_name + " Loaded")
                print("setting_dic=" + str(self.setting_dic))
            except Exception:
                print("Load Failed")
                self.init_switch()  # 初始化设置
                self.setting_control(mode='initwrite')
        # 初始化写
        elif mode == 'initwrite':
            try:
                # 初始化设置字典
                self.setting_dic = {'Show FPS': self.switch_fps,
                                    'Show STL': self.switch_ShowSleepTime,
                                    'Boot Logo': self.switch_ShowBootLogo}
                # 写入文件
                with open(file_name, 'w') as f:
                    f.write(str(self.setting_dic))
                print(file_name + " Initialized")
            except OSError:
                #如果出错
                self.error_window('OSError')
        # 覆写设置
        elif mode == 'overwrite':
            try:
                # 写入文件
                with open(file_name, 'w') as f:
                    f.write(str(self.setting_dic))
                print(file_name + " Updated")
            except OSError:
                #如果出错
                self.error_window('OSError')
        # 更新(先写再读)
        elif mode == 'update':
            self.setting_control(mode='overwrite')
            self.setting_control(mode='read')
            print("Setting Updated And Loaded")

    def shot_timer(self, _):
        self.timer_cond = 1

    # 重要功能部分 # 主界面
    def fun_MainMenu(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        week_lis = ["Sun", "Mon", "Tues", "Wed", "Thur", "Fri", "Sat"]  # 星期名

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        if self.switch_ShowBootLogo:
            self.fun_BootLogo()

        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                if ButtonSign == 'y':
                    self.fun_SubMenu()
            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            # self.draw_border()  # 绘制边界

            # 绘制时间
            self.text_m("%02d:%02d:%02d" % (self.TimeDS3231[2], self.TimeDS3231[1], self.TimeDS3231[0]), 18)
            #  绘制日期
            self.text_m("20%d/%02d/%02d" % (self.TimeDS3231[6], self.TimeDS3231[5], self.TimeDS3231[4]), 28)
            #  绘制星期
            self.text_m("%s" % (week_lis[self.TimeDS3231[3]]), 38)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps

            self.show()  # 绘制所有

            ###副屏幕内容###
            if self.frame_counter % self.refresh_scale == 0:
                self.clear(id=1)  # 清除所有
                self.text_little("Hello World", 0, 0, id=1)
                self.show(id=1)  # 绘制所有

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 等待

    # 细分菜单
    def fun_SubMenu(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]

        # 功能代号
        SHT31 = 'Temp & RH'
        BaseConverter = 'Base Converter'
        REPL = 'EZ REPL'
        IconTest = 'Icon Test'
        fx = 'fx'
        Setting = 'Setting'
        UnitConverter = 'Unit Converter'

        index_lis = [SHT31, BaseConverter, UnitConverter, REPL, Setting]
        index_lis_len = len(index_lis)
        index_now = 0

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                # 确认按钮
                if ButtonSign == 'y':
                    if index_lis[index_now] == 'Main Menu':
                        return 0
                    elif index_lis[index_now] == SHT31:
                        self.fun_SHT31()
                    elif index_lis[index_now] == BaseConverter:
                        self.fun_BaseConverter()
                    elif index_lis[index_now] == REPL:
                        self.fun_REPL()
                    elif index_lis[index_now] == Setting:
                        self.fun_Setting()
                    elif index_lis[index_now] == UnitConverter:
                        self.fun_UnitConverter()

                    # test
                    elif index_lis[index_now] == fx:
                        self.fx_window()
                    elif index_lis[index_now] == IconTest:
                        self.fun_IconTest()

                # 左按钮
                if ButtonSign == 'l':
                    if index_now == 0:
                        index_now = index_lis_len - 1
                    else:
                        index_now -= 1
                # 右按钮
                if ButtonSign == 'r':
                    if index_now == index_lis_len - 1:
                        index_now = 0
                    else:
                        index_now += 1
                # 返回按钮
                if ButtonSign == 'n':
                    return 0

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            self.draw_border()  # 绘制边界

            self.text_m(index_lis[index_now], 28)  # 显示当前选中的功能名
            self.simple_bar(38, index_lis_len, index_now, id=0)  # 显示一个条,告诉用户当前位置

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###
            self.clear(id=1)  # 清除所有

            self.text_m("%02d:%02d:%02d" % (self.TimeDS3231[2], self.TimeDS3231[1], self.TimeDS3231[0]), 0, id=1)

            self.show(id=1)  # 绘制所有

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 等待

    # 错误弹窗,会在屏幕上打印参数code
    def error_window(self, code='null'):
        self.is_button_ready = 0

        width = 100
        height = 50
        self.oled_0.fill_rect(64 - int(width / 2), 32 - int(height / 2), width, height, 0)
        self.oled_0.rect(64 - int(width / 2), 32 - int(height / 2), width, height, 1)
        self.text_m("!ERROR!", 18)
        self.text_m(code, 28)
        self.text_m("[PRESS]", 38)
        self.show()
        while True:
            ButtonSign = self.button_sign()
            if ButtonSign != 0 and self.is_button_ready:
                self.is_button_ready = 0
                return 0
            elif ButtonSign == 0 and not self.is_button_ready:
                self.is_button_ready = 1
            else:
                sleep_ms(50)

    # 普通弹窗
    def jump_window(self, title='!Notice!', code='null'):
        self.is_button_ready = 0

        width = 100
        height = 50
        self.oled_0.fill_rect(64 - int(width / 2), 32 - int(height / 2), width, height, 0)
        self.oled_0.rect(64 - int(width / 2), 32 - int(height / 2), width, height, 1)
        self.text_m(title, 18)
        self.text_m(code, 28)
        self.text_m("[PRESS]", 38)
        self.show()
        while True:
            ButtonSign = self.button_sign()
            if ButtonSign != 0 and self.is_button_ready:
                self.is_button_ready = 0
                return 0
            elif ButtonSign == 0 and not self.is_button_ready:
                self.is_button_ready = 1
            else:
                sleep_ms(50)

    # 输入界面,会返回用户输入的东西
    def input_keyboard(self, msg_already=''):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器
        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        line_lis_button = ['OK', 'RE', '<-', '_', '->', 'BS']
        line_lis_0 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', 'CAP']
        line_lis_1 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', '-', 'CAP']
        line_lis_2 = ['K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', '*', 'CAP']
        line_lis_3 = ['U', 'V', 'W', 'X', 'Y', 'Z', ':', '$', '%', '&', '/', 'FX']
        line_lis_4 = ['(', '[', '{', '<', '>', '!', '=', ',', '.', '\'', '\"', 'FX']
        line_lis_all = [line_lis_button, line_lis_0, line_lis_1, line_lis_2, line_lis_3, line_lis_4]

        # 初始化大小写
        try:
            if self.input_cap_mode == 'a':
                pass
        except Exception:
            self.input_cap_mode = 'a'
        # 初始同步列表里字母大小写
        for lis in line_lis_all:
            for x in range(len(lis)):
                if len(lis[x]) == 1 and self.input_cap_mode == 'A':
                    lis[x] = lis[x].upper()
                elif len(lis[x]) == 1 and self.input_cap_mode == 'a':
                    lis[x] = lis[x].lower()

        msg_input = msg_already  # 用户输入的信息
        focus_input = 0  # 输入指针位置
        focus_select_x = 0  # 指针x轴
        focus_select_y = 1  # 指针y轴
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间
            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                # 确认键
                if ButtonSign == 'y':
                    focus_now = line_lis_all[focus_select_y][focus_select_x]
                    # 确认
                    if focus_now == 'OK':
                        return str(msg_input)
                    # 重置
                    elif focus_now == 'RE':
                        msg_input = ''
                        focus_input = 0
                    # 空格
                    elif focus_now == '_':
                        msg_input += ' '
                        focus_input += 1
                    # 左移
                    elif focus_now == '<-' and focus_input != 0:
                        focus_input -= 1
                    # 右移
                    elif focus_now == '->' and focus_input != len(str(msg_input)):
                        focus_input += 1
                    # 退格
                    elif focus_now == 'BS' and msg_input != '':
                        msg_input = list(msg_input)
                        if focus_input != 0:
                            del msg_input[focus_input - 1]
                        msg_input = ''.join(msg_input)
                        if focus_input != 0:
                            focus_input -= 1
                    # CAP
                    elif focus_now == 'CAP':
                        for lis in line_lis_all:
                            for x in range(len(lis)):
                                if len(lis[x]) == 1 and self.input_cap_mode == 'A':
                                    lis[x] = lis[x].lower()
                                elif len(lis[x]) == 1 and self.input_cap_mode == 'a':
                                    lis[x] = lis[x].upper()
                        if self.input_cap_mode == 'A':
                            self.input_cap_mode = 'a'
                        elif self.input_cap_mode == 'a':
                            self.input_cap_mode = 'A'

                    # FX
                    elif focus_now == 'FX':
                        fx = self.fx_window()
                        if fx != 'null':
                            msg_input = list(msg_input)
                            msg_input.insert(focus_input, fx)
                            msg_input = ''.join(msg_input)
                            focus_input += len(fx) - 1

                    # 一般输入
                    else:
                        msg_input = list(msg_input)
                        msg_input.insert(focus_input, focus_now)
                        msg_input = ''.join(msg_input)
                        focus_input += 1

                        # 括号
                        if focus_now == '(':
                            msg_input = list(msg_input)
                            msg_input.insert(focus_input, ')')
                            msg_input = ''.join(msg_input)
                        elif focus_now == '[':
                            msg_input = list(msg_input)
                            msg_input.insert(focus_input, ']')
                            msg_input = ''.join(msg_input)
                        elif focus_now == '{':
                            msg_input = list(msg_input)
                            msg_input.insert(focus_input, '}')
                            msg_input = ''.join(msg_input)

                # 返回键
                elif ButtonSign == 'n':
                    return 'null'
                # 左键
                elif ButtonSign == 'l':
                    if focus_select_x == 0:
                        focus_select_x = len(line_lis_all[focus_select_y]) - 1
                    else:
                        focus_select_x -= 1
                # 右键
                elif ButtonSign == 'r':
                    if focus_select_x == len(line_lis_all[focus_select_y]) - 1:
                        focus_select_x = 0
                    else:
                        focus_select_x += 1
                # 上键
                elif ButtonSign == 'u':
                    if line_lis_all[focus_select_y][focus_select_x] == 'FX':
                        focus_select_y = 1
                    else:
                        if focus_select_y == 0:
                            focus_select_y = len(line_lis_all) - 1
                        else:
                            focus_select_y -= 1
                    if focus_select_x > len(line_lis_all[focus_select_y]) - 1:
                        focus_select_x = len(line_lis_all[focus_select_y]) - 1
                # 下键
                elif ButtonSign == 'd':
                    if line_lis_all[focus_select_y][focus_select_x] == 'CAP':
                        focus_select_y = 5
                    else:
                        if focus_select_y == len(line_lis_all) - 1:
                            focus_select_y = 0
                        else:
                            focus_select_y += 1
                    if focus_select_x > len(line_lis_all[focus_select_y]) - 1:
                        focus_select_x = len(line_lis_all[focus_select_y]) - 1

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有

            # 打印可输入字符
            for y in range(len(line_lis_all) - 1):
                for x in range(len(line_lis_all[y + 1]) - 1):
                    self.oled_0.text(line_lis_all[y + 1][x], 4 + x * 10, 8 + y * 11)
            # 打印CAP
            if self.input_cap_mode == 'A':
                self.oled_0.text("C", 118, 11)
                self.oled_0.text("A", 118, 19)
                self.oled_0.text("P", 118, 27)
            elif self.input_cap_mode == 'a':
                self.oled_0.text("c", 118, 11)
                self.oled_0.text("a", 118, 19)
                self.oled_0.text("p", 118, 27)
            # 打印FX
            self.text_little('fx', 119, 47)

            # 绘制主屏指针框
            if focus_select_y != 0 and focus_select_x != len(line_lis_all[focus_select_y]) - 1:
                self.oled_0.rect(4 + focus_select_x * 10 - 1, 8 + (focus_select_y - 1) * 11 - 2, 10, 11, 1)
            elif line_lis_all[focus_select_y][focus_select_x] == 'CAP':
                self.oled_0.rect(117, 9, 10, 27, 1)
            elif line_lis_all[focus_select_y][focus_select_x] == 'FX':
                self.oled_0.rect(117, 45, 11, 9, 1)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###
            self.clear(id=1)  # 清除所有

            self.oled_1.text(msg_input, 4, 1)
            self.draw_hline(10, id=1, leng=120)
            self.oled_1.text("OK", 2, 16)
            self.oled_1.text("RE", 21, 16)
            self.oled_1.text("<", 40, 16)
            self.oled_1.text("-", 46, 16)
            self.oled_1.text("_", 57, 14)
            self.oled_1.text("-", 68, 17)
            self.oled_1.text(">", 74, 17)
            self.oled_1.text("BS", 85, 17)

            # 绘制副屏指针框
            if focus_select_y == 0:
                if focus_select_x == 0:
                    self.oled_1.rect(2 - 1, 16 - 2, 2 * 8 + 2, 11, 1)
                elif focus_select_x == 1:
                    self.oled_1.rect(21 - 1, 16 - 2, 2 * 8 + 2, 11, 1)
                elif focus_select_x == 2:
                    self.oled_1.rect(40 - 1, 16 - 2, 2 * 8 + 1, 11, 1)
                elif focus_select_x == 3:
                    self.oled_1.rect(57 - 1, 16 - 2, 1 * 8 + 1, 11, 1)
                elif focus_select_x == 4:
                    self.oled_1.rect(68 - 1, 16 - 1, 2 * 8 + 1, 11, 1)
                elif focus_select_x == 5:
                    self.oled_1.rect(85 - 1, 16 - 1, 2 * 8 + 2, 11, 1)

            # 绘制指针
            self.draw_icon(self.icon_dic.get("icon_focus_now"), 2 + 8 * focus_input, 11, id=1)

            self.show(id=1)  # 绘制所有

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 函数选择窗口
    def fx_window(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        fx_lis = ['acos()', 'acosh()', 'asin()', 'asinh()', 'atan()', 'atanh()',
                  'cos()', 'cosh()', 'degrees()', 'dist()', 'abs()', 'gcd()',
                  'log()', 'log10()', 'pow()', 'radians()', 'sin()', 'sinh()',
                  'sqrt()', 'tan()', 'tanh()']
        fx_lis.sort()
        focus_y = 0

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                if ButtonSign == 'n':
                    return 'null'
                elif ButtonSign == 'y':
                    return fx_lis[focus_y]
                elif ButtonSign == 'u':
                    if focus_y == 0:
                        focus_y = len(fx_lis) - 1
                    else:
                        focus_y -= 1
                elif ButtonSign == 'd':
                    if focus_y == len(fx_lis) - 1:
                        focus_y = 0
                    else:
                        focus_y += 1
                elif ButtonSign == 'l':
                    if focus_y - 5 < 0:
                        focus_y = focus_y + len(fx_lis) - 5
                    else:
                        focus_y -= 5
                elif ButtonSign == 'r':
                    if focus_y + 5 > len(fx_lis) - 1:
                        focus_y = focus_y - len(fx_lis) + 5
                    else:
                        focus_y += 5

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            self.oled_0.text('F(x)=', 3, 3)  # 提示
            self.oled_0.text('->', 3, 32)  # 箭头
            # 打印函数
            for x in range(5):
                if focus_y + x - 2 <= len(fx_lis) - 1:
                    self.oled_0.text(fx_lis[focus_y + x - 2], 20, 32 + (x - 2) * 8)
                else:
                    self.oled_0.text(fx_lis[focus_y + x - 2 - len(fx_lis)], 20, 32 + (x - 2) * 8)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 分支功能部分 # 子界面模板
    def fun_model(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            # self.draw_border()  # 绘制边界

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 温度/湿度传感器SHT-31
    def fun_SHT31(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        sht31 = sht30.SHT30()

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                if ButtonSign == 'n':
                    return 0

            elif ButtonSign == 0 and not self.is_button_ready:
                self.is_button_ready = 1

            ###主屏幕内容###
            if self.frame_counter == 0:
                self.clear()  # 清除所有
                self.draw_border()  # 绘制边界

                sht_lis = sht31.measure_int()
                t = ("%2d.%2d" % (sht_lis[0], sht_lis[1]))
                h = ("%2d.%2d" % (sht_lis[2], sht_lis[3]))

                self.oled_0.text("Temp= " + str(t) + " C", 10, 18)
                self.oled_0.text("RH= " + str(h) + " %", 26, 28)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.draw_icon(self.icon_dic.get('icon_°'), 103, 18)
            self.show()  # 绘制所有

            ###副屏幕内容###
            if self.frame_counter == 0:
                self.clear(id=1)  # 清除所有

                # 显示一个简易时钟
                self.text_m("%02d:%02d:%02d" % (self.TimeDS3231[2], self.TimeDS3231[1], self.TimeDS3231[0]), 0, id=1)

                self.show(id=1)  # 绘制所有

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 进制转换器
    def fun_BaseConverter(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器
        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        focus_lis = ['HEX', 'DEC', 'OCT', 'BIN', 'RESET']
        focus_lis_len = len(focus_lis)
        focus_now = 0

        var_BASE = 0  # BASE变量,本质上是十进制
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                # 返回按钮
                if ButtonSign == 'n':
                    return 0
                # 左或上按钮
                if ButtonSign == 'l' or ButtonSign == 'u':
                    if focus_now == 0:
                        focus_now = focus_lis_len - 1
                    else:
                        focus_now -= 1
                # 右或下按钮
                if ButtonSign == 'r' or ButtonSign == 'd':
                    if focus_now == focus_lis_len - 1:
                        focus_now = 0
                    else:
                        focus_now += 1
                # 确定按钮
                if ButtonSign == 'y':
                    try:
                        if focus_lis[focus_now] == 'HEX':
                            temp = str(self.input_keyboard())
                            if temp != 'null':
                                var_BASE = int(temp, 16)
                        elif focus_lis[focus_now] == 'DEC':
                            temp = str(self.input_keyboard())
                            if temp != 'null':
                                var_BASE = int(temp)
                        elif focus_lis[focus_now] == 'OCT':
                            temp = str(self.input_keyboard())
                            if temp != 'null':
                                var_BASE = int(temp, 8)
                        elif focus_lis[focus_now] == 'BIN':
                            temp = str(self.input_keyboard())
                            if temp != 'null':
                                var_BASE = int(temp, 2)
                        elif focus_lis[focus_now] == 'RESET':
                            var_BASE = 0
                    except ValueError:
                        self.error_window("ValueError")

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            # 根据BASE计算其他进制
            var_HEX = hex(var_BASE)
            var_DEC = var_BASE
            var_OCT = oct(var_BASE)
            var_BIN = bin(var_BASE)

            ###主屏幕内容###
            self.clear()  # 清除所有
            self.draw_border()  # 绘制边界

            # HEX
            self.oled_0.text("HEX=", 3, 8)
            if len(str(var_HEX)[2:]) <= 10:
                self.oled_0.text(str(var_HEX)[2:], 3 + 35, 8)
            else:
                self.text_little(str(var_HEX)[2:], 3 + 35, 8 + 2)
            # DEC
            self.oled_0.text("DEC=", 3, 18)
            if len(str(var_DEC)) <= 10:
                self.oled_0.text(str(var_DEC), 3 + 35, 18)
            else:
                self.text_little(str(var_DEC), 3 + 35, 18 + 2)
            # OCT
            self.oled_0.text("OCT=", 3, 28)
            if len(str(var_OCT)[2:]) <= 10:
                self.oled_0.text(str(var_OCT)[2:], 3 + 35, 28)
            else:
                self.text_little(str(var_OCT)[2:], 3 + 35, 28 + 2)
            # BIN
            self.oled_0.text("BIN=", 3, 38)
            if len(str(var_BIN)[2:]) <= 10:
                self.oled_0.text(str(var_BIN)[2:], 3 + 35, 38)
            else:
                self.text_little(str(var_BIN)[2:], 3 + 35, 38 + 2)
            # RESET
            self.text_m("RESET", 48)

            if focus_now == 0:
                self.oled_0.rect(37, 6, 88, 11, 1)
            elif focus_now == 1:
                self.oled_0.rect(37, 16, 88, 11, 1)
            elif focus_now == 2:
                self.oled_0.rect(37, 26, 88, 11, 1)
            elif focus_now == 3:
                self.oled_0.rect(37, 36, 88, 11, 1)
            elif focus_now == 4:
                self.oled_0.rect(40, 46, 48, 11, 1)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###
            if self.frame_counter == 0:
                self.clear(id=1)  # 清除所有

                self.text_m("%02d:%02d:%02d" % (self.TimeDS3231[2], self.TimeDS3231[1], self.TimeDS3231[0]), 0, id=1)

                self.show(id=1)  # 绘制所有

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 测试自定义符号
    def fun_IconTest(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                if ButtonSign == 'n':
                    return 0

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有

            for i in range(len(self.icon_dic_keys)):
                self.draw_icon(self.icon_dic.get(self.icon_dic_keys[i]), (i % 30) * 4, (i // 30) * 6 + 20)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # REPL
    def fun_REPL(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        # 指令相关
        command = ''
        # 指针相关
        focus_now = 0
        focus_lis = ['input', 'OK', 'RE']
        # 历史记录
        history_lis = []

        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                # 确认键
                if ButtonSign == 'y':
                    # 输入框
                    if focus_lis[focus_now] == 'input':
                        temp = self.input_keyboard(msg_already=command)
                        focus_now = 1
                        if temp != 'null':
                            command = temp
                    # OK
                    elif focus_lis[focus_now] == 'OK' and command != '':
                        history_lis.insert(0, "   " + command)

                        try:
                            if command.startswith("print"):
                                command = command[6:-1]

                            eval_result = eval(command)
                            history_lis.insert(0, ">>>" + str(eval_result))
                        except SyntaxError:
                            history_lis.insert(0, ">>>" + "SyntaxError")
                        except NameError:
                            history_lis.insert(0, ">>>" + "NameError")

                        command = ''
                    # 重置
                    elif focus_lis[focus_now] == 'RE':
                        command = ''

                # 退出键
                elif ButtonSign == 'n':
                    return 0
                # 左键
                elif ButtonSign == 'l':
                    if focus_now == 0:
                        focus_now = len(focus_lis) - 1
                    else:
                        focus_now -= 1
                # 右键
                elif ButtonSign == 'r':
                    if focus_now == len(focus_lis) - 1:
                        focus_now = 0
                    else:
                        focus_now += 1

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            if self.frame_counter % self.refresh_scale == 0:
                self.clear(id=0)
                for i in range(len(history_lis)):
                    self.oled_0.text(history_lis[i], 0, 64 - 8 - i * 8)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show(id=0)

            ###副屏幕内容###
            # if self.frame_counter % self.refresh_scale == 0:
            if 1:
                self.clear(id=1)

                self.text_little(command, 4, 3, 1)
                self.oled_1.text("OK", 2, 16)
                self.oled_1.text("RE", 21, 16)

                if focus_lis[focus_now] == 'input':
                    self.draw_hline(10, id=1, leng=120)
                elif focus_lis[focus_now] == 'OK':
                    self.oled_1.rect(2 - 1, 16 - 2, 2 * 8 + 2, 11, 1)
                elif focus_lis[focus_now] == 'RE':
                    self.oled_1.rect(21 - 1, 16 - 2, 2 * 8 + 2, 11, 1)

                self.show(id=1)

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 开机logo
    def fun_BootLogo(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = 0  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        # Raspberry Pi logo as 32x32 bytearray
        logo = bytearray(
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80"
            b"\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00"
            b"\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18"
            b"\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c "
            b"\x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

        # Load the raspberry pi logo into the framebuffer (the image is 32x32)
        logo = framebuf.FrameBuffer(logo, 32, 32, framebuf.MONO_HLSB)

        tim = Timer()
        tim.init(mode=Timer.ONE_SHOT, period=3000, callback=self.shot_timer)
        self.timer_cond = 0

        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                return 0

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            if self.timer_cond:
                tim.deinit()
                return 0

            ###主屏幕内容###
            self.clear()  # 清除所有

            self.oled_0.blit(logo, 64 - 16, 32 - 16)
            self.text_m("Powered by RP2", 32 + 16 + 4)
            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 设置弹窗
    def fun_Setting(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        focus_now = 0
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                if ButtonSign == 'l' or ButtonSign == 'u':
                    if focus_now:
                        focus_now = 0
                    else:
                        focus_now = 1
                elif ButtonSign == 'r' or ButtonSign == 'd':
                    if focus_now:
                        focus_now = 0
                    else:
                        focus_now = 1
                elif ButtonSign == 'y':
                    if focus_now == 0:
                        self.fun_SettingSwitch()
                    elif focus_now == 1:
                        self.fun_SettingTime()
                elif ButtonSign == 'n':
                    return 0

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            self.draw_border()  # 绘制边界

            self.oled_0.text("Choose:", 24, 13)
            self.oled_0.text("Set Switch", 24, 28)
            self.oled_0.text("Set Time", 24, 43)

            self.oled_0.text("->", 4, focus_now * 15 + 28)

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###
            if self.frame_counter == 0:
                self.clear(id=1)
                self.text_m("[Yes] to Confirm", 16 - 9, id=1)
                self.text_m("[NO]  to Return ", 16, id=1)
                self.show(id=1)

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 设置(开关)
    def fun_SettingSwitch(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        #  将字典复制为列表
        setting_lis = list(self.setting_dic.items())
        for i in range(len(setting_lis)):
            setting_lis[i] = list(setting_lis[i])

        focus_y = 0  # 当前选择

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                # 返回键
                if ButtonSign == 'n':
                    return 0
                # 确认键
                elif ButtonSign == 'y':
                    self.setting_dic = dict(setting_lis)
                    self.setting_control(mode='update')
                    self.jump_window(code="Updated!")
                    return 0
                # 上
                elif ButtonSign == 'u':
                    if focus_y == 0:
                        focus_y = len(setting_lis) - 1
                    else:
                        focus_y -= 1
                # 下
                elif ButtonSign == 'd':
                    if focus_y == len(setting_lis) - 1:
                        focus_y = 0
                    else:
                        focus_y += 1
                # 左
                elif ButtonSign == 'l':
                    if setting_lis[focus_y][1]:
                        setting_lis[focus_y][1] = 0
                    else:
                        setting_lis[focus_y][1] = 1
                # 右
                elif ButtonSign == 'r':
                    if setting_lis[focus_y][1]:
                        setting_lis[focus_y][1] = 0
                    else:
                        setting_lis[focus_y][1] = 1

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            self.oled_0.text('->', 3, 32)  # 箭头

            for i in [-2, -1, 0, 1, 2]:

                try:
                    if focus_y + i >= 0:
                        # 打印选项名
                        if len(setting_lis[focus_y + i]) <= 9:
                            self.oled_0.text(setting_lis[focus_y + i][0], 20, 32 + i * 8)
                        else:
                            self.text_little(setting_lis[focus_y + i][0], 20, 32 + i * 8)
                        # 打印状态
                        if setting_lis[focus_y + i][1]:
                            self.oled_0.text("En", 100, 32 + i * 8)
                        else:
                            self.oled_0.text("Dis", 100, 32 + i * 8)
                    else:
                        pass
                except Exception:
                    pass

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###
            if self.frame_counter == 0:
                self.clear(id=1)
                self.text_m("[Yes] to Confirm", 16 - 9, id=1)
                self.text_m("[NO]  to Return ", 16, id=1)
                self.show(id=1)

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 设置(时间)
    def fun_SettingTime(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕

        # sec min hour week day mon year
        NowTime = b'\x00\x00\x15\x04\x21\x01\x21'

        focus_now = 0  # 当前选择
        setting_lis = ['Set Hour', 'Set Minute', 'Set Second',
                       'Set Year', 'Set Month', 'Set Day', 'Set Week']
        week_lis = ["Sun", "Mon", "Tues", "Wed", "Thur", "Fri", "Sat"]
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0
                # 返回键
                if ButtonSign == 'n':
                    return 0
                # 确认键
                elif ButtonSign == 'y':

                    temp = self.input_keyboard()
                    if temp != 'null' and 1 <= len(temp) <=2 and temp.isdigit():
                        ind = int(temp)
                        time_set = self.TimeDS3231.copy()

                        ok = 1

                        if setting_lis[focus_now] == 'Set Second' and 0 <= ind <= 59:
                            time_set[0] = ind
                        elif setting_lis[focus_now] == 'Set Minute' and 0 <= ind <= 59:
                            time_set[1] = ind
                        elif setting_lis[focus_now] == 'Set Hour' and 0 <= ind <= 23:
                            time_set[2] = ind
                        elif setting_lis[focus_now] == 'Set Week' and 0 <= ind <= 7:
                            time_set[3] = ind % 7
                        elif setting_lis[focus_now] == 'Set Day' and 0 <= ind <= 31:
                            time_set[4] = ind
                        elif setting_lis[focus_now] == 'Set Month' and 0 <= ind <= 12:
                            time_set[5] = ind
                        elif setting_lis[focus_now] == 'Set Year' and 0 <= ind <= 99:
                            time_set[6] = ind
                        else:
                            ok = 0

                        if ok:
                            # 先将10进制当作16进制转换为10进制,因为bytes()会把10进制转换为16进制
                            for i in range(len(time_set)):
                                time_set[i] = int(str(time_set[i]), 16)
                            time_set = bytes(time_set)
                            ds3231.SetTime(time_set)

                            self.jump_window(code='Success')
                    else:
                        self.error_window(code='Wrong Input')


                # 上
                elif ButtonSign == 'u' or ButtonSign == 'l':
                    if focus_now == 0:
                        focus_now = len(setting_lis) - 1
                    else:
                        focus_now -= 1
                # 下
                elif ButtonSign == 'd' or ButtonSign == 'r':
                    if focus_now == len(setting_lis) - 1:
                        focus_now = 0
                    else:
                        focus_now += 1

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            self.oled_0.text('->', 3, 32)  # 箭头

            for i in [-2, -1, 0, 1, 2]:
                try:
                    if focus_now + i >= 0:
                        # 打印选项名
                        self.oled_0.text(setting_lis[focus_now + i], 20, 32 + i * 8)
                    else:
                        pass
                except Exception:
                    pass

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###
            if self.frame_counter == 0:
                self.clear(id=1)
                # 绘制时间
                self.oled_1.text("Time=%02d:%02d:%02d" % (self.TimeDS3231[2], self.TimeDS3231[1], self.TimeDS3231[0]), 0, 0)
                #  绘制日期
                self.oled_1.text("Date=20%d/%02d/%02d" % (self.TimeDS3231[6], self.TimeDS3231[5], self.TimeDS3231[4]), 0, 8)
                #  绘制星期
                self.oled_1.text("Day of Week=%s" % (week_lis[self.TimeDS3231[3]]), 0, 16)
                self.show(id=1)

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数

    # 进制转换器
    def fun_UnitConverter(self):
        self.is_init_fps = 0  # fps计数器初始化
        self.is_button_ready = 0  # 按钮复位标志初始化
        self.sec_buffer = self.TimeDS3231[0]  # 初始化记秒器

        self.clear(id=2)
        self.show(id=2)  # 清空两个屏幕
        while True:
            self.TimeDS3231 = ds3231.ReportList()  # 获取时间

            # 按钮部分
            ButtonSign = self.button_sign()  # 获取按钮状态
            # 检测按钮做出反应
            if ButtonSign != 0 and self.is_button_ready == 1:
                self.is_button_ready = 0

            elif ButtonSign == 0 and self.is_button_ready == 0:
                self.is_button_ready = 1

            ###主屏幕内容###
            self.clear()  # 清除所有
            # self.draw_border()  # 绘制边界

            self.show_fps(s=self.TimeDS3231[0])  # 显示fps
            self.show()  # 绘制所有

            ###副屏幕内容###

            self.fps_limiter(limit=self.fps_limit, frame_count=self.frame_counter, fps=self.fps)  # 限制帧数


if __name__ == '__main__':
    PicoClock()
