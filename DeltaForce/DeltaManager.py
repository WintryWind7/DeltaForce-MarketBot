# -*- coding: utf-8 -*-
"""
DeltaManager - 主辅端Delta管理器
正式的主辅端Delta实例管理器，支持动态句柄绑定和Behavior集成
"""

from typing import List, Dict, Optional, Tuple
# 尝试相对导入，如果失败则使用绝对导入
try:
    from .DeltaForceClass import DeltaForceClass
except ImportError:
    from DeltaForceClass import DeltaForceClass


class DeltaManager:
    """
    DeltaManager - 正式的主辅端Delta管理器
    
    负责管理主辅两个DeltaForce实例，支持动态句柄绑定和Behavior集成。
    启动时创建两个Delta实例，等待UI传递句柄进行绑定。
    
    使用方式：
        # 创建管理器（自动启动两个Delta实例）
        manager = DeltaManager()
        
        # UI传递句柄进行绑定
        manager.bind_handles([hwnd1, hwnd2])
        
        # Behavior获取实例
        main_delta = manager.get_main()     # 单端使用
        main, aux = manager.get_both()      # 双端使用
    """
    
    def __init__(self):
        """
        初始化Delta管理器
        自动创建两个Delta实例，等待句柄绑定
        """
        # 创建两个Delta实例
        self.main_delta: DeltaForceClass = DeltaForceClass()
        self.aux_delta: DeltaForceClass = DeltaForceClass()
        
        # 绑定状态
        self.main_bound = False
        self.aux_bound = False
        self.window_info: Dict[int, Dict] = {}  # 存储窗口信息 {hwnd: window_info}
        
        print("✅ DeltaManager初始化完成，已创建主辅Delta实例")
    
    def bind_handles(self, window_handles: List[int]) -> bool:
        """
        绑定窗口句柄到Delta实例
        
        Args:
            window_handles: 窗口句柄列表
            
        Returns:
            bool: 绑定是否成功
        """
        try:
            if len(window_handles) < 1:
                print("❌ 至少需要一个窗口句柄")
                return False
            
            if len(window_handles) > 2:
                print(f"⚠️ 检测到{len(window_handles)}个窗口，只使用前两个")
                window_handles = window_handles[:2]
            
            # 重置绑定状态
            self.main_bound = False
            self.aux_bound = False
            self.window_info.clear()
            
            # 收集窗口信息用于分类
            window_infos = []
            
            for hwnd in window_handles:
                try:
                    # 创建临时Delta实例获取窗口信息
                    temp_delta = DeltaForceClass()
                    temp_delta.target_window_handle = hwnd
                    temp_delta._update_window_info()
                    
                    if temp_delta.window_width <= 0 or temp_delta.window_height <= 0:
                        print(f"⚠️ 窗口 {hwnd} 信息无效: {temp_delta.window_width}x{temp_delta.window_height}")
                        continue
                    
                    window_info = {
                        'hwnd': hwnd,
                        'width': temp_delta.window_width,
                        'height': temp_delta.window_height,
                        'x': temp_delta.window_x,
                        'y': temp_delta.window_y,
                        'area': temp_delta.window_width * temp_delta.window_height
                    }
                    
                    window_infos.append(window_info)
                    self.window_info[hwnd] = window_info
                    
                except Exception as e:
                    print(f"❌ 获取窗口 {hwnd} 信息时出错: {e}")
                    continue
            
            if len(window_infos) == 0:
                print("❌ 没有获取到有效的窗口信息")
                return False
            
            # 根据窗口大小分配主辅角色并绑定
            success = self._bind_by_size(window_infos)
            
            if success:
                print(f"🎯 DeltaManager绑定完成，主窗口: {self.main_delta.target_window_handle if self.main_bound else 'None'}, 辅窗口: {self.aux_delta.target_window_handle if self.aux_bound else 'None'}")
            
            return success
            
        except Exception as e:
            print(f"❌ DeltaManager绑定失败: {e}")
            return False
    
    def _bind_by_size(self, window_infos: List[Dict]) -> bool:
        """
        根据窗口大小分配主辅角色并绑定到Delta实例
        
        Args:
            window_infos: 窗口信息列表
            
        Returns:
            bool: 绑定是否成功
        """
        try:
            if len(window_infos) == 1:
                # 单窗口模式，绑定到主Delta
                hwnd = window_infos[0]['hwnd']
                success = self._bind_delta_to_window(self.main_delta, hwnd)
                if success:
                    self.main_bound = True
                    print(f"📱 单窗口模式，主窗口: {hwnd}")
                return success
                
            elif len(window_infos) >= 2:
                # 双窗口模式，按面积大小分配（小的是主，大的是辅）
                sorted_windows = sorted(window_infos, key=lambda x: x['area'])
                
                main_hwnd = sorted_windows[0]['hwnd']  # 较小的窗口作为主窗口
                aux_hwnd = sorted_windows[1]['hwnd']   # 较大的窗口作为辅窗口
                
                # 绑定主窗口
                main_success = self._bind_delta_to_window(self.main_delta, main_hwnd)
                if main_success:
                    self.main_bound = True
                
                # 绑定辅窗口
                aux_success = self._bind_delta_to_window(self.aux_delta, aux_hwnd)
                if aux_success:
                    self.aux_bound = True
                
                if main_success and aux_success:
                    main_info = sorted_windows[0]
                    aux_info = sorted_windows[1]
                    print(f"🎯 双窗口模式绑定完成:")
                    print(f"   主窗口: {main_info['hwnd']} (面积: {main_info['area']})")
                    print(f"   辅窗口: {aux_info['hwnd']} (面积: {aux_info['area']})")
                    return True
                elif main_success:
                    print(f"⚠️ 只成功绑定主窗口: {main_hwnd}")
                    return True
                else:
                    print("❌ 主辅窗口绑定都失败")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ 窗口绑定失败: {e}")
            return False
    
    def _bind_delta_to_window(self, delta: DeltaForceClass, hwnd: int) -> bool:
        """
        将Delta实例绑定到指定窗口
        
        Args:
            delta: Delta实例
            hwnd: 窗口句柄
            
        Returns:
            bool: 绑定是否成功
        """
        try:
            # 设置目标窗口句柄
            delta.target_window_handle = hwnd
            
            # 更新窗口信息
            delta._update_window_info()
            
            # 验证窗口信息是否有效
            if delta.window_width <= 0 or delta.window_height <= 0:
                print(f"⚠️ 窗口 {hwnd} 信息无效: {delta.window_width}x{delta.window_height}")
                return False
            
            print(f"✅ 成功绑定窗口 {hwnd} (尺寸: {delta.window_width}x{delta.window_height})")
            return True
            
        except Exception as e:
            print(f"❌ 绑定窗口 {hwnd} 失败: {e}")
            return False
    
    def get_main(self) -> Optional[DeltaForceClass]:
        """
        获取主窗口Delta实例（单端使用）
        
        Returns:
            DeltaForceClass: 主窗口实例，如果未绑定则返回None
        """
        if self.main_bound:
            return self.main_delta
        else:
            print("⚠️ 主窗口未绑定")
            return None
    
    def get_aux(self) -> Optional[DeltaForceClass]:
        """
        获取辅窗口Delta实例
        
        Returns:
            DeltaForceClass: 辅窗口实例，如果未绑定则返回None
        """
        if self.aux_bound:
            return self.aux_delta
        else:
            print("⚠️ 辅窗口未绑定")
            return None
    
    def get_both(self) -> Tuple[Optional[DeltaForceClass], Optional[DeltaForceClass]]:
        """
        同时获取主辅窗口实例（双端使用）
        
        Returns:
            Tuple: (主窗口实例, 辅窗口实例)
        """
        main = self.main_delta if self.main_bound else None
        aux = self.aux_delta if self.aux_bound else None
        return main, aux
    
    def has_main(self) -> bool:
        """检查是否有主窗口绑定"""
        return self.main_bound
    
    def has_aux(self) -> bool:
        """检查是否有辅窗口绑定"""
        return self.aux_bound
    
    def is_single_mode(self) -> bool:
        """检查是否为单端模式"""
        return self.main_bound and not self.aux_bound
    
    def is_dual_mode(self) -> bool:
        """检查是否为双端模式"""
        return self.main_bound and self.aux_bound
    
    def get_bound_count(self) -> int:
        """获取已绑定的窗口数量"""
        count = 0
        if self.main_bound:
            count += 1
        if self.aux_bound:
            count += 1
        return count
    
    def get_status_summary(self) -> Dict:
        """
        获取状态摘要
        
        Returns:
            Dict: 包含绑定状态的字典
        """
        summary = {
            'main_bound': self.main_bound,
            'aux_bound': self.aux_bound,
            'bound_count': self.get_bound_count(),
            'mode': 'dual' if self.is_dual_mode() else 'single' if self.is_single_mode() else 'none',
            'main_window': None,
            'aux_window': None
        }
        
        if self.main_bound:
            summary['main_window'] = {
                'hwnd': self.main_delta.target_window_handle,
                'size': f"{self.main_delta.window_width}x{self.main_delta.window_height}",
                'position': f"({self.main_delta.window_x}, {self.main_delta.window_y})"
            }
        
        if self.aux_bound:
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
        if not self.main_bound:
            print("❌ 主窗口未绑定")
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
        if not self.aux_bound:
            print("❌ 辅窗口未绑定")
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
        if not (self.main_bound or self.aux_bound):
            return "DeltaManager(未绑定)"
        
        main_hwnd = self.main_delta.target_window_handle if self.main_bound else "None"
        aux_hwnd = self.aux_delta.target_window_handle if self.aux_bound else "None"
        
        return f"DeltaManager(主窗口: {main_hwnd}, 辅窗口: {aux_hwnd})"


# 全局单例实例
_delta_manager_instance: Optional[DeltaManager] = None

def get_delta_manager() -> DeltaManager:
    """
    获取全局DeltaManager单例实例
    
    Returns:
        DeltaManager: 全局单例实例
    """
    global _delta_manager_instance
    if _delta_manager_instance is None:
        _delta_manager_instance = DeltaManager()
    return _delta_manager_instance

def reset_delta_manager():
    """重置全局DeltaManager实例"""
    global _delta_manager_instance
    _delta_manager_instance = None


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("DeltaManager 测试")
    print("=" * 60)
    
    # 测试创建管理器
    manager = DeltaManager()
    print(f"\n管理器状态: {manager}")
    
    # 显示状态摘要
    summary = manager.get_status_summary()
    print(f"\n📊 状态摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("=" * 60)
