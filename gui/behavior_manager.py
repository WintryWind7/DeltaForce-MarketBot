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
    from DeltaForce import DeltaForceManager, DeltaForceClass
except ImportError:
    from DeltaForceManager import DeltaForceManager
    from DeltaForceClass import DeltaForceClass

class BehaviorManager:
    """行为管理器 - 统一管理所有行为和Delta实例"""
    
    def __init__(self):
        self.behavior_dir = os.path.join(os.path.dirname(__file__), 'behavior')
        self.behaviors = {}
        self.delta_manager = None
        self.single_delta = None
        self.load_behaviors()
    
    def initialize_delta_management(self, window_handles):
        """
        初始化Delta管理
        根据窗口数量决定使用单端还是双端管理
        """
        if not window_handles:
            return False
        
        try:
            if len(window_handles) >= 2:
                # 双端模式：使用DeltaForceManager
                self.delta_manager = DeltaForceManager(window_handles)
                if self.delta_manager.is_initialized:
                    return True
                else:
                    return False
            else:
                # 单端模式：使用单个DeltaForceClass
                self.single_delta = DeltaForceClass()
                if self.single_delta.bind_to_window(window_handles[0]):
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Delta管理初始化失败: {e}")
            return False
    
    def get_delta_for_behavior(self, behavior_type="single"):
        """
        为行为获取适当的Delta实例
        Args:
            behavior_type: "single" 单端, "dual" 双端, "main" 主端, "aux" 辅端
        Returns:
            Delta实例或Manager
        """
        if behavior_type == "single" or behavior_type == "main":
            if self.delta_manager:
                return self.delta_manager.get_main()
            else:
                return self.single_delta
        elif behavior_type == "aux":
            if self.delta_manager:
                return self.delta_manager.get_auxiliary()
            else:
                return None
        elif behavior_type == "dual":
            return self.delta_manager
        else:
            # 默认返回主端或单端
            if self.delta_manager:
                return self.delta_manager.get_main()
            else:
                return self.single_delta
    
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
            behavior_instance = behavior_class(window_handles, config)
            
            # 如果行为实例有set_delta_manager方法，注入Delta管理器
            if hasattr(behavior_instance, 'set_delta_manager'):
                if self.delta_manager:
                    behavior_instance.set_delta_manager(self.delta_manager)
                elif self.single_delta:
                    behavior_instance.set_delta_manager(self.single_delta)
            
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
    
    def load_behaviors(self):
        """加载所有behavior模块"""
        self.behaviors = {}
        
        if not os.path.exists(self.behavior_dir):
            return
        
        # 遍历behavior目录中的所有.py文件
        for filename in os.listdir(self.behavior_dir):
            if filename.endswith('_behavior.py') and filename != '__init__.py':
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
        """获取行为列表，按标题排序"""
        behavior_list = []
        for behavior_id, info in self.behaviors.items():
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
