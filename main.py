import threading
import cv2
from adbutils import adb
from mysc_core.video import VideoAdapter, VideoKwargs
from mysc_core.control import ControlAdapter, ControlKwargs, EnumDirection
from mysc_core.session import Session  
from core.reco_state import RecoState
from interface.scrcpy_touch import ScrcpyTouchAdapter
import os
import numpy as np
import time
from dataclasses import dataclass  
from typing import Optional  
#适配分辨率 1080x1920 density 240

# ------------------------------------------------------------
# Demo RecoState 子类 — 替换 on_pic 为你的识别逻辑
# ------------------------------------------------------------


class DemoAuto(RecoState):
    def __init__(self, ta):
        super().__init__(ta)
        self.state = None
        self.click_on_find = []
        self.templates = {}
        for file in sorted([ x for x in os.listdir('templates/clickOnFind') if x.endswith('.jpg')] , key=lambda x: x):
            print( "load type clickOnFind : ", file)
            path = os.path.join('templates/clickOnFind', file)
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is not None:
                self.click_on_find.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        for file in [ x for x in os.listdir('templates') if x.endswith('.jpg')]:
            print( "load type special : ", file)
            path = os.path.join('templates', file)
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is not None:
                self.templates[file.split('.')[0]] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    def match(self,gray,name):
        if name not in self.templates:
            return None
        img = self.templates[name]
        result = cv2.matchTemplate(gray, img, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.8:
            h, w = img.shape[:2]
            center_x = (max_loc[0] + w // 2) / gray.shape[1]
            center_y = (max_loc[1] + h // 2) / gray.shape[0]
            print(f"{name} matched: center=({center_x}, {center_y}), confidence={max_val:.3f}")
            time.sleep(0.5)
            print("sleep 0.5s")
            return center_x, center_y
        return None


    def on_pic(self, pic: np.ndarray):
        gray = cv2.cvtColor(pic, cv2.COLOR_RGB2GRAY)
        if self.state is None:
            for img in self.click_on_find:
                result = cv2.matchTemplate(gray, img, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val > 0.8:
                    h, w = img.shape[:2]
                    center_x = (max_loc[0] + w // 2) / pic.shape[1]
                    center_y = (max_loc[1] + h // 2) / pic.shape[0]
                    print(f"click_on_find matched: center=({center_x}, {center_y}), confidence={max_val:.3f}")
                    self.ta.tap(center_x, center_y)  # trigger a tap at the matched position
                    time.sleep(0.5)
                    return

        if self.state is None:
            if (pos := self.match(gray,'获得奖励')) is not None:
                self.ta.tap(pos[0], pos[1] - 0.2)  # trigger a tap at the matched position
                time.sleep(0.5)
                return

            if (pos := self.match(gray,'选球')) is not None:
                self.ta.tap(pos[0], pos[1])  # trigger a tap at the matched position
                self.state = '已选球'
                time.sleep(0.5)
                return
            

            if (pos := self.match(gray,'已逮捕')) is not None:
                self.ta.tap(pos[0] - 0.3, pos[1])  # trigger a tap at the matched position
                time.sleep(0.5)
                return
            
            if (pos := self.match(gray,'力量增效')) is not None:
                time.sleep(1)
                self.ta.tap(pos[0], pos[1])  # trigger a tap at the matched position
                self.state = '力量增效OK'
                time.sleep(2)
                return


        if self.state == '已选球':
            if (pos := self.match(gray,'逮捕')) is not None:
                self.ta.tap(pos[0], pos[1])  # trigger a tap at the matched position
                self.state = None
                time.sleep(0.5)
                return
        
        if self.state == '力量增效OK':
            if (pos := self.match(gray,'冰雹')) is not None:
                self.ta.tap(pos[0], pos[1])  # trigger a tap at the matched position
                time.sleep(0.5)
                return
            if (pos := self.match(gray,'印记')) is not None:
                self.ta.tap(pos[0], pos[1])  # trigger a tap at the matched position
                time.sleep(0.5)
                self.state = None
                return


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------



device = adb.device_list()[0]
print(device)
displayID = input("请输入 displayID,默认0: ")
if displayID == '':
    displayID = 0
else:
    displayID = int(displayID)
# 控制适配器


# 触控 & 状态机

# 视频适配器
va = VideoAdapter(
    VideoKwargs(
        video_codec=VideoKwargs.EnumVideoCodec.H264,
        max_fps=60,
        display_id=displayID
    )
)
va.connect(device)

ca = ControlAdapter(
    ControlKwargs(_screen_status=ControlKwargs.EnumScreenStatus.ON, display_id=displayID)
).connect(device)

ta = ScrcpyTouchAdapter(ca)
ta.direction = EnumDirection.HORIZONTAL  # 横屏游戏
reco = DemoAuto(ta)


# ------------------------------------------------------------
# 帧共享：主线程写，worker 线程取最新
# ------------------------------------------------------------

_latest_frame = None
_lock = threading.Lock()
_running = True


def _worker():
    """Worker 线程 — 取最新帧喂给 RecoState"""
    global _latest_frame
    while _running:
        with _lock:
            frame = _latest_frame
            _latest_frame = None
        if frame is not None:
            reco.process(frame)
        else:
            cv2.waitKey(1)


threading.Thread(target=_worker, daemon=True).start()

# ------------------------------------------------------------
# 主线程：拿帧 → 丢给 worker → 显示
# ------------------------------------------------------------

try:
    init = False
    while True:
        data = va.get_ndarray(frame_format='rgb24')
        if data is None:
            continue

        with _lock:
            _latest_frame = data  # 覆盖旧帧，不堆积

        bgr = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
        if not init:
            init = True
            cv2.namedWindow('my_window', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow('my_window', bgr.shape[1] // 4, bgr.shape[0] // 4)
        cv2.imshow('my_window', bgr)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite('screen.jpg', bgr)
            print('saved: screen.jpg')
finally:
    _running = False
    va.disconnect()
    cv2.destroyAllWindows()
