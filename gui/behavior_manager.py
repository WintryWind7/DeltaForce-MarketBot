# -*- coding: utf-8 -*-
"""
行为管理器 - 动态加载和管理behavior模块
提供统一的Delta类管理和行为接口
"""

import os
import importlib.util
import sys
from typing import Dict, List, Any, Optional

# 添加DeltaForce路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'DeltaForce'))

try:
    from DeltaForce.DeltaManager import get_delta_manager
    from DeltaForce.DeltaForceClass import DeltaForceClass
except ImportError:
    from DeltaManager import get_delta_manager
    from DeltaForceClass import DeltaForceClass

class BehaviorManager:
    """行为管理器 - 统一管理所有行为和Delta实例"""
    
    def __init__(self):
        self.behavior_dir = os.path.join(os.path.dirname(__file__), 'behavior')
        self.behaviors = {}
        self.delta_manager = get_delta_manager()  # 获取全局DeltaManager实例
        self.load_behaviors()
    
    def initialize_delta_management(self, window_handles):
        """
        初始化Delta管理 - 绑定窗口句柄到全局DeltaManager
        """
        if not window_handles:
            print("❌ 未提供窗口句柄")
            return False
        
        try:
            # 绑定窗口句柄到全局DeltaManager
            success = self.delta_manager.bind_handles(window_handles)
            if success:
                print(f"✅ BehaviorManager成功绑定{len(window_handles)}个窗口到DeltaManager")
                return True
            else:
                print("❌ BehaviorManager窗口绑定失败")
                return False
                    
        except Exception as e:
            print(f"❌ BehaviorManager Delta管理初始化失败: {e}")
            return False
    
    def get_delta_for_behavior(self, behavior_type="single"):
        """
        为行为获取适当的Delta实例（已弃用 - 现在Behavior直接使用DeltaManager）
        Args:
            behavior_type: "single" 单端, "dual" 双端, "main" 主端, "aux" 辅端
        Returns:
            Delta实例或Manager
        """
        # 注意：此方法已弃用，现在Behavior直接从DeltaManager获取实例
        # 保留此方法仅为向后兼容
        if behavior_type == "single" or behavior_type == "main":
            return self.delta_manager.get_main()
        elif behavior_type == "aux":
            return self.delta_manager.get_aux()
        elif behavior_type == "dual":
            return self.delta_manager
        else:
            # 默认返回主端
            return self.delta_manager.get_main()
    
    def create_behavior_instance(self, behavior_id: str, window_handles: List[int], config: Dict = None):
        """
        创建行为实例的统一接口
        自动处理Delta管理和依赖注入
        """
        if behavior_id not in self.behaviors:
            return None
        
        # 初始化Delta管理
        if not self.initialize_delta_management(window_handles):
            print("Delta管理初始化失败")
            return None
        
        # 获取行为类
        behavior_class = self.get_behavior_class(behavior_id)
        if not behavior_class:
            return None
        
        try:
            # 创建行为实例
            # 注意：Behavior会自动从全局DeltaManager获取Delta实例，无需手动注入
            behavior_instance = behavior_class(window_handles, config)
            
            # 添加窗口预切换功能
            self._add_window_pre_switch(behavior_instance, window_handles)
            
            # 确保所有行为都有stop_behavior方法
            if not hasattr(behavior_instance, 'stop_behavior'):
                # 动态添加stop_behavior方法
                def stop_behavior():
                    behavior_instance.should_stop = True
                    if hasattr(behavior_instance, 'log_message'):
                        behavior_instance.log_message.emit("🛑 正在停止行为...")
                    if behavior_instance.isRunning():
                        behavior_instance.wait(5000)
                    if hasattr(behavior_instance, 'log_message'):
                        behavior_instance.log_message.emit("✅ 行为已完全停止")
                
                behavior_instance.stop_behavior = stop_behavior
            
            return behavior_instance
            
        except Exception as e:
            print(f"创建行为实例失败: {e}")
            return None
    
    def _add_window_pre_switch(self, behavior_instance, window_handles):
        """
        为行为实例添加窗口预切换功能
        在原有run方法前添加窗口切换和等待逻辑
        """
        import time
        
        # 保存原始的run方法
        original_run = behavior_instance.run
        
        def enhanced_run():
            try:
                # 发送日志消息（如果支持）
                if hasattr(behavior_instance, 'log_message'):
                    behavior_instance.log_message.emit("🔄 [窗口管理] 准备切换到目标窗口...")
                
                # 保持原有的3秒停顿
                if hasattr(behavior_instance, 'log_message'):
                    behavior_instance.log_message.emit("⏱️ [窗口管理] 等待3秒后开始执行...")
                time.sleep(3.0)
                
                # 切换到指定窗口
                success = self._switch_to_target_window(behavior_instance, window_handles)
                
                if success:
                    if hasattr(behavior_instance, 'log_message'):
                        behavior_instance.log_message.emit("✅ [窗口管理] 窗口切换成功，等待1秒稳定...")
                    # 等待1秒让窗口稳定
                    time.sleep(1.0)
                    
                    if hasattr(behavior_instance, 'log_message'):
                        behavior_instance.log_message.emit("🚀 [窗口管理] 开始执行行为...")
                else:
                    if hasattr(behavior_instance, 'log_message'):
                        behavior_instance.log_message.emit("⚠️ [窗口管理] 窗口切换失败，但继续执行...")
                
                # 调用原始的run方法
                return original_run()
                
            except Exception as e:
                if hasattr(behavior_instance, 'log_message'):
                    behavior_instance.log_message.emit(f"❌ [窗口管理] 预处理失败: {e}")
                # 即使预处理失败，也尝试执行原始run方法
                return original_run()
        
        # 替换run方法
        behavior_instance.run = enhanced_run
    
    def _switch_to_target_window(self, behavior_instance, window_handles):
        """
        切换到目标窗口
        """
        try:
            if not window_handles:
                return False
            
            # 获取主窗口句柄
            target_handle = window_handles[0]
            
            # 尝试通过Delta实例切换窗口
            if hasattr(behavior_instance, 'delta') and behavior_instance.delta:
                if hasattr(behavior_instance.delta, 'focus_window'):
                    return behavior_instance.delta.focus_window()
            
            # 如果没有Delta实例，尝试直接使用Windows API
            try:
                import ctypes
                # 将窗口置于前台
                ctypes.windll.user32.SetForegroundWindow(target_handle)
                # 确保窗口不是最小化状态
                ctypes.windll.user32.ShowWindow(target_handle, 9)  # SW_RESTORE
                return True
            except Exception as api_error:
                if hasattr(behavior_instance, 'log_message'):
                    behavior_instance.log_message.emit(f"⚠️ [窗口管理] Windows API切换失败: {api_error}")
                return False
                
        except Exception as e:
            if hasattr(behavior_instance, 'log_message'):
                behavior_instance.log_message.emit(f"❌ [窗口管理] 切换窗口时发生错误: {e}")
            return False
    
    def load_behaviors(self):
        """加载所有behavior模块"""
        self.behaviors = {}
        
        if not os.path.exists(self.behavior_dir):
            return
        
        # 遍历behavior目录中的所有.py文件
        for filename in os.listdir(self.behavior_dir):
            # 匹配 _behavior.py 结尾的文件或者 S、D、T 开头的代码ID文件（如SMB000X.py、DMR000X.py、SSS000X.py、SPR000X.py、TEST919G.py等）
            if ((filename.endswith('_behavior.py') or 
                 (filename.startswith(('S', 'D', 'T')) and filename.endswith('.py'))) and 
                filename != '__init__.py'):
                behavior_id = filename[:-3]  # 移除.py扩展名
                
                try:
                    # 动态导入模块
                    module_path = os.path.join(self.behavior_dir, filename)
                    spec = importlib.util.spec_from_file_location(behavior_id, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 检查是否有BEHAVIOR_INFO
                    if hasattr(module, 'BEHAVIOR_INFO'):
                        behavior_info = module.BEHAVIOR_INFO
                        
                        # 验证必需字段
                        required_fields = ['title', 'description']
                        if all(field in behavior_info for field in required_fields):
                            # 添加模块信息
                            behavior_info['module'] = module
                            behavior_info['id'] = behavior_id
                            behavior_info['filename'] = filename
                            
                            self.behaviors[behavior_id] = behavior_info
                        else:
                            print(f"警告: {filename} 缺少必需的BEHAVIOR_INFO字段")
                    else:
                        print(f"警告: {filename} 没有定义BEHAVIOR_INFO")
                        
                except Exception as e:
                    print(f"加载行为模块 {filename} 失败: {e}")
    
    def get_behaviors(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的行为"""
        return self.behaviors
    
    def get_behavior_info(self, behavior_id: str) -> Dict[str, Any]:
        """获取指定行为的信息"""
        return self.behaviors.get(behavior_id, {})
    
    def get_behavior_class(self, behavior_id: str):
        """获取指定行为的类"""
        if behavior_id not in self.behaviors:
            return None
        
        module = self.behaviors[behavior_id]['module']
        
        # 优先检查模块是否有get_behavior_class函数
        if hasattr(module, 'get_behavior_class'):
            try:
                return module.get_behavior_class()
            except Exception as e:
                print(f"调用 {behavior_id} 的 get_behavior_class 函数失败: {e}")
        
        # 查找行为类（通常以Behavior结尾）
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                attr_name.endswith('Behavior') and 
                attr_name != 'QThread'):
                return attr
        
        return None
    
    def reload_behaviors(self):
        """重新加载所有行为模块"""
        self.load_behaviors()
    
    def get_behavior_list(self) -> List[Dict[str, Any]]:
        """获取行为列表，按标题排序（过滤掉模板行为）"""
        behavior_list = []
        for behavior_id, info in self.behaviors.items():
            # 过滤掉模板行为（template_behavior）
            if behavior_id == 'template_behavior':
                continue
                
            behavior_list.append({
                'id': behavior_id,
                'title': info['title'],
                'description': info['description'],
                'version': info.get('version', '1.0.0'),
                'author': info.get('author', 'Unknown'),
                'tags': info.get('tags', [])
            })
        
        # 按标题排序
        behavior_list.sort(key=lambda x: x['title'])
        return behavior_list
