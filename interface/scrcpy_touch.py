# -*- coding: utf-8 -*-
"""
    scrcpy_touch
    ~~~~~~~~~~~~~~~~~~
    基于 mysc-core ControlAdapter 的 TouchAdapter 实现

    通过 scrcpy 控制协议将相对坐标触摸原语转换为设备触控事件。
    内部维护每个触控点的最后已知位置，确保抬起事件携带正确坐标。
"""

from __future__ import annotations

from typing import Optional

from mysc_core.control import ControlAdapter, EnumAction, ScalePointR, EnumDirection

from interface.touchAdapter import TouchAdapter


class ScrcpyTouchAdapter(TouchAdapter):
    """
        基于 ControlAdapter 的触控实现

        将 TouchAdapter 的抽象触控原语映射到 ControlAdapter.f_touch_spr()，
        坐标统一使用 ScalePointR(VERTICAL) 相对坐标系。
    """

    def __init__(self, control_adapter: ControlAdapter):
        """
        :param control_adapter: 已连接设备的 ControlAdapter 实例
        """
        super().__init__()
        self._ca = control_adapter
        self.direction: EnumDirection = EnumDirection.VERTICAL
        self._positions: dict[int, tuple[float, float]] = {}

    # ------------------------------------------------------------
    # Coordinate Helper
    # ------------------------------------------------------------

    def _to_spr(self, x: float, y: float) -> ScalePointR:
        """相对坐标 (0.0~1.0) → ScalePointR"""
        return ScalePointR(x, y, self.direction)

    # ------------------------------------------------------------
    # TouchAdapter Implementation
    # ------------------------------------------------------------

    def tap(self, x: float, y: float, duration: float = 0.05) -> None:
        fid = self._alloc_id()
        if fid is None:
            return

        spr = self._to_spr(x, y)
        self._ca.f_touch_spr(EnumAction.DOWN, spr, fid)
        self._sleep(duration)
        self._ca.f_touch_spr(EnumAction.UP, spr, fid)
        self._free_id(fid)

    def swipe(
            self,
            x1: float, y1: float,
            x2: float, y2: float,
            duration: float = 0.3,
            steps: int = 10,
    ) -> None:
        fid = self._alloc_id()
        if fid is None:
            return

        # 起点按下
        self._ca.f_touch_spr(EnumAction.DOWN, self._to_spr(x1, y1), fid)

        # 中间插值移动
        step_duration = duration / steps
        for i in range(1, steps + 1):
            t = i / steps
            xi = x1 + (x2 - x1) * t
            yi = y1 + (y2 - y1) * t
            self._sleep(step_duration)
            self._ca.f_touch_spr(
                EnumAction.MOVE, self._to_spr(xi, yi), fid,
                ignore_repeat_check=True,
            )

        # 终点抬起
        self._ca.f_touch_spr(EnumAction.UP, self._to_spr(x2, y2), fid)
        self._free_id(fid)

    def long_press(self, x: float, y: float, duration: float = 0.5) -> None:
        fid = self._alloc_id()
        if fid is None:
            return

        spr = self._to_spr(x, y)
        self._ca.f_touch_spr(EnumAction.DOWN, spr, fid)
        self._sleep(duration)
        self._ca.f_touch_spr(EnumAction.UP, spr, fid)
        self._free_id(fid)

    def touch_down(self, x: float, y: float, finger_id: Optional[int] = None) -> int:
        if finger_id is None:
            finger_id = self._alloc_id()
        elif finger_id not in self._allocated_ids:
            self._allocated_ids.add(finger_id)

        self._positions[finger_id] = (x, y)
        self._ca.f_touch_spr(EnumAction.DOWN, self._to_spr(x, y), finger_id)
        return finger_id

    def touch_move(self, x: float, y: float, finger_id: int) -> None:
        self._positions[finger_id] = (x, y)
        self._ca.f_touch_spr(
            EnumAction.MOVE, self._to_spr(x, y), finger_id,
            ignore_repeat_check=True,
        )

    def touch_up(self, finger_id: int) -> None:
        x, y = self._positions.pop(finger_id, (0, 0))
        self._ca.f_touch_spr(EnumAction.UP, self._to_spr(x, y), finger_id)
        self._free_id(finger_id)
