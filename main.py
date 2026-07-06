import threading
import cv2
from adbutils import adb
from mysc_core.video import VideoAdapter, VideoKwargs
from mysc_core.control import ControlAdapter, ControlKwargs, EnumDirection

from core.reco_state import RecoState
from interface.scrcpy_touch import ScrcpyTouchAdapter


# ------------------------------------------------------------
# Demo RecoState 子类 — 替换 on_pic 为你的识别逻辑
# ------------------------------------------------------------

class DemoAuto(RecoState):
    def on_pic(self, pic):
        # TODO: 识别逻辑，通过 self.ta 操作触控
        # 此方法跑在 worker 线程中，不会卡 GUI
        pass


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

device = adb.device_list()[0]
print(device)

# 控制适配器
ca = ControlAdapter(
    ControlKwargs(_screen_status=ControlKwargs.EnumScreenStatus.ON)
).connect(device)

# 触控 & 状态机
ta = ScrcpyTouchAdapter(ca)
ta.direction = EnumDirection.HORIZONTAL  # 横屏游戏
reco = DemoAuto(ta)

# 视频适配器
va = VideoAdapter(
    VideoKwargs(
        video_codec=VideoKwargs.EnumVideoCodec.H264,
        max_fps=60,
    )
)
va.connect(device)

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
    while True:
        data = va.get_ndarray(frame_format='rgb24')
        if data is None:
            continue

        with _lock:
            _latest_frame = data  # 覆盖旧帧，不堆积

        bgr = cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
        cv2.imshow('Device Screen', bgr)

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
