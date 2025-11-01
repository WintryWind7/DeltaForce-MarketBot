# -*- coding: utf-8 -*-
"""
DeltaForce 自动化操作包
"""

from .DeltaForceWindow import DeltaForceWindow
from .DeltaForceRecognize import DeltaForceRecognize
from .DeltaForceClass import DeltaForceClass

# 导入 DeltaManager（原 DeltaForceManager 已重命名）
try:
    from .DeltaManager import DeltaManager, get_delta_manager
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from DeltaManager import DeltaManager, get_delta_manager

__all__ = [
    'DeltaForceWindow',
    'DeltaForceRecognize', 
    'DeltaForceClass',
    'DeltaManager',
    'get_delta_manager'
]
