# 候机楼源码

本包包含模拟器和 30 秒宣传片的完整制作源码。

## 文件

- `机场翻牌显示器.html`：模拟器全部 HTML、CSS 和 JavaScript，双击用浏览器打开即可，离线可用，无需安装依赖。
- `render.py`：宣传片画面、翻牌动画、文案、剪辑时间轴、合成配乐、机械音效和 MP4 导出逻辑。
- `requirements.txt`：视频制作所需 Python 依赖。

## 重新制作宣传片

原版使用 Python 3.12、Pillow 13.0.0、NumPy 2.3.5 和 FFmpeg，在 macOS 上制作。

1. 安装 Python 3.12 和支持 libx264/AAC 的 FFmpeg；确保 `ffmpeg` 可在终端运行。
2. 在本文件所在目录运行：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python render.py --preview
python render.py
```

Windows 使用 `.venv\Scripts\activate` 激活环境。预览输出到 `work/`，视频与封面输出到 `outputs/`；重复运行会覆盖同名生成文件。

默认导出：30 秒，1920×1080，30 帧/秒，H.264 视频、AAC 立体声音频。

## 字体与工具路径

程序优先使用系统字体，不包含或分发字体文件。原版字体为 macOS 的黑体、Avenir Next Condensed 和 Menlo。源码也提供 Windows 微软雅黑与 Linux Noto CJK 等常见字体路径作为候选；使用其他字体时外观会有所不同，Windows/Linux 未实际验证。

找不到中文字体时，可以设置 `CJK_FONT` 为本地字体文件路径；也支持 `LATIN_FONT`、`DISPLAY_FONT`、`MONO_FONT` 分别替换其他字体，`FFMPEG_BIN` 可指定 FFmpeg 的完整路径。

## 修改内容

- 五个 `scene_...` 函数：分镜画面与文案。
- `frame()`：分镜时间轴与转场。
- `FLIGHTS`、`NEW_FLIGHT`、`BIG_ROWS`：片中模拟航班。
- `flap()`、`animated_char()`：半片翻折和随机字符动画。
- `audio()`：原创合成氛围配乐与机械音效。
- `PALETTES`：画面配色。

片长、画幅和分镜位置是为当前 30 秒 1080p 成片设计的；若改变时长或画幅，需同步调整各分镜、音效和文案布局。

宣传片是根据模拟器设计绘制的动态产品演示，并非浏览器录屏；航班均为模拟数据，换班镜头有加速展示标记。制作过程中没有使用第三方图片、视频或音乐素材。
