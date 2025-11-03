# 项目优化历史记录

## 截图函数优化

| 项目 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 实现方式 | pyautogui.screenshot() | Win32 API (BitBlt) | - |
| 平均耗时 | 30ms | 8ms | 3.75倍 |
| 优化日期 | - | 2025-11-03 | - |
| 实现位置 | - | DeltaForce/DeltaForceRecognize.py | - |
| 函数名 | _capture_screenshot_pyautogui() | _capture_screenshot_win32api() | - |

---

