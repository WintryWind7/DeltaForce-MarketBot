
# -*- coding: utf-8 -*-
"""测试 search_and_sell_first_9_items 函数是否存在"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

from DeltaForce.DeltaForceClass import DeltaForceClass

# 检查函数是否存在
print("=" * 80)
print("检查 DeltaForceClass 中的方法")
print("=" * 80)

delta = DeltaForceClass()

# 列出所有方法
all_methods = [method for method in dir(delta) if not method.startswith('_')]
print(f"\n总共有 {len(all_methods)} 个公开方法\n")

# 检查特定方法
target_methods = [
    'search_and_sell_first_9_items',
    'generate_grid_coords',
    'check_waiting_status',
    'check_purchase_error'
]

print("检查目标方法:")
for method_name in target_methods:
    exists = hasattr(delta, method_name)
    status = "✅ 存在" if exists else "❌ 不存在"
    print(f"  {method_name}: {status}")
    if exists:
        method = getattr(delta, method_name)
        print(f"    类型: {type(method)}")

print("\n" + "=" * 80)

