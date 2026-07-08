# -*- coding: utf-8 -*-
"""
    params
    ~~~~~~~~~~~~~~~~~~
    
    Log:
        2026-03-10 1.0.0 Me2sY  分离

"""

__author__ = 'Me2sY'
__version__ = '1.0.0'

__all__ = ['Param']

import pathlib
from typing import ClassVar

PROJECT_NAME = 'mysc_core'


def project_path() -> pathlib.Path:
    """
        获取项目根目录
    :return:
    """
    for _ in pathlib.Path(__file__).resolve().parents:
        if _.name == PROJECT_NAME:
            return _

    raise FileNotFoundError(PROJECT_NAME)


class Param:

    PROJECT_NAME: ClassVar[str] = PROJECT_NAME
    AUTHOR: ClassVar[str] = __author__
    VERSION: ClassVar[str] = __version__
    EMAIL: ClassVar[str] = 'me2sy@outlook.com'
    GITHUB: ClassVar[str] = 'https://github.com/Me2sY/mysc'

    PATH_BASE: ClassVar[pathlib.Path] = project_path()

    PATH_LIBS: ClassVar[pathlib.Path] = PATH_BASE.joinpath('libs')
    PATH_LIBS.mkdir(parents=True, exist_ok=True)

    PATH_LOCAL: ClassVar[pathlib.Path] = pathlib.Path.home().joinpath(f".{PROJECT_NAME}")
    PATH_LOCAL.mkdir(parents=True, exist_ok=True)

    PATH_CONFIG: ClassVar[pathlib.Path] = PATH_LOCAL.joinpath("config")
    PATH_CONFIG.mkdir(parents=True, exist_ok=True)
