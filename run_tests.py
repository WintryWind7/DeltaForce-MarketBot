"""
DeltaForce Market Bot 测试运行器

自动发现和运行tests目录下的所有测试文件。
使用方法: python run_tests.py
"""

import os
import sys
import glob
import importlib.util
import time
from pathlib import Path

def discover_tests():
    """发现tests目录下的所有测试文件"""
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print("❌ tests目录不存在")
        return []
    
    # 查找所有以test_开头的Python文件
    test_files = list(tests_dir.glob("test_*.py"))
    
    if not test_files:
        print("⚠️  在tests目录中未找到测试文件")
        return []
    
    print(f"🔍 发现 {len(test_files)} 个测试文件:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    return test_files

def run_test_file(test_file_path):
    """运行单个测试文件"""
    print(f"\n{'='*60}")
    print(f"🧪 运行测试: {test_file_path.name}")
    print(f"{'='*60}")
    
    try:
        # 动态导入测试模块
        spec = importlib.util.spec_from_file_location(
            test_file_path.stem, 
            test_file_path
        )
        test_module = importlib.util.module_from_spec(spec)
        
        # 设置模块的__file__属性
        test_module.__file__ = str(test_file_path)
        
        # 执行模块
        spec.loader.exec_module(test_module)
        
        print(f"✅ 测试文件 {test_file_path.name} 执行完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试文件 {test_file_path.name} 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 DeltaForce Market Bot 测试运行器")
    print("=" * 60)
    
    # 检查是否已编译
    core_dist_dir = Path("core/dist")
    if not core_dist_dir.exists():
        print("❌ core/dist目录不存在，请先编译Cython代码:")
        print("   python .\\core\\setup.py build_ext")
        return False
    
    pyd_files = list(core_dist_dir.glob("*.pyd"))
    if not pyd_files:
        print("❌ core/dist目录中没有找到.pyd文件，请先编译Cython代码:")
        print("   python .\\core\\setup.py build_ext")
        return False
    
    print(f"✅ 找到编译好的模块: {[f.name for f in pyd_files]}")
    
    # 发现测试文件
    test_files = discover_tests()
    if not test_files:
        return False
    
    # 运行所有测试
    print(f"\n🚀 开始运行 {len(test_files)} 个测试文件...")
    start_time = time.time()
    
    success_count = 0
    total_count = len(test_files)
    
    for test_file in test_files:
        if run_test_file(test_file):
            success_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    # 输出测试结果摘要
    print(f"\n{'='*60}")
    print("📊 测试结果摘要")
    print(f"{'='*60}")
    print(f"总测试文件数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"总耗时: {duration:.2f} 秒")
    
    if success_count == total_count:
        print("🎉 所有测试通过!")
        return True
    else:
        print("⚠️  部分测试失败")
        return False

def main():
    """主函数"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行器出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
