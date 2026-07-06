# -*- coding: utf-8 -*-
"""
    reco-state
    ~~~~~~~~~~~~~~~~~~
    画面识别状态机 — 防重入 + on_pic 钩子
"""

from interface.touchAdapter import TouchAdapter


class RecoState:
    """
        画面识别状态机

        Attributes:
            ta: TouchAdapter 实例，子类在 on_pic() 中通过 self.ta 操作触控
    """

    def __init__(self, touch_adapter: TouchAdapter):
        self.ta = touch_adapter
        self._handling = False

    def process(self, pic) -> bool:
        """
            喂入一帧进行处理。若上一帧尚未处理完则跳过。

        :param pic: ndarray 格式画面
        :returns: 是否进入了 on_pic
        """
        if self._handling:
            return False

        self._handling = True
        try:
            self.on_pic(pic)
        finally:
            self._handling = False
        return True

    # ------------------------------------------------------------
    # Subclass Hook
    # ------------------------------------------------------------

    def on_pic(self, pic):
        """
            画面识别核心方法 — 子类实现

            本方法受防重入保护：若上一帧的 on_pic 尚未返回，新帧会被跳过。

        :param pic: 当前帧画面
        """
        raise NotImplementedError("Subclasses must implement on_pic()")
