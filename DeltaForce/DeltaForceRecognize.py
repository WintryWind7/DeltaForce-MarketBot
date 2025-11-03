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
    def recognize(self, protocol, top_left_ratio: Tuple[float, float], bottom_right_ratio: Tuple[float, float], save: bool = False, allow_list: str = None, return_image: bool = False, preprocess_type: str = None, debug: bool = False) -> bool:
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
        
        # 使用统一的坐标换算函数
        screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        # 调用OCR识别
        result = self.ocr.recognize((screen_left, screen_top), (screen_right, screen_bottom), save=save, allow_list=allow_list, return_image=return_image, preprocess_type=preprocess_type, debug=debug)
        # print((screen_left, screen_top), (screen_right, screen_bottom))
        
        # 将结果存储到协议中
        if return_image:
            protocol.recognized_text = result[0] if result else ""
            protocol.image = result[1] if result and len(result) > 1 else None
        else:
            protocol.recognized_text = result if result else ""
        
        protocol.coordinates = {
            'screen_left': screen_left,
            'screen_top': screen_top, 
            'screen_right': screen_right,
            'screen_bottom': screen_bottom
        }
        
        return bool(result)
    
    @protocol_handler()
    def _capture_screenshot_pyautogui(self, protocol, left: int, top: int, width: int, height: int) -> bool:
        """
        使用 pyautogui 截取屏幕区域（底层函数，用于性能追踪 - 纯截图耗时）
        
        Args:
            left: 左上角X坐标
            top: 左上角Y坐标
            width: 截图宽度
            height: 截图高度
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        import pyautogui
        import numpy as np
        
        # 使用pyautogui截图
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        
        # 转换为numpy数组
        screenshot_array = np.array(screenshot)
        
        # 存储到protocol
        protocol.screenshot = screenshot
        protocol.screenshot_array = screenshot_array
        protocol.is_base_function = True  # 标记为底层函数
        
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
        if not capture_result.success:
            protocol.error_message = "截图失败"
            return False
        
        # 合并结果到当前protocol
        protocol.screenshot = capture_result.screenshot
        protocol.screenshot_array = capture_result.screenshot_array
        protocol.region = {'left': left, 'top': top, 'width': width, 'height': height}
        
        return True
    
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
    底层OCR识别引擎 - 使用easyocr进行图片文字识别
    提供截图、预处理、文字识别等底层功能
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
    
    @protocol_handler()
    def _screenshot(self, protocol, top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> bool:
        """
        根据坐标进行截图
        
        Args:
            top_left: 左上角坐标 (x, y)
            bottom_right: 右下角坐标 (x, y)
            
        Returns:
            numpy.ndarray: 截取的图片数组
        """
        try:
            # 使用PIL的ImageGrab进行截图
            bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
            screenshot = ImageGrab.grab(bbox=bbox)
            
            # 转换为numpy数组
            screenshot_array = np.array(screenshot)
            
            # 如果是RGBA格式，转换为RGB
            if len(screenshot_array.shape) == 3 and screenshot_array.shape[2] == 4:
                screenshot_array = cv2.cvtColor(screenshot_array, cv2.COLOR_RGBA2RGB)
            
            return screenshot_array
            
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    @protocol_handler()
    def _preprocess_image(self, protocol, image: np.ndarray, preprocess_type: str = None) -> bool:
        """
        图像预处理函数
        
        Args:
            image: 输入图像（numpy数组）
            preprocess_type: 预处理类型编号
            
        Returns:
            np.ndarray: 预处理后的图像
        """
        if preprocess_type == "peizhuang":
            return self._preprocess_peizhuang(image)
        else:
            # 无预处理或未知类型，返回原图
            return image
    
    @protocol_handler()
    def _preprocess_peizhuang(self, protocol, image: np.ndarray) -> bool:
        """
        配装预处理：只进行裁剪，直接返回原图像
        
        Args:
            image: 输入图像（numpy数组，RGB格式）
            
        Returns:
            np.ndarray: 预处理后的图像
        """
        try:
            # 裁剪上方3像素，下方4像素
            height = image.shape[0]
            if height > 7:  # 确保图像足够高
                image = image[3:height-4, :]  # 裁剪上方3像素，下方4像素
            
            # 直接返回裁剪后的图像
            return image
            
        except Exception as e:
            print(f"配装预处理失败: {e}")
            return image
    
    @protocol_handler()
    def _postprocess_peizhuang_text(self, protocol, text: str, allow_list: str = None) -> bool:
        """
        配装类型的文本后处理，只保留数字字符
        
        Args:
            text: 原始识别文本
            allow_list: 允许的字符列表（已废弃，强制只返回数字）
            
        Returns:
            str: 只包含数字的文本
        """
        if not text:
            return ""
        
        # 强制只保留数字字符0-9
        filtered = ''.join(char for char in text if char.isdigit())
        return filtered
    
    @protocol_handler()
    def _recognize_text(self, protocol, image: Union[np.ndarray, Image.Image, str], allow_list: str = None, preprocess_type: str = None) -> bool:
        """
        识别图片中的文字
        
        Args:
            image: 图片，可以是numpy数组、PIL Image对象或图片路径
            allow_list: 允许识别的字符列表
            preprocess_type: 预处理类型编号
            
        Returns:
            List[str]: 识别出的文字列表
        """
        try:
            # 如果输入是PIL Image，转换为numpy数组
            if isinstance(image, Image.Image):
                image = np.array(image)
            
            # 如果输入是字符串路径，读取图片
            elif isinstance(image, str):
                image = cv2.imread(image)
                if image is None:
                    raise ValueError("无法读取图片文件")
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 确保图片是numpy数组
            if not isinstance(image, np.ndarray):
                raise ValueError("不支持的图片格式")
            
            # 图像预处理
            processed_image = self._preprocess_image(image, preprocess_type)
            
            # 根据预处理类型选择EasyOCR参数
            if preprocess_type == "peizhuang":
                # 配装类型：使用数字allowlist，优化参数
                results = self.reader.readtext(processed_image, allowlist='1234567890', width_ths=0.7, height_ths=0.7, decoder='beamsearch', text_threshold=0.5)
                
                # 后处理：处理带斜杠的0和其他特殊情况
                text_list = []
                for _, text, confidence in results:
                    processed_text = self._postprocess_peizhuang_text(text, allow_list)
                    if processed_text:  # 只添加非空结果
                        text_list.append(processed_text)
                
                return text_list
            else:
                # 默认参数
                if allow_list is None:
                            results = self.reader.readtext(processed_image)
                else:
                            results = self.reader.readtext(processed_image, allowlist=allow_list)
                
                # 只返回文字内容
                return [text for _, text, _ in results]
            
        except Exception as e:
            print(f"文字识别失败: {e}")
            return []
    
    @protocol_handler()
    def recognize(self, protocol, top_left: Tuple[int, int], bottom_right: Tuple[int, int], save: bool = False, allow_list: str = None, return_image: bool = False, preprocess_type: str = None, debug: bool = False) -> bool:
        """
        从指定坐标截图并识别文字
        
        Args:
            top_left: 左上角坐标 (x, y)
            bottom_right: 右下角坐标 (x, y)
            save: 是否保存截图到本地，默认为False (已废弃，保持兼容性)
            allow_list: 允许识别的字符列表
            return_image: 是否返回截图图像，默认为False
            preprocess_type: 预处理类型编号，默认为None（不预处理）
            
        Returns:
            str 或 tuple: 如果return_image=False返回识别文本，如果return_image=True返回(识别文本, PIL图像)
        """
        # 先截图
        screenshot = self._screenshot(top_left, bottom_right)
        
        if screenshot is None:
            protocol.error_message = "截图失败"
            return False
        
        # 图像预处理
        processed_image = self._preprocess_image(screenshot, preprocess_type)
        
        # 将预处理后的numpy数组转换为PIL Image
        processed_pil = Image.fromarray(processed_image)
        
        # 如果启用旧版保存功能（保存预处理后的图片）
        if save:
            try:
                processed_pil.save("recognize.jpg", "JPEG", quality=95)
            except Exception as e:
                print(f"保存截图失败: {e}")
        
        # 识别文字（使用预处理后的图像）
        text_list = self._recognize_text(processed_image, allow_list=allow_list, preprocess_type=preprocess_type)
        recognized_text = " ".join(text_list) if text_list else ""
        
        # 根据参数决定返回内容（返回预处理后的图片）
        protocol.recognized_text = recognized_text
        if return_image:
            protocol.processed_image = processed_pil
        return True


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