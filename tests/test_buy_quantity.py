import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from DeltaForce import DeltaForceClass

def test_quantity_selection():
    """
    测试数量选择的点击位置计算和实际点击
    
    测试用例：
    - 最大值：200
    - 测试数量：1, 31, 62, 200
    """
    print("🧪 开始测试 buy_in_market 数量选择功能")
    print("=" * 50)
    
    # 创建 DeltaForce 实例
    delta = DeltaForceClass()
    
    # 测试参数
    max_quantity = 200
    test_quantities = [1, 31, 62, 200]
    
    print(f"📊 测试参数:")
    print(f"   最大数量: {max_quantity}")
    print(f"   测试数量: {test_quantities}")
    print()
    
    # 检查是否有DeltaForce窗口
    window_handle = delta.find_deltaforce_process()
    if not window_handle:
        print("⚠️  未找到DeltaForce进程，将在无窗口模式下测试计算逻辑")
        test_calculation_only(max_quantity, test_quantities)
        return
    
    # 如果找到进程，绑定到窗口
    if delta.bind_to_window(window_handle):
        print(f"✅ 已绑定到窗口: {window_handle}")
        test_with_window(delta, max_quantity, test_quantities)
    else:
        print("❌ 窗口绑定失败，将在无窗口模式下测试计算逻辑")
        test_calculation_only(max_quantity, test_quantities)

def test_calculation_only(max_quantity, test_quantities):
    """
    仅测试计算逻辑，不实际点击
    """
    print("🧮 测试数量选择的计算逻辑:")
    print("-" * 30)
    
    # 从 DeltaForceClass.buy_in_market 方法中获取拖动条参数
    # 这些参数在 buy_in_market 方法中定义：
    # left_ratio = 0.7890, right_ratio = 0.9036, y_ratio = 0.7233
    left_ratio = 0.7890   # 与 buy_in_market 方法保持一致
    right_ratio = 0.9036  # 与 buy_in_market 方法保持一致
    y_ratio = 0.7233      # 与 buy_in_market 方法保持一致
    
    print(f"📊 拖动条参数（来自 DeltaForceClass.buy_in_market）:")
    print(f"   左端: {left_ratio}, 右端: {right_ratio}, Y坐标: {y_ratio}")
    print()
    
    for quantity in test_quantities:
        # 修正的计算逻辑：将数量1-max_quantity映射到0%-100%
        if max_quantity == 1:
            quantity_ratio = 0.0
        else:
            quantity_ratio = (quantity - 1) / (max_quantity - 1)
        
        # 计算实际点击的X坐标比例
        click_x_ratio = left_ratio + (right_ratio - left_ratio) * quantity_ratio
        
        print(f"📍 数量 {quantity:3d}/{max_quantity}:")
        print(f"   修正比例: {quantity_ratio:6.2%}")
        print(f"   点击位置: ({click_x_ratio:.4f}, {y_ratio})")
        print(f"   相对偏移: {(click_x_ratio - left_ratio) / (right_ratio - left_ratio):6.2%}")
        print()

def test_with_window(delta, max_quantity, test_quantities):
    """
    在有窗口的情况下测试实际点击
    """
    print("🎯 测试实际点击操作:")
    print("-" * 30)
    
    for i, quantity in enumerate(test_quantities):
        print(f"测试 {i+1}/{len(test_quantities)}: 数量 {quantity}/{max_quantity}")
        
        try:
            # 调用 buy_in_market 方法，设置 buy=False 仅测试数量选择
            success = delta.buy_in_market(
                buyin=quantity,
                maxin=max_quantity,
                times=1,
                delay=0.07,
                buy=False,  # 仅测试数量选择，不执行购买
                loop=False
            )
            
            if success:
                print(f"✅ 数量 {quantity} 选择测试成功")
            else:
                print(f"❌ 数量 {quantity} 选择测试失败")
                
        except Exception as e:
            print(f"❌ 数量 {quantity} 测试异常: {e}")
        
        # 测试间隔
        if i < len(test_quantities) - 1:
            print("⏳ 等待 2 秒后进行下一个测试...")
            time.sleep(2)
            print()

def test_edge_cases():
    """
    测试边界情况
    """
    print("\n🔍 测试边界情况:")
    print("-" * 30)
    
    delta = DeltaForceClass()
    
    # 测试无效参数
    test_cases = [
        {"buyin": 0, "maxin": 200, "desc": "购买数量为0"},
        {"buyin": -1, "maxin": 200, "desc": "购买数量为负数"},
        {"buyin": 100, "maxin": 0, "desc": "最大数量为0"},
        {"buyin": 100, "maxin": -1, "desc": "最大数量为负数"},
        {"buyin": 300, "maxin": 200, "desc": "购买数量超过最大数量"},
    ]
    
    for case in test_cases:
        print(f"测试: {case['desc']}")
        try:
            # 这些调用应该在参数验证阶段就失败
            success = delta.buy_in_market(
                buyin=case["buyin"],
                maxin=case["maxin"],
                buy=False,
                loop=False
            )
            print(f"   结果: {'通过' if not success else '意外成功'}")
        except Exception as e:
            print(f"   异常: {e}")
        print()

if __name__ == "__main__":
    print("🚀 DeltaForce 数量选择测试工具")
    print("=" * 50)
    
    try:
        # 主要测试
        test_quantity_selection()
        
        # 边界情况测试
        test_edge_cases()
        
        print("✨ 测试完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
