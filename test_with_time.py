import time
import statistics
import sys
import os
import numpy as np
from PIL import Image, ImageGrab
import pyautogui
from typing import List, Union, Tuple

# 添加DeltaForce模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'DeltaForce'))

try:
    import easyocr
    from DeltaForce.DeltaForceClass import DeltaForceClass
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 无法导入必要模块: {e}")
    OCR_AVAILABLE = False

class GetBalanceOCRTester:
    """
    专门测试get_balance方法中OCR识别部分的性能
    不执行点击行为，只测试指定位置的OCR识别耗时
    """
    
    def __init__(self):
        """初始化测试器"""
        if OCR_AVAILABLE:
            # 创建DeltaForce实例以获取窗口信息和OCR配置
            self.delta = DeltaForceClass()
            
            # 查找游戏窗口
            if not self.delta.find_deltaforce_process():
                print("⚠️ 未找到DeltaForce游戏进程，将使用模拟坐标")
                self.game_found = False
            else:
                self.game_found = True
                print(f"✅ 找到游戏窗口: {self.delta.window_width}x{self.delta.window_height}")
        else:
            self.delta = None
            self.game_found = False
    
    def switch_ocr_mode(self, use_gpu=True):
        """切换OCR模式"""
        if not self.delta or not hasattr(self.delta, 'ocr'):
            return False
        
        mode_name = "GPU" if use_gpu else "CPU"
        print(f"🔧 切换OCR到{mode_name}模式...")
        
        try:
            import os
            model_dir = os.path.expanduser("~/.EasyOCR/model")
            self.delta.ocr.reader = easyocr.Reader(['en'], gpu=use_gpu, 
                                                 model_storage_directory=model_dir, 
                                                 download_enabled=True)
            print(f"✅ OCR已切换到{mode_name}模式")
            return True
        except Exception as e:
            print(f"❌ 切换到{mode_name}模式失败: {e}")
            return False
    
    def get_balance_ocr_regions(self):
        """获取get_balance方法中使用的OCR识别区域坐标"""
        regions = {}
        
        if self.game_found and self.delta:
            # 默认位置配置 (从get_balance方法中提取)
            default_m4_ratio = (0.7555, 0.2777)  # 余额显示区域左上角
            default_m5_ratio = (0.8566, 0.2914)  # 余额显示区域右下角
            
            # 交易行位置配置
            market_m4_ratio = (0.7855, 0.2750)  # 余额显示区域左上角（加上偏移）
            market_m5_ratio = (0.9066, 0.2914)  # 余额显示区域右下角（加上偏移）
            
            # 转换为屏幕坐标
            default_m4_screen = self.delta.ratio_to_screen_coords(default_m4_ratio[0], default_m4_ratio[1])
            default_m5_screen = self.delta.ratio_to_screen_coords(default_m5_ratio[0], default_m5_ratio[1])
            
            market_m4_screen = self.delta.ratio_to_screen_coords(market_m4_ratio[0], market_m4_ratio[1])
            market_m5_screen = self.delta.ratio_to_screen_coords(market_m5_ratio[0], market_m5_ratio[1])
            
            # 计算截图区域
            regions["default"] = {
                "name": "默认位置余额区域",
                "ratio_coords": (default_m4_ratio, default_m5_ratio),
                "screen_coords": self._calculate_region_bounds(default_m4_screen, default_m5_screen)
            }
            
            regions["market"] = {
                "name": "交易行位置余额区域", 
                "ratio_coords": (market_m4_ratio, market_m5_ratio),
                "screen_coords": self._calculate_region_bounds(market_m4_screen, market_m5_screen)
            }
        else:
            # 模拟坐标（用于测试）
            regions["default"] = {
                "name": "默认位置余额区域 (模拟)",
                "ratio_coords": ((0.7555, 0.2777), (0.8566, 0.2914)),
                "screen_coords": (100, 100, 200, 150)  # 模拟区域
            }
            
            regions["market"] = {
                "name": "交易行位置余额区域 (模拟)",
                "ratio_coords": ((0.7855, 0.2750), (0.9066, 0.2914)),
                "screen_coords": (150, 100, 250, 150)  # 模拟区域
            }
        
        return regions
    
    def _calculate_region_bounds(self, m4_screen, m5_screen):
        """计算截图区域边界坐标 (从get_balance方法中提取的逻辑)"""
        left = min(m4_screen[0], m5_screen[0])
        top = min(m4_screen[1], m5_screen[1])
        right = max(m4_screen[0], m5_screen[0])
        bottom = max(m4_screen[1], m5_screen[1])
        return (left, top, right, bottom)
    
    def capture_balance_region(self, region_coords):
        """截取余额区域的屏幕截图"""
        try:
            left, top, right, bottom = region_coords
            # 使用pyautogui截图 (与get_balance方法相同)
            screenshot = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
            screenshot_array = np.array(screenshot)
            return screenshot_array
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            # 返回模拟图片
            return np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
    
    def test_balance_ocr_performance(self, region_name, region_info, test_count=100, mode_name=""):
        """测试特定区域的OCR识别性能"""
        
        print(f"\n--- {region_info['name']} {mode_name} ---")
        
        if not self.delta or not self.delta.ocr:
            print("❌ OCR不可用，跳过测试")
            return None
        
        times = []  # 存储耗时数据
        
        for i in range(test_count + 1):  # +1 因为第一次不计入统计
            try:
                # 截取余额区域
                screenshot_array = self.capture_balance_region(region_info['screen_coords'])
                
                # 测试OCR识别耗时 (使用与get_balance相同的参数)
                start = time.perf_counter()
                
                # 这里是get_balance方法中的OCR识别逻辑
                ocr_results = self.delta.ocr.reader.readtext(
                    screenshot_array,
                    allowlist='1234567890',  # 限制只识别数字字符，提高准确性
                    width_ths=0.7,          # 文本框宽度阈值
                    height_ths=0.7,         # 文本框高度阈值
                    text_threshold=0.5,     # 文本置信度阈值
                    decoder='beamsearch'    # 使用束搜索解码器提高识别准确性
                )
                
                end = time.perf_counter()
                
                elapsed = (end - start) * 1000  # 转换为毫秒
                
                # 处理识别结果 (模拟get_balance的处理逻辑)
                if ocr_results:
                    combined_text = ""
                    for (bbox, text, confidence) in ocr_results:
                        filtered_text = ''.join(char for char in text if char.isdigit())
                        combined_text += filtered_text
                    
                    if combined_text:
                        result_text = combined_text
                    else:
                        result_text = "无数字"
                else:
                    result_text = "无识别"
                
                if i == 0:
                    # 第一次：显示但不计入统计
                    print(f"第1次 (预热): {result_text}, {elapsed:.2f}ms")
                else:
                    # 后续测试：计入统计
                    times.append(elapsed)
                    if i <= 10 or i % 50 == 0:  # 显示前10次和每50次的里程碑
                        print(f"第{i}次: {result_text}, {elapsed:.2f}ms")
                    elif i == test_count:  # 最后一次
                        print(f"第{i}次: {result_text}, {elapsed:.2f}ms")
                    elif i % 10 == 0:  # 每10次显示一个进度点
                        print(".", end="", flush=True)
                
            except Exception as e:
                print(f"第{i+1}次: 错误, {e}")
        
        # 返回统计数据
        if times:
            return self._get_statistics(times)
        else:
            return None
    
    def _get_statistics(self, times):
        """获取统计数据"""
        
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        cv = (std_time / avg_time) * 100 if avg_time > 0 else 0
        
        return {
            'count': len(times),
            'avg': avg_time,
            'min': min_time,
            'max': max_time,
            'median': median_time,
            'std': std_time,
            'cv': cv
        }
    
    def _print_statistics(self, stats, mode_name):
        """打印统计数据"""
        
        print(f"\n📊 {mode_name} 统计结果 (基于 {stats['count']} 次有效测试):")
        print("-" * 40)
        
        print(f"平均值: {stats['avg']:.2f}ms")
        print(f"最小值: {stats['min']:.2f}ms")
        print(f"最大值: {stats['max']:.2f}ms")
        print(f"中位数: {stats['median']:.2f}ms")
        print(f"标准差: {stats['std']:.2f}ms")
        print(f"范围:   {stats['max'] - stats['min']:.2f}ms")
        print(f"变异系数: {stats['cv']:.1f}%")
        
        # 性能评级
        if stats['avg'] < 50:
            rating = "🚀 极快"
        elif stats['avg'] < 100:
            rating = "⚡ 很快"
        elif stats['avg'] < 200:
            rating = "✅ 良好"
        elif stats['avg'] < 500:
            rating = "⚠️ 一般"
        else:
            rating = "🐌 较慢"
        
        print(f"性能评级: {rating}")
    
    def _analyze_performance(self, region_name, times, results):
        """分析OCR性能数据"""
        
        print(f"\n📈 {region_name} OCR性能分析:")
        print("-" * 50)
        
        # 时间统计
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        
        print(f"⏱️  时间统计 (基于 {len(times)} 次测试):")
        print(f"   平均耗时: {avg_time:6.2f}ms")
        print(f"   中位数:   {median_time:6.2f}ms")
        print(f"   标准差:   {std_time:6.2f}ms")
        print(f"   最快:     {min_time:6.2f}ms")
        print(f"   最慢:     {max_time:6.2f}ms")
        print(f"   范围:     {max_time - min_time:6.2f}ms")
        
        # 成功率统计
        success_count = sum(1 for result in results if result)
        success_rate = (success_count / len(results)) * 100
        print(f"✅ 成功率: {success_count}/{len(results)} ({success_rate:.1f}%)")
        
        # 性能评级
        if avg_time < 100:
            rating = "🚀 极快"
        elif avg_time < 300:
            rating = "⚡ 很快"
        elif avg_time < 500:
            rating = "✅ 良好"
        elif avg_time < 1000:
            rating = "⚠️ 一般"
        else:
            rating = "🐌 较慢"
        
        print(f"📊 性能评级: {rating}")
        
        # 稳定性评估
        cv = (std_time / avg_time) * 100 if avg_time > 0 else 0
        if cv < 10:
            stability = "🎯 非常稳定"
        elif cv < 20:
            stability = "✅ 稳定"
        elif cv < 30:
            stability = "⚠️ 一般稳定"
        else:
            stability = "❌ 不稳定"
        
        print(f"📊 稳定性: {stability} (变异系数: {cv:.1f}%)")
        
        # 识别结果样本
        valid_results = [r for r in results if r]
        if valid_results:
            print(f"\n📋 识别结果样本 (前3个):")
            for i, result in enumerate(valid_results[:3]):
                combined_text = ""
                for (bbox, text, confidence) in result:
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                print(f"   样本{i+1}: '{combined_text}' (原始结果数: {len(result)})")

def test_get_balance_ocr_timing():
    """主测试函数：分别测试CPU和GPU模式的OCR识别性能"""
    
    if not OCR_AVAILABLE:
        print("❌ 必要模块不可用，无法进行测试")
        return
    
    print("get_balance OCR识别对比测试 (CPU vs GPU)")
    print("每种模式测试100次，排除第一次预热")
    print("=" * 60)
    
    try:
        # 初始化测试器
        tester = GetBalanceOCRTester()
        
        # 获取OCR识别区域，只测试默认位置
        regions = tester.get_balance_ocr_regions()
        default_region = regions.get("default")
        
        if not default_region:
            print("❌ 无法获取默认区域")
            return
        
        # 存储两种模式的统计结果
        results = {}
        
        # 测试GPU模式
        print("\n🚀 开始GPU模式测试...")
        if tester.switch_ocr_mode(use_gpu=True):
            gpu_stats = tester.test_balance_ocr_performance("default", default_region, test_count=100, mode_name="(GPU模式)")
            if gpu_stats:
                results['GPU'] = gpu_stats
                tester._print_statistics(gpu_stats, "GPU模式")
        
        print("\n" + "="*60)
        
        # 测试CPU模式
        print("\n💻 开始CPU模式测试...")
        if tester.switch_ocr_mode(use_gpu=False):
            cpu_stats = tester.test_balance_ocr_performance("default", default_region, test_count=100, mode_name="(CPU模式)")
            if cpu_stats:
                results['CPU'] = cpu_stats
                tester._print_statistics(cpu_stats, "CPU模式")
        
        # 对比分析
        if len(results) == 2:
            print_comparison_results(results)
        
    except Exception as e:
        print(f"❌ 测试错误: {e}")

def print_comparison_results(results):
    """打印CPU和GPU对比结果"""
    
    print("\n" + "="*60)
    print("📊 CPU vs GPU 性能对比分析")
    print("="*60)
    
    gpu_stats = results['GPU']
    cpu_stats = results['CPU']
    
    print(f"{'指标':<12} {'GPU模式':<15} {'CPU模式':<15} {'GPU优势':<15}")
    print("-" * 60)
    
    # 平均值对比
    gpu_faster_avg = ((cpu_stats['avg'] - gpu_stats['avg']) / cpu_stats['avg']) * 100
    print(f"{'平均耗时':<12} {gpu_stats['avg']:<15.2f} {cpu_stats['avg']:<15.2f} {gpu_faster_avg:>+14.1f}%")
    
    # 最小值对比
    gpu_faster_min = ((cpu_stats['min'] - gpu_stats['min']) / cpu_stats['min']) * 100
    print(f"{'最小耗时':<12} {gpu_stats['min']:<15.2f} {cpu_stats['min']:<15.2f} {gpu_faster_min:>+14.1f}%")
    
    # 最大值对比
    gpu_faster_max = ((cpu_stats['max'] - gpu_stats['max']) / cpu_stats['max']) * 100
    print(f"{'最大耗时':<12} {gpu_stats['max']:<15.2f} {cpu_stats['max']:<15.2f} {gpu_faster_max:>+14.1f}%")
    
    # 中位数对比
    gpu_faster_median = ((cpu_stats['median'] - gpu_stats['median']) / cpu_stats['median']) * 100
    print(f"{'中位数':<12} {gpu_stats['median']:<15.2f} {cpu_stats['median']:<15.2f} {gpu_faster_median:>+14.1f}%")
    
    # 标准差对比
    print(f"{'标准差':<12} {gpu_stats['std']:<15.2f} {cpu_stats['std']:<15.2f} {'--':<15}")
    
    # 变异系数对比
    print(f"{'变异系数':<12} {gpu_stats['cv']:<15.1f} {cpu_stats['cv']:<15.1f} {'--':<15}")
    
    print("\n💡 分析结论:")
    if gpu_faster_avg > 0:
        print(f"✅ GPU模式平均快 {gpu_faster_avg:.1f}%")
    else:
        print(f"❌ CPU模式平均快 {-gpu_faster_avg:.1f}%")
    
    if gpu_stats['cv'] < cpu_stats['cv']:
        print(f"✅ GPU模式更稳定 (变异系数: {gpu_stats['cv']:.1f}% vs {cpu_stats['cv']:.1f}%)")
    else:
        print(f"❌ CPU模式更稳定 (变异系数: {cpu_stats['cv']:.1f}% vs {gpu_stats['cv']:.1f}%)")
    
    # 推荐
    if gpu_faster_avg > 10:  # GPU快10%以上
        print("🚀 推荐使用GPU模式")
    elif gpu_faster_avg < -10:  # CPU快10%以上
        print("💻 推荐使用CPU模式")
    else:
        print("⚖️ 两种模式性能相近，可根据系统资源选择")

def test_ocr_parameter_comparison(tester):
    """测试不同OCR参数配置的性能对比"""
    
    # 获取默认区域进行测试
    regions = tester.get_balance_ocr_regions()
    default_region = regions.get("default")
    
    if not default_region:
        print("❌ 无法获取测试区域")
        return
    
    # 截取一张测试图片
    screenshot_array = tester.capture_balance_region(default_region['screen_coords'])
    
    # 不同的OCR参数配置
    ocr_configs = [
        {
            "name": "get_balance标准配置",
            "params": {
                "allowlist": '1234567890',
                "width_ths": 0.7,
                "height_ths": 0.7,
                "text_threshold": 0.5,
                "decoder": 'beamsearch'
            }
        },
        {
            "name": "默认配置",
            "params": {}
        },
        {
            "name": "高精度配置",
            "params": {
                "allowlist": '1234567890',
                "width_ths": 0.5,
                "height_ths": 0.5,
                "text_threshold": 0.3,
                "decoder": 'beamsearch'
            }
        },
        {
            "name": "快速配置",
            "params": {
                "allowlist": '1234567890',
                "width_ths": 0.8,
                "height_ths": 0.8,
                "text_threshold": 0.7
            }
        }
    ]
    
    for config in ocr_configs:
        print(f"\n--- {config['name']} ---")
        
        times = []
        results = []
        
        for i in range(5):
            try:
                start = time.perf_counter()
                
                if config['params']:
                    result = tester.delta.ocr.reader.readtext(screenshot_array, **config['params'])
                else:
                    result = tester.delta.ocr.reader.readtext(screenshot_array)
                
                end = time.perf_counter()
                
                elapsed = (end - start) * 1000
                times.append(elapsed)
                results.append(result)
                
                result_count = len(result) if result else 0
                print(f"  第{i+1}次: {elapsed:6.2f}ms (结果数: {result_count})")
                
            except Exception as e:
                print(f"  第{i+1}次: 失败 - {e}")
        
        if times:
            avg_time = statistics.mean(times)
            std_time = statistics.stdev(times) if len(times) > 1 else 0
            min_time = min(times)
            max_time = max(times)
            
            print(f"  📊 统计:")
            print(f"     平均: {avg_time:6.2f}ms")
            print(f"     范围: {min_time:6.2f}ms ~ {max_time:6.2f}ms")
            print(f"     标准差: {std_time:6.2f}ms")

def main():
    """主函数"""
    test_get_balance_ocr_timing()

if __name__ == "__main__":
    main()