# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

reco-auto is an Android device automation tool that combines screen recognition (via OpenCV template matching) with scrcpy-based touch control. The primary use case is automating gameplay in mobile games by recognizing UI elements on screen and issuing touch events in response.

Requires Python 3.12.

## Dev Commands

```powershell
# Activate environment
.venv\Scripts\activate

# Run the main automation script
uv run python main.py

# Add a dependency
uv add <package-name>
```

## Architecture

```
main.py                          — Entry point / game automation demo
core/
  reco_state.py                  — RecoState: state machine for frame recognition (callback-driven)
interface/
  touchAdapter.py                — TouchAdapter (ABC): abstract touch API (tap, swipe, long_press, multi-touch)
  scrcpy_touch.py                — ScrcpyTouchAdapter: concrete impl using ControlAdapter
templates/
  clickOnFind/                   — Templates matched only in default state ("always click when seen")
  *.jpg                          — Templates matched with state-aware logic
```

### Library layer (`lib/MYSC-Core/`)

The project vendors the **`mysc-core`** Scrcpy control library (by Me2sY). It provides:

- **`VideoAdapter`** — H264/H265 video streaming via pyav. `.connect(adb_device)` starts streaming; `.get_ndarray()` / `.get_image()` grab frames. `VideoKwargs` configures codec, max_fps, display_id.
- **`ControlAdapter`** — Scrcpy control socket. Touch events, text paste, scroll, UHID keyboard/mouse. `f_touch_spr(EnumAction, ScalePointR, finger_id)` for touch. `ControlKwargs` for screen/power settings.
- **`Session`** — Combines video, audio, and control adapters. `Session.from_dict(device, config)` is the preferred constructor pattern.
- **`MYDevice` / `JSDeviceInfo`** — Device info caching (brand, model, SDK, release), USB/TCP-IP connection management.
- **Coordinates** (`mysc_core.utils.vector`): `ScalePointR(ratio_x, ratio_y, direction)` for device-agnostic relative positioning; `EnumDirection.VERTICAL` | `HORIZONTAL`.

### TouchAdapter hierarchy

`TouchAdapter` (ABC) defines the abstract touch primitives — `tap`, `swipe`, `long_press`, `touch_down/move/up` — all using relative coordinates (0.0–1.0). It includes a built-in finger ID pool (0–9).

`ScrcpyTouchAdapter` is the concrete implementation: it maps abstract primitives to `ControlAdapter.f_touch_spr()` calls using `ScalePointR` and `EnumDirection`. It tracks per-finger last-known positions so `touch_up` always sends the correct coordinate.

### Recognition state machine

`RecoState.process(pic)` is the frame entry point. It calls `on_pic(pic)` (subclass hook) with re-entrance protection: if the previous `on_pic` hasn't returned, the new frame is silently dropped.

Subclasses implement `on_pic` and access `self.ta` (a `TouchAdapter`) to issue touch events.

### Template matching (main.py pattern)

Two tiers of templates:
1. **`templates/clickOnFind/*.jpg`** — Matched only when `state is None`. If any template matches (confidence > 0.8), a tap is issued at the match center. These represent "always dismiss" popups/buttons.
2. **`templates/*.jpg`** — Matched with explicit `self.match(gray, name)` calls, gated by the current `self.state`. State transitions drive which templates are active.

### Threading model (main.py)

A double-buffering approach with a single shared frame:

- **Main thread** — Grabs frames from `va.get_ndarray()`, writes the latest one under `_lock`, renders it in an OpenCV window.
- **Worker thread** — Reads the latest frame under `_lock`, feeds it to `reco.process()`. If no frame is available, waits briefly.

This decouples the video framerate from the (potentially slow) recognition logic, dropping frames when the worker is busy.
