# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

reco-auto is an Android device automation tool that combines screen recognition (via OpenCV) with scrcpy-based touch control. It's in early development (v0.1.0, pre-initial commit).

## Dev Commands

```powershell
# Activate environment
.venv\Scripts\activate

# Run the main demo script
uv run python main.py

# Add a dependency
uv add <package-name>

# Update lockfile
uv lock

# Run a single Python file
uv run python path/to/file.py
```

## Architecture

```
main.py                     — Entry point / demo: device connection, touch gestures, video streaming
core/
  reco-state.py             — RecoState: state machine for picture recognition events (callback-driven)
interface/
  touchAdapter.py           — TouchAdapter: touch ID allocation, down/up/move/click abstraction
```

The project builds on **`mysc-core[all]`** (a Scrcpy control library by Me2sY), which provides:

- **`VideoAdapter`** / **`VideoKwargs`** — Scrcpy H264/H265 video streaming via pyav, with frame callback support. Call `.connect(adb_device)` to start streaming, `.get_ndarray()` / `.get_image()` to grab frames.
- **`ControlAdapter`** / **`ControlKwargs`** — Device control over scrcpy control socket. Supports touch events, text paste, scroll, UHID keyboard/mouse/gamepad. Coordinates use `ScalePointR` (relative positioning with direction awareness: `EnumDirection.VERTICAL` / `HORIZONTAL`).
- **`Session`** — Combines video, audio, and control adapters into one connection.
- **`MYDevice`** / **`JSDeviceInfo`** — Device info caching (brand, model, SDK, release), USB/TCP-IP connection management.
- **Coordinate system** (`mysc_core.utils.vector`): `ScalePointR(ratio_x, ratio_y, direction)` for device-agnostic relative positioning; `Coordinate` for physical resolution with rotation handling.

## Key Patterns

- **Adapters follow a connect/disconnect lifecycle** — `Adapter.connect(adb_device)` returns `self`, starts worker threads; `.disconnect()` tears down.
- **ScalePointR for touch targeting** — Always use relative coordinates (`ScalePointR(0.2, 0.3, EnumDirection.VERTICAL)`) rather than absolute pixels, so gestures work across device resolutions.
- **ControlAdapter uses a send queue** — Methods like `f_touch_spr()` enqueue packets onto a background thread; optional `ignore_repeat_check` bypasses dedup.
- **RecoState is a state machine stub** — The `on_pic(pic)` callback is the hook point for frame recognition logic; `pic_now_handling` flag prevents re-entrance.
- **TouchAdapter manages touch ID allocation** — IDs 0-9 are tracked in an `allocated_ids` set; `touch_down` allocates, `touch_up` frees.

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `mysc-core[all]` | >=1.0.1 | Scrcpy device control (video, touch, keyboard, gamepad) |
| `opencv-python` | >=5.0.0.93 | Computer vision for screen recognition |
| `adbutils` | (transitive) | ADB device discovery and communication |
