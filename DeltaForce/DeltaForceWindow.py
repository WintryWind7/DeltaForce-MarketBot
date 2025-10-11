import os
import sys
import time
import threading
import ctypes
from typing import Optional, Dict, Any, Tuple

# 添加core目录到Python路径
core_path = os.path.join(os.path.dirname(__file__), '..', 'core')
sys.path.insert(0, core_path)

# 导入编译后的pyd文件
try:
    from dist.window_func import (
        find_window_by_name, 
        get_window_info, 
        get_window_title,
        get_process_name,
        enum_windows
    )
    print("✓ 成功导入编译后的window_func模块")
except ImportError as e:
    print(f"警告: 无法从dist导入window_func模块: {e}")
    # 如果直接导入失败，尝试从src导入
    try:
        sys.path.append(os.path.join(core_path, 'src'))
        from window_func import (
            find_window_by_name, 
            get_window_info, 
            get_window_title,
            get_process_name,
            enum_windows
        )
        print("✓ 成功从src导入window_func模块")
    except ImportError as e2:
        print(f"警告: 无法导入window_func模块: {e2}")
        print("请确保已编译pyd文件或安装Cython依赖")
        # 提供模拟函数用于测试
        def find_window_by_name(*args, **kwargs): return None
        def get_window_info(*args, **kwargs): return {}
        def get_window_title(*args, **kwargs): return ""
        def get_process_name(*args, **kwargs): return ""
        def enum_windows(): return []


class DeltaForceWindow(object):
    """DeltaForce窗口管理类"""
    
    def __init__(self):
        # 核心属性
        self.target_process_name = "DeltaForceClient-Win64-Shipping.exe"
        self.target_window_handle = None
        
        # 窗口物理属性（像素）
        self.window_x = 0          # 窗口左上角X坐标
        self.window_y = 0          # 窗口左上角Y坐标
        self.window_width = 0      # 窗口物理宽度
        self.window_height = 0     # 窗口物理高度
        
        # DPI缩放因子
        self.dpi_scale_x = 1.0     # X方向DPI缩放
        self.dpi_scale_y = 1.0     # Y方向DPI缩放
        
        # 监控相关
        self.is_monitoring = False
        self.monitor_duration = 10
        
    def _get_dpi_for_window(self, hwnd: int) -> Tuple[float, float]:
        """获取指定窗口的DPI值"""
        try:
            # 尝试使用Windows 10+的GetDpiForWindow API
            if hasattr(ctypes.windll.user32, 'GetDpiForWindow'):
                dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
                if dpi > 0:
                    return float(dpi), float(dpi)
            
            # 回退到GetDeviceCaps方法
            dc = ctypes.windll.user32.GetDC(hwnd)
            if dc:
                try:
                    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                    dpi_y = ctypes.windll.gdi32.GetDeviceCaps(dc, 90)  # LOGPIXELSY
                    if dpi_x > 0 and dpi_y > 0:
                        return float(dpi_x), float(dpi_y)
                finally:
                    ctypes.windll.user32.ReleaseDC(hwnd, dc)
            
            # 如果都失败，使用系统DPI
            return self._get_system_dpi()
            
        except Exception as e:
            print(f"获取窗口DPI时出错: {e}")
            return self._get_system_dpi()
    
    def _get_system_dpi(self) -> Tuple[float, float]:
        """获取系统DPI值"""
        try:
            dc = ctypes.windll.user32.GetDC(0)
            if dc:
                try:
                    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)
                    dpi_y = ctypes.windll.gdi32.GetDeviceCaps(dc, 90)
                    if dpi_x > 0 and dpi_y > 0:
                        return float(dpi_x), float(dpi_y)
                finally:
                    ctypes.windll.user32.ReleaseDC(0, dc)
        except Exception as e:
            print(f"获取系统DPI时出错: {e}")
        
        return 96.0, 96.0
    
    def _update_window_info(self):
        """更新窗口信息到实例属性"""
        if self.target_window_handle is None:
            return
            
        try:
            window_info = get_window_info(self.target_window_handle)
            
            # 获取DPI缩放因子
            dpi_x, dpi_y = self._get_dpi_for_window(self.target_window_handle)
            self.dpi_scale_x = dpi_x / 96.0
            self.dpi_scale_y = dpi_y / 96.0
            
            # 更新物理坐标和尺寸
            self.window_x = window_info.get("left", 0)
            self.window_y = window_info.get("top", 0)
            self.window_width = window_info.get("width", 0)
            self.window_height = window_info.get("height", 0)
            
        except Exception as e:
            print(f"更新窗口信息时出错: {e}")
    
    def find_deltaforce_process(self) -> Optional[int]:
        """查找DeltaForceClient进程窗口"""
        try:
            # 方法1: 通过进程名查找
            self.target_window_handle = find_window_by_name(window_name=self.target_process_name)
            
            # 方法2: 如果方法1失败，枚举所有窗口查找
            if self.target_window_handle is None:
                windows = enum_windows()
                for hwnd, title, process in windows:
                    if process == self.target_process_name:
                        self.target_window_handle = hwnd
                        break
            
            # 如果找到窗口，立即更新窗口信息
            if self.target_window_handle:
                self._update_window_info()
            
            return self.target_window_handle
            
        except Exception as e:
            print(f"查找DeltaForce进程时出错: {e}")
            return None
    
    def get_process_info(self) -> Dict[str, Any]:
        """获取DeltaForce进程的详细信息"""
        if self.target_window_handle is None:
            if not self.find_deltaforce_process():
                return {"error": "未找到DeltaForce进程"}
        
        try:
            self._update_window_info()
            
            title = get_window_title(self.target_window_handle)
            process_name = get_process_name(self.target_window_handle)
            
            return {
                "window_handle": self.target_window_handle,
                "process_name": process_name,
                "window_title": title,
                "position": (self.window_x, self.window_y),
                "size": (self.window_width, self.window_height),
                "dpi_scale": (self.dpi_scale_x, self.dpi_scale_y)
            }
            
        except Exception as e:
            return {"error": f"获取进程信息时出错: {e}"}
    
    def start_monitoring(self, duration: int = 10):
        """开始监控窗口变化"""
        if self.is_monitoring:
            print("窗口监控已在运行中")
            return
            
        if self.target_window_handle is None:
            if not self.find_deltaforce_process():
                print("未找到DeltaForce进程，无法开始监控")
                return
        
        self.is_monitoring = True
        self.monitor_duration = duration
        
        def monitor():
            start_time = time.time()
            while self.is_monitoring and (time.time() - start_time) < self.monitor_duration:
                try:
                    if self.target_window_handle:
                        current_info = get_window_info(self.target_window_handle)
                        
                        # 检查是否有变化
                        if (current_info.get("left") != self.window_x or
                            current_info.get("top") != self.window_y or
                            current_info.get("width") != self.window_width or
                            current_info.get("height") != self.window_height):
                            
                            self._update_window_info()
                            print(f"窗口变化: 位置({self.window_x}, {self.window_y}) 尺寸({self.window_width}, {self.window_height})")
                    
                    time.sleep(0.1)
                except Exception as e:
                    print(f"监控出错: {e}")
                    time.sleep(1)
            
            if self.is_monitoring:
                print("监控时间到，自动停止")
                self.is_monitoring = False
        
        threading.Thread(target=monitor, daemon=True).start()
        print(f"开始监控窗口变化，将持续{duration}秒...")
    
    def stop_monitoring(self):
        """停止监控窗口变化"""
        self.is_monitoring = False
        print("停止监控窗口变化")
    
    def is_process_running(self) -> bool:
        """检查DeltaForce进程是否正在运行"""
        return self.find_deltaforce_process() is not None
    
    def wait_for_process(self, timeout: int = 30) -> bool:
        """等待DeltaForce进程启动"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.find_deltaforce_process():
                return True
            time.sleep(1)
        return False
    
    def get_scaled_size(self) -> Tuple[int, int]:
        """获取乘算后的窗口尺寸（物理尺寸 × DPI缩放因子）
        
        返回:
            tuple: (width, height) 乘算后的窗口尺寸
        """
        if self.target_window_handle is None:
            return (0, 0)
        
        # 乘算后的尺寸 = 物理尺寸 × DPI缩放因子
        scaled_width = int(self.window_width * self.dpi_scale_x)
        scaled_height = int(self.window_height * self.dpi_scale_y)
        
        return (scaled_width, scaled_height)
    
    def get_scaled_position(self) -> Tuple[int, int]:
        """获取乘算后的窗口位置（物理坐标 × DPI缩放因子）
        
        返回:
            tuple: (x, y) 乘算后的窗口坐标
        """
        if self.target_window_handle is None:
            return (0, 0)
        
        # 乘算后的坐标 = 物理坐标 × DPI缩放因子
        scaled_x = int(self.window_x * self.dpi_scale_x)
        scaled_y = int(self.window_y * self.dpi_scale_y)
        
        return (scaled_x, scaled_y)
    
    def ratio_to_screen_coords(self, x_ratio: float, y_ratio: float) -> Tuple[int, int]:
        """将窗口内的比例坐标转换为实际屏幕坐标（物理坐标）
        
        参数:
            x_ratio: X方向比例 (0.0-1.0)
            y_ratio: Y方向比例 (0.0-1.0)
            
        返回:
            tuple: (screen_x, screen_y) 实际屏幕坐标（物理坐标）
            
        示例:
            # 获取窗口中心点的屏幕坐标
            center_x, center_y = df_window.ratio_to_screen_coords(0.5, 0.5)
            
            # 获取窗口右上角的屏幕坐标
            right_top_x, right_top_y = df_window.ratio_to_screen_coords(1.0, 0.0)
        """
        if self.target_window_handle is None:
            print("错误: 未找到游戏窗口，请先调用find_deltaforce_process()")
            return (0, 0)
        
        # 验证比例参数
        if not 0.0 <= x_ratio <= 1.0:
            print(f"错误: X比例值 {x_ratio} 超出范围 [0.0, 1.0]")
            return (0, 0)
        
        if not 0.0 <= y_ratio <= 1.0:
            print(f"错误: Y比例值 {y_ratio} 超出范围 [0.0, 1.0]")
            return (0, 0)
        
        # 更新窗口信息确保数据最新
        self._update_window_info()
        
        # 使用物理坐标（不进行DPI感知转换）
        # 计算窗口内的相对坐标（使用物理尺寸）
        window_relative_x = int(self.window_width * x_ratio)
        window_relative_y = int(self.window_height * y_ratio)
        
        # 转换为物理屏幕坐标（窗口内坐标 + 物理窗口位置）
        screen_x = self.window_x + window_relative_x
        screen_y = self.window_y + window_relative_y
        
        return (screen_x, screen_y)
    
    def switch_to_deltaforce_window(self) -> bool:
        """切换到DeltaForce游戏窗口"""
        if self.target_window_handle is None:
            if not self.find_deltaforce_process():
                return False
        
        try:
            # 使用Windows API将窗口置于前台
            ctypes.windll.user32.SetForegroundWindow(self.target_window_handle)
            # 确保窗口不是最小化状态
            ctypes.windll.user32.ShowWindow(self.target_window_handle, 9)  # SW_RESTORE
            print("切换到游戏窗口")
            return True
        except Exception as e:
            return False
    
    def get_all_deltaforce_windows(self):
        """获取所有DeltaForce窗口信息"""
        try:
            windows = enum_windows()
            deltaforce_windows = []
            
            for hwnd in windows:
                try:
                    win_info = get_window_info(hwnd)
                    if win_info and win_info.get('process_name') == self.target_process_name:
                        deltaforce_windows.append({
                            'hwnd': hwnd,
                            'window_info': win_info
                        })
                except Exception:
                    continue
            
            return deltaforce_windows
        except Exception as e:
            print(f"获取DeltaForce窗口失败: {e}")
            return []
    
    def switch_to_window(self, hwnd):
        """切换到指定的窗口句柄"""
        try:
            import ctypes
            # 设置前台窗口
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            # 确保窗口不是最小化状态
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            
            # 更新当前目标窗口
            self.target_window_handle = hwnd
            
            # 获取窗口信息并更新尺寸
            win_info = get_window_info(hwnd)
            if win_info:
                self.window_width = win_info.get('width', 1920)
                self.window_height = win_info.get('height', 1080)
                self.window_x = win_info.get('x', 0)
                self.window_y = win_info.get('y', 0)
                
                # 将鼠标移动到窗口中心，避免触发PyAutoGUI的fail-safe
                center_x = self.window_x + self.window_width // 2
                center_y = self.window_y + self.window_height // 2
                
                import pyautogui
                pyautogui.moveTo(center_x, center_y)
            
            return True
        except Exception as e:
            print(f"切换窗口失败: {e}")
            return False
    
    def classify_windows_by_size(self, windows):
        """根据窗口大小分类为主窗口和辅窗口"""
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


def print_process_info():
    """打印DeltaForce进程信息"""
    print("=" * 60)
    print("DeltaForce进程信息")
    print("=" * 60)
    
    df_window = DeltaForceWindow()
    
    print("正在查找DeltaForce进程...")
    if df_window.find_deltaforce_process():
        print("✓ 找到DeltaForce进程!")
        
        info = df_window.get_process_info()
        if "error" not in info:
            print(f"\n进程名称: {info['process_name']}")
            print(f"窗口标题: {info['window_title']}")
            print(f"窗口句柄: {info['window_handle']}")
            print(f"\n物理坐标和尺寸 (像素):")
            print(f"  位置: ({info['position'][0]}, {info['position'][1]})")
            print(f"  尺寸: ({info['size'][0]}, {info['size'][1]})")
            print(f"\nDPI缩放因子: {info['dpi_scale'][0]:.2f}x, {info['dpi_scale'][1]:.2f}x")
            
            print(f"\n实例属性:")
            print(f"  窗口句柄: {df_window.target_window_handle}")
            print(f"  物理位置: ({df_window.window_x}, {df_window.window_y})")
            print(f"  物理尺寸: ({df_window.window_width}, {df_window.window_height})")
            print(f"  DPI缩放: ({df_window.dpi_scale_x:.2f}x, {df_window.dpi_scale_y:.2f}x)")
            
            # 显示乘算后的尺寸和坐标
            scaled_size = df_window.get_scaled_size()
            scaled_position = df_window.get_scaled_position()
            print(f"\n乘算后的尺寸和坐标:")
            print(f"  乘算后位置: ({scaled_position[0]}, {scaled_position[1]})")
            print(f"  乘算后尺寸: ({scaled_size[0]}, {scaled_size[1]})")
            
            print(f"\n开始监控窗口变化...")
            df_window.start_monitoring(duration=10)
            
            while df_window.is_monitoring:
                time.sleep(0.1)
            
        else:
            print(f"获取进程信息失败: {info['error']}")
    else:
        print("✗ 未找到DeltaForce进程")
        print("\n可能的原因:")
        print("1. DeltaForce游戏未启动")
        print("2. 进程名称不匹配")
        print("3. 权限不足")
        
        print("\n当前可见窗口列表:")
        try:
            windows = enum_windows()
            for i, (hwnd, title, process) in enumerate(windows[:10]):
                print(f"  {i+1}. {process} - {title}")
            if len(windows) > 10:
                print(f"  ... 还有 {len(windows) - 10} 个窗口")
        except Exception as e:
            print(f"  无法获取窗口列表: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    print_process_info()

