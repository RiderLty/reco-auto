# MYScrcpy Core
### 简介
从 [MYScrcpy](https://github.com/me2sy/MYScrcpy) 项目中抽离出Core部分，方便直接引用开发。

同时简化包引用，方面Termux等特殊环境中安装引用。

### 安装

```bash
# 最小安装方式，该方式不包含numpy、pyperclip，适用于termux环境。
uv add mysc-core
```
**注意！** numpy在termux环境下特殊，需要使用 `pkg install python-numpy`，如果使用uv管理，需要添加 `--system-site-packages` 参数

```bash
# 完全安装方式，包含全部依赖包，适合PC环境
uv add mysc-core[all]
```


- 如果使用剪切板同步功能，需单独安装 ``pyperclip`` 目前Termux环境不支持。
- numpy在termux环境下特殊，需要使用 ``pkg install python-numpy``，如果使用uv管理，需要添加全局变量

### 开发示例
获取视频流，音频及控制同理。
```python
from adbutils import adb

from mysc_core.video import VideoAdapter, VideoKwargs

device = adb.device_list()[0]

# 定义视频适配器
va = VideoAdapter(
    # 定义连接参数
    VideoKwargs(
        video_codec=VideoKwargs.EnumVideoCodec.H264,
        max_fps=30
    )
)

# 发起连接
va.connect(device)

while True:
    
    # Pillow Image
    pil_img = va.get_image()
    
    # RGB np.ndarray
    data = va.get_ndarray(frame_format='rgb24')
    
    # 自定义逻辑

# 关闭连接
va.disconnect()
```

## 鸣谢

感谢 [**Scrcpy**](https://github.com/Genymobile/scrcpy/) 项目及作者 [**rom1v**](https://github.com/rom1v)，在这一优秀项目基础上，才有了本项目。

感谢使用到的各个包项目及作者们。有你们的付出，才有了如此好的软件开发环境。

同时感谢各位使用者们，谢谢你们的支持与帮助，也希望MYSC-Core成为你们得心应手的好工具，好帮手。

## 声明

本项目供日常学习（图形、声音、AI训练等）、Android测试、开发等使用。

**请一定注意：**

1.开启手机调试模式存在一定风险，可能会造成数据泄露等风险，使用前确保您了解并可以规避相关风险

**2.本项目不可用于违法犯罪等使用**

**本人及本项目不对以上产生的相关后果负任何责任，请斟酌使用。**

## GUI
[MYScrcpy](https://github.com/me2sy/MYScrcpy) 基于 MYSC-Core及Kivy/KivyMD 制作的Scrcpy python客户端。