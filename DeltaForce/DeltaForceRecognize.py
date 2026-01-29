# 尝试相对导入，如果失败则使用绝对导入
try:
    from .DeltaForceWindow import DeltaForceWindow
except ImportError:
    from DeltaForceWindow import DeltaForceWindow
from typing import Tuple, List, Union
import easyocr
import numpy as np
from PIL import ImageGrab, Image
import cv2
import os
import sys

# Win32 API 导入（用于高性能截图）
import win32gui
import win32ui
import win32con
from PIL import Image

# 导入协议装饰器
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from base.decorators import protocol_handler


class DeltaForceRecognize(DeltaForceWindow):
    """
    底层识别类 - 提供OCR文字识别功能
    继承自DeltaForceWindow，专门负责游戏内文字识别
    """

    def __init__(self):
        super().__init__()
        self.ocr = OCR()
    
    @protocol_handler()
    def OCR_digits_recognize(self, protocol, top_left_ratio: Tuple[float, float], bottom_right_ratio: Tuple[float, float], save: bool = False, allow_list: str = None, return_image: bool = False, preprocess_type: str = None, debug: bool = False) -> bool:
        """根据游戏窗口内的相对比例坐标进行截图识别
        
        参数:
            top_left_ratio: 左上角坐标比例 (x_ratio, y_ratio)，范围0.0-1.0
            bottom_right_ratio: 右下角坐标比例 (x_ratio, y_ratio)，范围0.0-1.0
            save: 是否保存截图到本地，默认为False
            allow_list: 允许识别的字符列表，默认为None（识别所有字符）
            return_image: 是否返回截图图像，默认为False
            preprocess_type: 预处理类型编号，默认为None（不预处理）
            
        返回:
            str 或 tuple: 识别出的文字文本，或(文字文本, PIL图像)
            
        示例:
            # 基础识别
            result = recognizer.recognize((0.6625, 0.2767), (0.7418, 0.3168))
            
            # 使用配装预处理
            result = recognizer.recognize((0.4, 0.4), (0.6, 0.6), preprocess_type="peizhuang")
            
            # 只识别数字并返回图像
            text, image = recognizer.recognize((0.4, 0.4), (0.6, 0.6), allow_list="0123456789", return_image=True)
        """
        # 检查窗口是否已找到
        if self.target_window_handle is None:
            print("错误: 未找到游戏窗口，请先调用find_deltaforce_process()")
            protocol.error_message = "未找到游戏窗口"
            return False
        
        # 更新窗口信息确保数据最新
        self._update_window_info()
        
        # 步骤1: 使用坐标转换函数转换比例坐标为屏幕坐标
        screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        # 计算截图区域
        width = screen_right - screen_left
        height = screen_bottom - screen_top
        
        # 步骤2: 调用 screenshot_region 截图
        screenshot_result = self.screenshot_region(screen_left, screen_top, width, height)
        
        image_array = screenshot_result.screenshot_array
        
        # 步骤3: 预处理（可选）
        if preprocess_type:
            image_array = self.ocr.preprocess(image_array, preprocess_type)
        
        # 步骤4: 调用 OCR 识别
        ocr_results = self.ocr.recognize(
            image_array,
            allowlist=allow_list or '1234567890,',
            decoder='greedy'
        )
        
        # 提取识别文本并移除逗号
        recognized_text = ''.join([text for _, text, _ in ocr_results])
        recognized_text = recognized_text.replace(',', '')
        
        # 存储结果到协议
        protocol.recognized_text = recognized_text
        protocol.ocr_results = ocr_results
        protocol.coordinates = {
            'screen_left': screen_left,
            'screen_top': screen_top, 
            'screen_right': screen_right,
            'screen_bottom': screen_bottom
        }
        
        if return_image:
            protocol.screenshot_image = screenshot_result.screenshot
        
        return True
    
    @protocol_handler()
    def _capture_screenshot_win32api(self, protocol, left: int, top: int, width: int, height: int) -> bool:
        """
        使用 Win32 API 截取屏幕区域（底层函数，用于性能追踪 - 纯截图耗时）
        
        Args:
            left: 左上角X坐标
            top: 左上角Y坐标
            width: 截图宽度
            height: 截图高度
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        import numpy as np
        
        # 使用 Win32 API 截图
        hdesktop = win32gui.GetDesktopWindow()
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        
        screenshot_bmp = win32ui.CreateBitmap()
        screenshot_bmp.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot_bmp)
        
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
        
        bmpinfo = screenshot_bmp.GetInfo()
        bmpstr = screenshot_bmp.GetBitmapBits(True)
        
        screenshot = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        mem_dc.DeleteDC()
        win32gui.DeleteObject(screenshot_bmp.GetHandle())
        win32gui.ReleaseDC(hdesktop, desktop_dc)
        
        # 转换为numpy数组
        screenshot_array = np.array(screenshot)
        
        # 存储到protocol
        protocol.screenshot = screenshot
        protocol.screenshot_array = screenshot_array
        protocol.is_base_function = True  # 标记为底层函数
        
        return True
    
    @protocol_handler()
    def screenshot_region(self, protocol, left: int, top: int, width: int, height: int) -> bool:
        """
        截取指定区域的屏幕截图（调用底层截图函数）
        
        Args:
            left: 左上角X坐标
            top: 左上角Y坐标
            width: 截图宽度
            height: 截图高度
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        # 调用底层截图函数（使用 Win32 API）
        capture_result = self._capture_screenshot_win32api(left, top, width, height)
        
        # 合并结果到当前protocol（自动合并，包括 success 状态）
        protocol.screenshot = capture_result.screenshot
        protocol.screenshot_array = capture_result.screenshot_array
        protocol.region = {'left': left, 'top': top, 'width': width, 'height': height}
        
        # 直接返回子函数的成功状态（如果子函数失败，这里也失败）
        return capture_result.success
    
    @protocol_handler()
    def ocr_readtext(self, protocol, image_array, allowlist: str = '1234567890', 
                    width_ths: float = 0.7, height_ths: float = 0.7, 
                    text_threshold: float = 0.5, decoder: str = 'greedy') -> bool:
        """
        使用EasyOCR识别图像中的文字（底层函数，用于追踪）
        
        Args:
            image_array: 图像的numpy数组
            allowlist: 允许识别的字符列表，默认 '1234567890' 只识别数字
            width_ths: 文本框宽度阈值，默认 0.7
            height_ths: 文本框高度阈值，默认 0.7
            text_threshold: 文本置信度阈值，默认 0.5
            decoder: 解码器类型，默认 'greedy'（贪婪解码器，速度快）
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        # 调用OCR引擎的readtext方法
        if allowlist:
            results = self.ocr.reader.readtext(
                image_array,
                allowlist=allowlist,
                width_ths=width_ths,
                height_ths=height_ths,
                text_threshold=text_threshold,
                decoder=decoder
            )
        else:
            results = self.ocr.reader.readtext(
                image_array,
                width_ths=width_ths,
                height_ths=height_ths,
                text_threshold=text_threshold,
                decoder=decoder
            )
        
        # 存储识别结果到protocol
        protocol.ocr_results = results
        protocol.ocr_params = {
            'allowlist': allowlist,
            'width_ths': width_ths,
            'height_ths': height_ths,
            'text_threshold': text_threshold,
            'decoder': decoder
        }
        
        return True


class OCR:
    """
    纯粹的OCR识别引擎 - 输入图片，输出识别结果
    只负责预处理和文字识别，不包含截图功能
    """
    
    def __init__(self, languages: List[str] = ['en']):
        """
        初始化OCR识别器
        
        Args:
            languages: 支持的语言列表，默认只使用英文（数字识别更准确）
        """
        # 使用自定义识别模型 best_norm_ED.pth
        # 使用默认模型目录，其中包含检测模型和自定义识别模型
        import os
        model_dir = os.path.expanduser("~/.EasyOCR/model")
        self.reader = easyocr.Reader(languages, gpu=True, 
                                   model_storage_directory=model_dir, 
                                   download_enabled=False)
        
        # 检查GPU状态
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"✅ OCR使用GPU加速: {gpu_name}")
            else:
                print("⚠️ OCR GPU不可用，使用CPU模式")
        except ImportError:
            print("⚠️ 无法检测GPU状态（PyTorch未安装）")
    
    def preprocess(self, image: np.ndarray, preprocess_type: str = None) -> np.ndarray:
        """
        图像预处理（可选）
        
        Args:
            image: 输入图像（numpy数组）
            preprocess_type: 预处理类型，目前支持 "peizhuang" 或 None
            
        Returns:
            预处理后的图像
        """
        if preprocess_type == "peizhuang":
            # 裁剪上方3像素，下方4像素
            height = image.shape[0]
            if height > 7:
                image = image[3:height-4, :]
        
        return image
    
    def recognize(self, image: np.ndarray, allowlist: str = None, 
                 width_ths: float = 0.7, height_ths: float = 0.7,
                 text_threshold: float = 0.5, decoder: str = 'greedy') -> List:
        """
        识别图片中的文字（核心功能）
        
        Args:
            image: 输入图像（numpy数组，RGB格式）
            allowlist: 允许识别的字符列表
            width_ths: 文本框宽度阈值
            height_ths: 文本框高度阈值
            text_threshold: 文本置信度阈值
            decoder: 解码器类型
            
        Returns:
            EasyOCR 识别结果列表 [(bbox, text, confidence), ...]
        """
        if allowlist:
            results = self.reader.readtext(
                image,
                allowlist=allowlist,
                width_ths=width_ths,
                height_ths=height_ths,
                text_threshold=text_threshold,
                decoder=decoder
            )
        else:
            results = self.reader.readtext(
                image,
                width_ths=width_ths,
                height_ths=height_ths,
                text_threshold=text_threshold,
                decoder=decoder
            )
            
        return results


def test_recognize():
    """测试DeltaForceRecognize类"""
    print("=" * 60)
    print("DeltaForceRecognize 测试")
    print("=" * 60)
    
    # 创建识别器实例
    recognizer = DeltaForceRecognize()
    
    # 查找游戏进程
    print("查找DeltaForce进程...")
    if recognizer.find_deltaforce_process():
        print("✓ 找到DeltaForce进程!")
        
        # 获取窗口信息
        print(f"\n窗口信息:")
        print(f"  窗口位置: ({recognizer.window_x}, {recognizer.window_y})")
        print(f"  窗口尺寸: {recognizer.window_width} x {recognizer.window_height}")
        print(f"  DPI缩放: {recognizer.dpi_scale_x:.2f}x, {recognizer.dpi_scale_y:.2f}x")
        
        # 测试比例识别功能
        print(f"\n测试比例识别功能...")
        
        # 示例：截取窗口中心区域 (0.4, 0.4) 到 (0.6, 0.6)
        print("截取窗口中心区域 (40% - 60%)...")
        result = recognizer.recognize((0.4, 0.4), (0.6, 0.6))
        print(f"识别结果: {result}")
        
        # 示例：截取窗口右上角区域 (0.8, 0.1) 到 (0.95, 0.2)
        print("\n截取窗口右上角区域...")
        result = recognizer.recognize((0.8, 0.1), (0.95, 0.2))
        print(f"识别结果: {result}")
        
        # 测试错误输入
        print(f"\n测试错误输入...")
        result = recognizer.recognize((1.5, 0.5), (0.8, 0.6))  # 超出范围的比例
        print(f"错误输入结果: {result}")
        
    else:
        print("✗ 未找到DeltaForce进程")
    
    print("=" * 60)
    print("测试完成!")


if __name__ == "__main__":
    test_recognize()