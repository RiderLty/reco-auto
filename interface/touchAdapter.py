# -*- coding: utf-8 -*-
"""
    touchAdapter
    ~~~~~~~~~~~~~~~~~~
    触摸输出统一抽象接口

    所有坐标使用相对坐标 (0.0 ~ 1.0)，与设备分辨率无关。
    具体实现负责将相对坐标映射到对应设备的触控后端。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional


class TouchAdapter(ABC):
    """
        触摸输出抽象基类

        定义了手游自动化所需的全部触摸原语。
        子类只需关注「如何把相对坐标发到设备」，上层识别代码不感知底层实现。

        ID 池:
            内置 0~9 共10个触控点 ID 分配器，子类通过 _alloc_id / _free_id 管理。
    """

    MAX_FINGERS = 10

    # ------------------------------------------------------------
    # ID Pool (shared infrastructure)
    # ------------------------------------------------------------

    def __init__(self):
        self._allocated_ids: set[int] = set()

    def _alloc_id(self) -> Optional[int]:
        """分配一个空闲触控点 ID，无空闲时返回 None"""
        for i in range(self.MAX_FINGERS):
            if i not in self._allocated_ids:
                self._allocated_ids.add(i)
                return i
        return None

    def _free_id(self, finger_id: int):
        """释放触控点 ID"""
        self._allocated_ids.discard(finger_id)

    @property
    def active_fingers(self) -> int:
        """当前已分配的触控点数"""
        return len(self._allocated_ids)

    # ------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------

    @staticmethod
    def _sleep(seconds: float):
        """阻塞等待，子类可覆写以适配异步/事件驱动场景"""
        time.sleep(seconds)

    # ------------------------------------------------------------
    # Abstract Touch Primitives
    # ------------------------------------------------------------

    @abstractmethod
    def tap(self, x: float, y: float, duration: float = 0.05) -> None:
        """
            点击 — 在 (x, y) 处快速按下并抬起

        :param x:        相对横坐标 0.0 ~ 1.0
        :param y:        相对纵坐标 0.0 ~ 1.0
        :param duration: 按下持续时间（秒）
        """
        ...

    @abstractmethod
    def swipe(
            self,
            x1: float, y1: float,
            x2: float, y2: float,
            duration: float = 0.3,
            steps: int = 10,
    ) -> None:
        """
            滑动 — 从 (x1, y1) 匀速移动到 (x2, y2)

        :param x1:       起点相对横坐标
        :param y1:       起点相对纵坐标
        :param x2:       终点相对横坐标
        :param y2:       终点相对纵坐标
        :param duration: 滑动总时长（秒）
        :param steps:    中间插值步数
        """
        ...

    @abstractmethod
    def long_press(self, x: float, y: float, duration: float = 0.5) -> None:
        """
            长按 — 在 (x, y) 处按下，保持一段时间后抬起

        :param x:        相对横坐标 0.0 ~ 1.0
        :param y:        相对纵坐标 0.0 ~ 1.0
        :param duration: 按下持续时间（秒）
        """
        ...

    @abstractmethod
    def touch_down(self, x: float, y: float, finger_id: Optional[int] = None) -> int:
        """
            手指按下 — 分配 ID 并发送按下事件

        :param x:         相对横坐标 0.0 ~ 1.0
        :param y:         相对纵坐标 0.0 ~ 1.0
        :param finger_id: 指定触控 ID（None 则自动分配）
        :returns:         实际使用的触控 ID
        """
        ...

    @abstractmethod
    def touch_move(self, x: float, y: float, finger_id: int) -> None:
        """
            手指移动 — 更新指定触控点的位置

        :param x:         相对横坐标 0.0 ~ 1.0
        :param y:         相对纵坐标 0.0 ~ 1.0
        :param finger_id: 触控 ID
        """
        ...

    @abstractmethod
    def touch_up(self, finger_id: int) -> None:
        """
            手指抬起 — 释放指定触控点

        :param finger_id: 触控 ID
        """
        ...
