# -*- coding: utf-8 -*-
"""
DeltaForce双窗口管理器
用于管理主辅两个DeltaForce实例，自动识别主辅角色
"""

from typing import List, Dict, Optional, Tuple
from DeltaForceClass import DeltaForceClass


class DeltaForceManager:
    """
    DeltaForce双窗口管理器
    
    负责管理主辅两个DeltaForce窗口实例，每个实例绑定到特定的窗口句柄。
    自动识别哪个是主窗口（较小）、哪个是辅窗口（较大）。
    
    使用方式：
        # 从UI获取窗口句柄列表
        hwnds = [hwnd1, hwnd2]  # UI传递的句柄列表
        
        # 创建管理器并自动分配主辅角色
        manager = DeltaForceManager(hwnds)
        
        # 获取主辅实例
        main_delta = manager.get_main()
        aux_delta = manager.get_aux()
        
        # 或者直接获取两个实例
        main, aux = manager.get_instances()
    """
    
    def __init__(self, window_handles: List[int] = None):
        """
        初始化DeltaForce管理器
        
        Args:
            window_handles: 窗口句柄列表，如果为None则需要后续调用initialize()
        """
        self.main_delta: Optional[DeltaForceClass] = None
        self.aux_delta: Optional[DeltaForceClass] = None
        self.window_info: Dict[int, Dict] = {}  # 存储窗口信息 {hwnd: window_info}
        self.is_initialized = False
        
        if window_handles:
            self.initialize(window_handles)
    
    def initialize(self, window_handles: List[int]) -> bool:
        """
        使用窗口句柄列表初始化管理器
        
        Args:
            window_handles: 窗口句柄列表
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            if len(window_handles) < 1:
                print("❌ 至少需要一个窗口句柄")
                return False
            
            if len(window_handles) > 2:
                print(f"⚠️ 检测到{len(window_handles)}个窗口，只使用前两个")
                window_handles = window_handles[:2]
            
            # 为每个句柄创建DeltaForce实例并获取窗口信息
            instances_info = []
            
            for hwnd in window_handles:
                try:
                    # 创建专用于该窗口的DeltaForce实例
                    delta = DeltaForceClass()
                    
                    # 绑定到指定窗口（不切换，只获取信息）
                    success = self._bind_to_window(delta, hwnd)
                    if not success:
                        print(f"❌ 绑定窗口失败: {hwnd}")
                        continue
                    
                    # 获取窗口信息
                    window_info = {
                        'hwnd': hwnd,
                        'width': delta.window_width,
                        'height': delta.window_height,
                        'x': delta.window_x,
                        'y': delta.window_y,
                        'area': delta.window_width * delta.window_height
                    }
                    
                    instances_info.append({
                        'delta': delta,
                        'hwnd': hwnd,
                        'window_info': window_info
                    })
                    
                    self.window_info[hwnd] = window_info
                    print(f"✅ 成功绑定窗口 {hwnd} (尺寸: {window_info['width']}x{window_info['height']})")
                    
                except Exception as e:
                    print(f"❌ 处理窗口 {hwnd} 时出错: {e}")
                    continue
            
            if len(instances_info) == 0:
                print("❌ 没有成功绑定任何窗口")
                return False
            
            # 根据窗口大小分配主辅角色
            self._assign_roles(instances_info)
            
            self.is_initialized = True
            print(f"🎯 DeltaForceManager初始化完成，主窗口: {self.main_delta.target_window_handle if self.main_delta else 'None'}, 辅窗口: {self.aux_delta.target_window_handle if self.aux_delta else 'None'}")
            return True
            
        except Exception as e:
            print(f"❌ DeltaForceManager初始化失败: {e}")
            return False
    
    def _bind_to_window(self, delta: DeltaForceClass, hwnd: int) -> bool:
        """
        将DeltaForce实例绑定到指定窗口（不切换焦点，只获取信息）
        
        Args:
            delta: DeltaForce实例
            hwnd: 窗口句柄
            
        Returns:
            bool: 绑定是否成功
        """
        try:
            # 直接设置目标窗口句柄
            delta.target_window_handle = hwnd
            
            # 更新窗口信息（不切换焦点）
            delta._update_window_info()
            
            # 验证窗口信息是否有效
            if delta.window_width <= 0 or delta.window_height <= 0:
                print(f"⚠️ 窗口 {hwnd} 信息无效: {delta.window_width}x{delta.window_height}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 绑定窗口 {hwnd} 失败: {e}")
            return False
    
    def _assign_roles(self, instances_info: List[Dict]) -> None:
        """
        根据窗口大小分配主辅角色
        
        Args:
            instances_info: 实例信息列表
        """
        if len(instances_info) == 1:
            # 只有一个窗口，设为主窗口
            self.main_delta = instances_info[0]['delta']
            self.aux_delta = None
            print(f"📱 单窗口模式，主窗口: {instances_info[0]['hwnd']}")
            
        elif len(instances_info) == 2:
            # 两个窗口，按面积大小分配（小的是主，大的是辅）
            sorted_instances = sorted(instances_info, key=lambda x: x['window_info']['area'])
            
            self.main_delta = sorted_instances[0]['delta']  # 较小的窗口作为主窗口
            self.aux_delta = sorted_instances[1]['delta']   # 较大的窗口作为辅窗口
            
            main_info = sorted_instances[0]['window_info']
            aux_info = sorted_instances[1]['window_info']
            
            print(f"🎯 双窗口模式分配完成:")
            print(f"   主窗口: {main_info['hwnd']} (面积: {main_info['area']})")
            print(f"   辅窗口: {aux_info['hwnd']} (面积: {aux_info['area']})")
    
    def get_main(self) -> Optional[DeltaForceClass]:
        """
        获取主窗口DeltaForce实例
        
        Returns:
            DeltaForceClass: 主窗口实例，如果不存在则返回None
        """
        if not self.is_initialized:
            print("⚠️ 管理器未初始化，请先调用initialize()")
            return None
        return self.main_delta
    
    def get_aux(self) -> Optional[DeltaForceClass]:
        """
        获取辅窗口DeltaForce实例
        
        Returns:
            DeltaForceClass: 辅窗口实例，如果不存在则返回None
        """
        if not self.is_initialized:
            print("⚠️ 管理器未初始化，请先调用initialize()")
            return None
        return self.aux_delta
    
    def get_instances(self) -> Tuple[Optional[DeltaForceClass], Optional[DeltaForceClass]]:
        """
        同时获取主辅窗口实例
        
        Returns:
            Tuple: (主窗口实例, 辅窗口实例)
        """
        return self.get_main(), self.get_aux()
    
    def has_main(self) -> bool:
        """检查是否有主窗口"""
        return self.main_delta is not None
    
    def has_aux(self) -> bool:
        """检查是否有辅窗口"""
        return self.aux_delta is not None
    
    def get_window_count(self) -> int:
        """获取管理的窗口数量"""
        count = 0
        if self.main_delta:
            count += 1
        if self.aux_delta:
            count += 1
        return count
    
    def get_window_info_summary(self) -> Dict:
        """
        获取窗口信息摘要
        
        Returns:
            Dict: 包含主辅窗口信息的字典
        """
        summary = {
            'initialized': self.is_initialized,
            'window_count': self.get_window_count(),
            'main_window': None,
            'aux_window': None
        }
        
        if self.main_delta:
            summary['main_window'] = {
                'hwnd': self.main_delta.target_window_handle,
                'size': f"{self.main_delta.window_width}x{self.main_delta.window_height}",
                'position': f"({self.main_delta.window_x}, {self.main_delta.window_y})"
            }
        
        if self.aux_delta:
            summary['aux_window'] = {
                'hwnd': self.aux_delta.target_window_handle,
                'size': f"{self.aux_delta.window_width}x{self.aux_delta.window_height}",
                'position': f"({self.aux_delta.window_x}, {self.aux_delta.window_y})"
            }
        
        return summary
    
    def focus_main(self) -> bool:
        """
        聚焦主窗口
        
        Returns:
            bool: 聚焦是否成功
        """
        if not self.main_delta:
            print("❌ 主窗口不存在")
            return False
        
        try:
            import ctypes
            hwnd = self.main_delta.target_window_handle
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            print(f"✅ 已聚焦主窗口: {hwnd}")
            return True
        except Exception as e:
            print(f"❌ 聚焦主窗口失败: {e}")
            return False
    
    def focus_aux(self) -> bool:
        """
        聚焦辅窗口
        
        Returns:
            bool: 聚焦是否成功
        """
        if not self.aux_delta:
            print("❌ 辅窗口不存在")
            return False
        
        try:
            import ctypes
            hwnd = self.aux_delta.target_window_handle
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            print(f"✅ 已聚焦辅窗口: {hwnd}")
            return True
        except Exception as e:
            print(f"❌ 聚焦辅窗口失败: {e}")
            return False
    
    def __str__(self) -> str:
        """字符串表示"""
        if not self.is_initialized:
            return "DeltaForceManager(未初始化)"
        
        main_hwnd = self.main_delta.target_window_handle if self.main_delta else "None"
        aux_hwnd = self.aux_delta.target_window_handle if self.aux_delta else "None"
        
        return f"DeltaForceManager(主窗口: {main_hwnd}, 辅窗口: {aux_hwnd})"


# 便利函数：从UI获取句柄并创建管理器
def create_manager_from_ui() -> Optional[DeltaForceManager]:
    """
    从UI获取窗口句柄并创建管理器
    
    Returns:
        DeltaForceManager: 初始化好的管理器，失败时返回None
    """
    try:
        # 导入UI的窗口获取函数
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'gui'))
        
        from window_utils import get_all_deltaforce_windows
        
        # 获取所有DeltaForce窗口
        windows = get_all_deltaforce_windows()
        if not windows:
            print("❌ 未找到DeltaForce窗口")
            return None
        
        # 提取句柄列表
        hwnds = [window['hwnd'] for window in windows]
        
        # 创建并初始化管理器
        manager = DeltaForceManager()
        if manager.initialize(hwnds):
            return manager
        else:
            return None
            
    except Exception as e:
        print(f"❌ 从UI创建管理器失败: {e}")
        return None


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("DeltaForceManager 测试")
    print("=" * 60)
    
    # 测试从UI创建管理器
    manager = create_manager_from_ui()
    
    if manager:
        print("\n✅ 管理器创建成功!")
        print(f"管理器状态: {manager}")
        
        # 显示详细信息
        summary = manager.get_window_info_summary()
        print(f"\n📊 窗口信息摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # 测试获取实例
        main_delta = manager.get_main()
        aux_delta = manager.get_aux()
        
        if main_delta:
            print(f"\n🎯 主窗口实例: {main_delta.target_window_handle}")
        if aux_delta:
            print(f"🎯 辅窗口实例: {aux_delta.target_window_handle}")
            
    else:
        print("❌ 管理器创建失败")
    
    print("=" * 60)
