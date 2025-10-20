# -*- coding: utf-8 -*-
"""
任务日志管理器
用于记录和管理脚本运行的统计数据，采用JSON格式存储
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

class TaskLogger:
    """任务日志管理器 - 内存友好型设计"""
    
    def __init__(self, log_file_path: str = None):
        """
        初始化任务日志管理器
        
        Args:
            log_file_path: 日志文件路径，默认为 log/task_history.json
        """
        if log_file_path is None:
            log_dir = os.path.join(os.getcwd(), "log")
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = os.path.join(log_dir, "task_history.json")
        
        self.log_file_path = log_file_path
        self.lock = threading.Lock()  # 线程安全
        self.max_records = 20  # 最多保留20条记录
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('tasks', [])
            return []
        except Exception as e:
            print(f"加载任务历史失败: {e}")
            return []
    
    def _save_history(self, tasks: List[Dict[str, Any]]) -> bool:
        """保存历史记录"""
        try:
            # 只保留最新的记录，内存友好
            if len(tasks) > self.max_records:
                tasks = tasks[-self.max_records:]
            
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "total_records": len(tasks),
                "tasks": tasks
            }
            
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存任务历史失败: {e}")
            return False
    
    def add_task_record(self, script_id: str, task_data: Dict[str, Any]) -> bool:
        """
        添加任务记录
        
        Args:
            script_id: 脚本ID (如 SMB000X, DMR000X)
            task_data: 任务统计数据
            
        Returns:
            bool: 是否保存成功
        """
        with self.lock:
            try:
                # 创建任务记录
                record = {
                    "task_id": f"{script_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "script_id": script_id,
                    "start_time": task_data.get('start_time'),
                    "end_time": datetime.now().isoformat(),
                    "duration": task_data.get('duration', 0),
                    "status": task_data.get('status', 'completed'),
                    "statistics": task_data.get('statistics', {}),
                    "summary": task_data.get('summary', '')
                }
                
                # 加载现有记录
                tasks = self._load_history()
                
                # 添加新记录
                tasks.append(record)
                
                # 保存记录
                return self._save_history(tasks)
                
            except Exception as e:
                print(f"添加任务记录失败: {e}")
                return False
    
    def get_recent_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取最近的任务记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            List[Dict]: 任务记录列表，按时间倒序
        """
        with self.lock:
            tasks = self._load_history()
            # 按时间倒序排列，返回最新的记录
            tasks.sort(key=lambda x: x.get('end_time', ''), reverse=True)
            return tasks[:limit]
    
    def get_tasks_by_script(self, script_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取指定脚本的任务记录
        
        Args:
            script_id: 脚本ID
            limit: 返回记录数量限制
            
        Returns:
            List[Dict]: 指定脚本的任务记录
        """
        with self.lock:
            tasks = self._load_history()
            script_tasks = [task for task in tasks if task.get('script_id') == script_id]
            script_tasks.sort(key=lambda x: x.get('end_time', ''), reverse=True)
            return script_tasks[:limit]
    
    def clear_old_records(self, keep_days: int = 30) -> int:
        """
        清理旧记录
        
        Args:
            keep_days: 保留天数
            
        Returns:
            int: 清理的记录数量
        """
        with self.lock:
            tasks = self._load_history()
            cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            original_count = len(tasks)
            tasks = [
                task for task in tasks 
                if datetime.fromisoformat(task.get('end_time', '')).timestamp() > cutoff_date
            ]
            
            self._save_history(tasks)
            return original_count - len(tasks)
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        获取统计摘要
        
        Returns:
            Dict: 包含各脚本的统计信息
        """
        with self.lock:
            tasks = self._load_history()
            
            summary = {
                "total_tasks": len(tasks),
                "scripts": {}
            }
            
            for task in tasks:
                script_id = task.get('script_id', 'unknown')
                if script_id not in summary["scripts"]:
                    summary["scripts"][script_id] = {
                        "count": 0,
                        "total_duration": 0,
                        "success_count": 0
                    }
                
                summary["scripts"][script_id]["count"] += 1
                summary["scripts"][script_id]["total_duration"] += task.get('duration', 0)
                if task.get('status') == 'completed':
                    summary["scripts"][script_id]["success_count"] += 1
            
            return summary

# 全局任务日志管理器实例
_task_logger = None

def get_task_logger() -> TaskLogger:
    """获取全局任务日志管理器实例"""
    global _task_logger
    if _task_logger is None:
        _task_logger = TaskLogger()
    return _task_logger
