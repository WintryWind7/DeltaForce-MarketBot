"""
测试window_func模块的窗口操作功能

这个测试文件用于验证编译好的pyd文件是否能正确读取窗口信息，
特别是查找包含DeltaForceClient的窗口。
"""

import sys
import os
import time

def setup_import_paths():
    """设置导入路径，支持两种运行方式"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 判断运行方式
    if os.path.basename(os.getcwd()) == 'tests':
        # 在tests目录内运行
        project_root = os.path.dirname(script_dir)
        core_dir = os.path.join(project_root, 'core')
        core_dist_dir = os.path.join(core_dir, 'dist')
        print(f"检测到在tests目录内运行")
    else:
        # 从项目根目录运行
        project_root = os.path.dirname(script_dir)
        core_dir = os.path.join(project_root, 'core')
        core_dist_dir = os.path.join(core_dir, 'dist')
        print(f"检测到从项目根目录运行")
    
    # 添加多个可能的路径到Python路径
    paths_to_add = [core_dir, core_dist_dir]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
            print(f"添加导入路径: {path}")
    
    return core_dir

# 设置导入路径
core_dir = setup_import_paths()

def test_window_func_import():
    """测试能否成功导入编译好的window_func模块"""
    try:
        import window_func
        print("✓ 成功导入window_func模块")
        return window_func
    except ImportError as e:
        print(f"✗ 导入window_func模块失败: {e}")
        print("请确保已经编译了Cython代码: python .\\core\\setup.py build_ext")
        
        # 尝试列出core/dist目录中的文件
        try:
            core_dist_dir = os.path.join(core_dir, 'dist')
            if os.path.exists(core_dist_dir):
                files = os.listdir(core_dist_dir)
                print(f"Core/dist目录中的文件: {files}")
            else:
                print(f"Core/dist目录不存在: {core_dist_dir}")
        except Exception as list_error:
            print(f"无法列出core/dist目录内容: {list_error}")
        
        return None

def test_get_screen_resolution(window_func):
    """测试获取屏幕分辨率功能"""
    try:
        width, height = window_func.get_screen_resolution()
        print(f"✓ 屏幕分辨率: {width} x {height}")
        return True
    except Exception as e:
        print(f"✗ 获取屏幕分辨率失败: {e}")
        return False

def test_get_foreground_window(window_func):
    """测试获取前台窗口功能"""
    try:
        hwnd = window_func.get_foreground_window()
        if hwnd:
            title = window_func.get_window_title(hwnd)
            print(f"✓ 前台窗口句柄: {hwnd}")
            print(f"  窗口标题: {title}")
            return True
        else:
            print("✗ 获取前台窗口失败")
            return False
    except Exception as e:
        print(f"✗ 获取前台窗口失败: {e}")
        return False

def test_enum_windows(window_func):
    """测试枚举所有窗口功能"""
    try:
        windows = window_func.enum_windows()
        print(f"✓ 找到 {len(windows)} 个可见窗口")
        return windows
    except Exception as e:
        print(f"✗ 枚举窗口失败: {e}")
        return []

def test_find_deltaforce_windows(window_func, windows):
    """查找包含DeltaForceClient的窗口"""
    print("\n🔍 查找DeltaForceClient相关窗口...")
    
    # 关键词列表，用于识别DeltaForce相关窗口
    keywords = [
        'deltaforce', 'delta', 'force', 'client', 'market', 'bot', 'trading',
        'DeltaForce', 'Delta', 'Force', 'Client', 'Market', 'Bot', 'Trading'
    ]
    
    deltaforce_windows = []
    
    for hwnd, title, process_name in windows:
        title_lower = title.lower()
        process_lower = process_name.lower()
        
        # 检查窗口标题和进程名是否包含关键词
        for keyword in keywords:
            if keyword.lower() in title_lower or keyword.lower() in process_lower:
                deltaforce_windows.append((hwnd, title, process_name))
                break
    
    if deltaforce_windows:
        print(f"✓ 找到 {len(deltaforce_windows)} 个可能的DeltaForce相关窗口:")
        print("=" * 80)
        for i, (hwnd, title, process_name) in enumerate(deltaforce_windows, 1):
            print(f"\n{i}. 窗口信息:")
            print(f"   句柄: {hwnd}")
            print(f"   标题: {title}")
            print(f"   进程: {process_name}")
            
            # 获取窗口详细信息
            try:
                info = window_func.get_window_info(hwnd)
                print(f"   位置: ({info['left']}, {info['top']})")
                print(f"   大小: {info['width']} x {info['height']}")
            except Exception as e:
                print(f"   位置信息: 获取失败 ({e})")
            
            print("-" * 60)
    else:
        print("⚠️  未找到明显的DeltaForce相关窗口")
        print("当前可见窗口:")
        for i, (hwnd, title, process_name) in enumerate(windows[:10], 1):  # 只显示前10个
            print(f"  {i}. {title} ({process_name})")
        if len(windows) > 10:
            print(f"  ... 还有 {len(windows) - 10} 个窗口")
    
    return deltaforce_windows

def test_find_window_by_name(window_func):
    """测试按名称查找窗口功能"""
    print("\n🔍 测试按名称查找窗口...")
    
    # 尝试查找一些常见的窗口
    test_names = [
        "DeltaForce",
        "DeltaForceClient", 
        "Market Bot",
        "Trading Client"
    ]
    
    for name in test_names:
        try:
            hwnd = window_func.find_window_by_name(window_name=name)
            if hwnd:
                title = window_func.get_window_title(hwnd)
                print(f"✓ 找到窗口 '{name}': {hwnd} - {title}")
            else:
                print(f"⚠️  未找到窗口 '{name}'")
        except Exception as e:
            print(f"✗ 查找窗口 '{name}' 时出错: {e}")

def test_window_operations(window_func, test_hwnd):
    """测试窗口操作功能"""
    if not test_hwnd:
        print("⚠️  跳过窗口操作测试（没有测试窗口）")
        return
    
    print(f"\n🔧 测试窗口操作功能 (使用窗口: {test_hwnd})...")
    
    try:
        # 测试获取窗口信息
        info = window_func.get_window_info(test_hwnd)
        print(f"✓ 窗口信息: {info}")
        
        # 测试获取窗口标题
        title = window_func.get_window_title(test_hwnd)
        print(f"✓ 窗口标题: {title}")
        
        # 测试获取进程名
        process = window_func.get_process_name(test_hwnd)
        print(f"✓ 进程名: {process}")
        
    except Exception as e:
        print(f"✗ 窗口操作测试失败: {e}")

def main():
    """主测试函数"""
    print("DeltaForce Window Functions 测试")
    print("=" * 50)
    
    # 测试导入模块
    window_func = test_window_func_import()
    if not window_func:
        return
    
    print("\n" + "=" * 50)
    print("开始功能测试...")
    print("=" * 50)
    
    # 测试基本功能
    test_get_screen_resolution(window_func)
    test_get_foreground_window(window_func)
    
    # 测试枚举窗口
    windows = test_enum_windows(window_func)
    if not windows:
        print("⚠️  无法枚举窗口，跳过后续测试")
        return
    
    # 查找DeltaForce相关窗口
    deltaforce_windows = test_find_deltaforce_windows(window_func, windows)
    
    # 测试按名称查找
    test_find_window_by_name(window_func)
    
    # 测试窗口操作（使用第一个找到的DeltaForce窗口，或者第一个普通窗口）
    test_hwnd = None
    if deltaforce_windows:
        test_hwnd = deltaforce_windows[0][0]
        print(f"\n🎯 使用DeltaForce窗口进行测试: {test_hwnd}")
    elif windows:
        test_hwnd = windows[0][0]
        print(f"\n🎯 使用普通窗口进行测试: {test_hwnd}")
    
    test_window_operations(window_func, test_hwnd)
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
