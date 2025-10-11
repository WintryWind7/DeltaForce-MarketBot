# -*- coding: utf-8 -*-
"""
行为管理器 - 动态加载和管理behavior模块
"""

import os
import importlib.util
import sys
from typing import Dict, List, Any

class BehaviorManager:
    """行为管理器"""
    
    def __init__(self):
        self.behavior_dir = os.path.join(os.path.dirname(__file__), 'behavior')
        self.behaviors = {}
        self.load_behaviors()
    
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
                'author': info.get('author', 'Unknown')
            })
        
        # 按标题排序
        behavior_list.sort(key=lambda x: x['title'])
        return behavior_list
