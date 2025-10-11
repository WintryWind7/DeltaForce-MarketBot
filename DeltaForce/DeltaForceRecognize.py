from DeltaForceWindow import DeltaForceWindow
from typing import Tuple, List, Union
import easyocr
import numpy as np
from PIL import ImageGrab, Image
import cv2


class DeltaForceRecognize(DeltaForceWindow):
    """
    底层识别类 - 提供OCR文字识别功能
    继承自DeltaForceWindow，专门负责游戏内文字识别
    """

    def __init__(self):
        super().__init__()
        self.ocr = OCR()
    
    def recognize(self, top_left_ratio: Tuple[float, float], bottom_right_ratio: Tuple[float, float], save: bool = False, allow_list: str = None, return_image: bool = False, preprocess_type: str = None, debug: bool = False):
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
            return ""
        
        # 更新窗口信息确保数据最新
        self._update_window_info()
        
        # 使用统一的坐标换算函数
        screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        # 调用OCR识别
        try:
            result = self.ocr.recognize((screen_left, screen_top), (screen_right, screen_bottom), save=save, allow_list=allow_list, return_image=return_image, preprocess_type=preprocess_type, debug=debug)
            # print((screen_left, screen_top), (screen_right, screen_bottom))
            return result
        except Exception as e:
            print(f"OCR识别失败: {e}")
            if debug:
                return ("", None, []) if return_image else ("", [])
            return ("", None) if return_image else ""


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
        self.reader = easyocr.Reader(languages, gpu=False, 
                                   model_storage_directory=model_dir, 
                                   download_enabled=False)
    
    def _screenshot(self, top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> np.ndarray:
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
    
    def _preprocess_image(self, image: np.ndarray, preprocess_type: str = None) -> np.ndarray:
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
    
    def _preprocess_peizhuang(self, image: np.ndarray) -> np.ndarray:
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
            
            # 直接返回裁剪后的图像，不进行其他预处理
            return image
            
            # 以下为注释掉的原始预处理逻辑
            """
            # 定义RGB绿色范围
            lower_green = np.array([15, 50, 60])  # R, G, B
            upper_green = np.array([33, 255, 130])  # R, G, B
            
            # 创建绿色区域的掩码
            green_mask = cv2.inRange(image, lower_green, upper_green)
            
            # 创建输出图像（白色背景）
            result = np.ones_like(image) * 255
            
            # 将绿色区域设置为黑色（字体）
            result[green_mask > 0] = [0, 0, 0]
            
            # 转换为灰度图进行轮廓分析
            gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
            
            # 反转图像：让文字变成白色，背景变成黑色（便于轮廓检测）
            gray_inv = cv2.bitwise_not(gray)
            
            # 使用形态学操作分离斜向连接的小形状
            # 创建一个小的十字形核，只保留水平和垂直连接
            kernel = np.array([[0, 1, 0],
                              [1, 1, 1], 
                              [0, 1, 0]], dtype=np.uint8)
            
            # 先腐蚀再膨胀，分离斜向连接
            gray_separated = cv2.erode(gray_inv, kernel, iterations=1)
            gray_separated = cv2.dilate(gray_separated, kernel, iterations=1)
            
            # 查找轮廓
            contours, _ = cv2.findContours(gray_separated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 在原图上去除逗号等小形状（保持原数字不变）
            result_processed = result.copy()
            
            # 分析轮廓，识别逗号和处理0/8字符
            comma_columns = set()  # 记录包含逗号的列
            
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                
                # 检查是否为过宽的轮廓（可能是多个字符连接）
                if w > 12:  # 单个字符宽度不应超过12像素
                    self._split_wide_contour(result_processed, x, y, w, h)
                    continue
                
                # 识别逗号特征：原有条件基础上增加4个像素点面积判定
                if (area <= 14 or h <= 4 or w <= 3):
                    # 先简单删除所有小形状，观察效果
                    # 记录包含逗号的列范围
                    for col in range(x, x + w):
                        comma_columns.add(col)
                    
                    # 用白色填充逗号区域
                    cv2.fillPoly(result_processed, [contour], (255, 255, 255))
                    continue
                
                # 识别其他小形状并去除（不在逗号列删除范围内的）
                elif (area <= 10 or h <= 4 or w <= 3):
                    cv2.fillPoly(result_processed, [contour], (255, 255, 255))
            
            # 如果检测到逗号，删除包含逗号的列并左右合并
            if comma_columns:
                height, width = result_processed.shape[:2]
                
                # 创建新图像，排除逗号列
                valid_columns = [col for col in range(width) if col not in comma_columns]
                
                if valid_columns:
                    # 提取有效列进行左右合并
                    if len(result_processed.shape) == 3:  # RGB图像
                        result_merged = result_processed[:, valid_columns, :]
                    else:  # 灰度图像
                        result_merged = result_processed[:, valid_columns]
                    
                    return result_merged
            
            return result_processed
            """
            
        except Exception as e:
            print(f"配装预处理失败: {e}")
            return image
    
    def _split_wide_contour(self, image, x, y, w, h):
        """
        分割过宽的轮廓，找到最细的一列并涂成白色进行分割
        
        Args:
            image: 要处理的图像
            x, y, w, h: 轮廓的边界框
        """
        try:
            # 提取轮廓区域
            roi = image[y:y+h, x:x+w]
            
            # 转换为灰度图进行分析
            if len(roi.shape) == 3:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
            else:
                gray_roi = roi
            
            # 二值化：黑色字符为255，白色背景为0
            binary_roi = (gray_roi < 128).astype(np.uint8) * 255
            
            # 计算每列的像素密度（黑色像素数量）
            column_densities = []
            for col in range(w):
                density = np.sum(binary_roi[:, col] > 0)
                column_densities.append(density)
            
            # 找到密度最小的列（最细的连接处）
            # 排除边界列，避免切掉字符边缘
            if w > 4:  # 确保有足够的列可以选择
                search_start = max(1, w // 4)      # 从1/4处开始搜索
                search_end = min(w - 1, 3 * w // 4) # 到3/4处结束搜索
                
                min_density = float('inf')
                split_col = -1
                
                for col in range(search_start, search_end):
                    if column_densities[col] < min_density and column_densities[col] > 0:
                        min_density = column_densities[col]
                        split_col = col
                
                # 如果找到了合适的分割列，将其涂成白色
                if split_col != -1:
                    actual_col = x + split_col
                    if actual_col < image.shape[1]:
                        # 将整列涂成白色
                        for row in range(y, y + h):
                            if row < image.shape[0]:
                                image[row, actual_col] = [255, 255, 255]
            
        except Exception as e:
            pass  # 分割失败时继续处理
    
    def _is_independent_comma(self, comma_contour, all_contours, cx, cy, cw, ch):
        """
        检测小形状是否为独立的逗号（不与其他字符水平或垂直相连，斜向相连不算相连）
        
        Args:
            comma_contour: 候选逗号轮廓
            all_contours: 所有轮廓
            cx, cy, cw, ch: 候选逗号的边界框
            
        Returns:
            bool: 是否为独立逗号
        """
        try:
            # 扩展检测范围（检测水平或垂直连接）
            expand_margin = max(cw, ch) + 2  # 扩展边界
            
            # 检查附近是否有大的轮廓（字符）
            for other_contour in all_contours:
                if np.array_equal(comma_contour, other_contour):
                    continue
                
                # 获取其他轮廓的边界框
                ox, oy, ow, oh = cv2.boundingRect(other_contour)
                other_area = cv2.contourArea(other_contour)
                
                # 忽略同样小的形状
                if other_area <= 14 or oh <= 4 or ow <= 3:
                    continue
                
                # 检查是否水平或垂直相连（斜向相连不算）
                if self._is_near_or_connected(cx, cy, cw, ch, ox, oy, ow, oh, expand_margin):
                    # 如果与大轮廓水平或垂直相连，则不是独立逗号
                    return False
            
            # 暂时禁用位置检查，因为我们无法准确获取图像高度
            # 后续可以通过传入图像尺寸来改进
            # if cy < image_height * 0.6:  # 逗号在上60%区域，可能是字符部分
            #     return False
            
            return True  # 是独立逗号
            
        except Exception as e:
            return True  # 出错时默认处理为逗号
    
    def _is_near_or_connected(self, x1, y1, w1, h1, x2, y2, w2, h2, margin):
        """
        检查两个矩形是否相连（只考虑水平或垂直相连，斜向相连不算）
        
        Args:
            x1, y1, w1, h1: 第一个矩形
            x2, y2, w2, h2: 第二个矩形
            margin: 扩展边界
            
        Returns:
            bool: 是否水平或垂直相连
        """
        x1_end = x1 + w1
        y1_end = y1 + h1
        x2_end = x2 + w2
        y2_end = y2 + h2
        
        # 检查水平相连（左右相邻）
        horizontal_connected = (
            # 垂直方向有重叠
            not (y2_end < y1 or y2 > y1_end) and
            # 水平方向相邻（在margin范围内）
            (abs(x1_end - x2) <= margin or abs(x2_end - x1) <= margin)
        )
        
        # 检查垂直相连（上下相邻）
        vertical_connected = (
            # 水平方向有重叠
            not (x2_end < x1 or x2 > x1_end) and
            # 垂直方向相邻（在margin范围内）
            (abs(y1_end - y2) <= margin or abs(y2_end - y1) <= margin)
        )
        
        # 只有水平或垂直相连才算相连，斜向相连不算
        return horizontal_connected or vertical_connected
    
    def _postprocess_peizhuang_text(self, text: str, allow_list: str = None) -> str:
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
    
    def _recognize_text(self, image: Union[np.ndarray, Image.Image, str], allow_list: str = None, preprocess_type: str = None) -> List[str]:
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
    
    def _recognize_text_debug(self, image: Union[np.ndarray, Image.Image, str]) -> List[Tuple]:
        """
        识别图片中的文字（调试模式），返回完整结果
        
        Args:
            image: 图片，可以是numpy数组、PIL Image对象或图片路径
            
        Returns:
            List[Tuple]: 识别结果列表，每个元素包含(bbox, text, confidence)
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
            
            # 使用easyocr进行识别
            results = self.reader.readtext(image)
            
            return results
            
        except Exception as e:
            print(f"文字识别失败: {e}")
            return []
    
    def recognize(self, top_left: Tuple[int, int], bottom_right: Tuple[int, int], save: bool = False, allow_list: str = None, return_image: bool = False, preprocess_type: str = None, debug: bool = False):
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
            return ("", None) if return_image else ""
        
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
        if return_image:
            return (recognized_text, processed_pil)
        else:
            return recognized_text
    
    def debug(self, top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> List[Tuple]:
        """
        调试模式：从指定坐标截图并返回详细的识别结果
        
        Args:
            top_left: 左上角坐标 (x, y)
            bottom_right: 右下角坐标 (x, y)
            
        Returns:
            List[Tuple]: 详细识别结果列表，每个元素包含(bbox, text, confidence)
        """
        # 先截图
        screenshot = self._screenshot(top_left, bottom_right)
        
        if screenshot is None:
            return []
        
        # 再识别文字（调试模式）
        return self._recognize_text_debug(screenshot)
    


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