# -*- coding: utf-8 -*-
"""
独立的窗口获取工具模块
从DeltaForce类中抽离出来的窗口管理功能
"""

def get_all_deltaforce_windows():
    """
    获取所有DeltaForce窗口信息（独立函数）
    从DeltaForceWindow类中抽离出来，供GUI独立使用
    """
    try:
        from DeltaForceWindow import enum_windows, get_window_info
        
        deltaforce_windows = []
        windows = enum_windows()
        
        for hwnd, title, process_name in windows:
            if process_name == "DeltaForceClient-Win64-Shipping.exe":
                try:
                    win_info = get_window_info(hwnd)
                    deltaforce_windows.append({
                        'hwnd': hwnd,
                        'title': title,
                        'process_name': process_name,
                        'window_info': win_info
                    })
                except Exception:
                    continue
        
        return deltaforce_windows
    except Exception as e:
        print(f"获取DeltaForce窗口失败: {e}")
        return []

def classify_windows_by_size(windows):
    """
    根据窗口大小分类为主窗口和辅窗口（独立函数）
    """
    if len(windows) == 0:
        return [], []
    elif len(windows) == 1:
        return windows, []
    else:
        # 按窗口大小排序，最小的作为主窗口
        sorted_windows = sorted(windows, 
                              key=lambda w: w['window_info']['width'] * w['window_info']['height'])
        
        main_windows = [sorted_windows[0]]
        aux_windows = sorted_windows[1:]
        
        return main_windows, aux_windows
