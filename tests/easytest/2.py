import re
import time
import numpy as np
import cv2
from paddleocr import PaddleOCR
from PIL import Image


class Ocr1:
    """
    高性能价格识别器 - 专门识别单个7-10位数字
    使用PaddleOCR的GPU加速和内部预处理
    """

    def __init__(self, debug=False):
        """
        初始化OCR识别器

        Args:
            debug: 是否启用调试模式
        """
        self.debug = debug

        # 编译正则表达式 - 匹配7-10位数字（带或不带逗号）
        self.price_pattern = re.compile(r'(\d{1,3}(?:,\d{3}){2,3}|\d{7,10})')

        # 字符替换映射 - 常见OCR错误
        self.char_replacements = {
            'O': '0', 'o': '0', 'B': '8',
            'l': '1', 'I': '1', 'i': '1',
            'S': '5', 's': '5',
            'Z': '2', 'z': '2',
            ' ': '', ',': ''  # 移除空格和逗号
        }

        # 初始化PaddleOCR引擎 - 使用GPU加速
        self.reader = PaddleOCR(
            use_angle_cls=False,  # 不使用文本方向分类
            lang='en',  # 英文识别
            use_gpu=True,  # 启用GPU加速
            show_log=debug  # 调试日志
        )

        if debug:
            print("✅ PriceRecognizer初始化完成 - PaddleOCR GPU加速已启用")

    def clean_and_extract_price(self, text):
        """
        清理文本并提取价格数字

        Args:
            text: 识别到的文本

        Returns:
            提取到的价格数字，未找到则返回None
        """
        if not text:
            return None

        # 字符替换
        cleaned = text
        for wrong, correct in self.char_replacements.items():
            cleaned = cleaned.replace(wrong, correct)

        # 查找匹配的价格模式
        match = self.price_pattern.search(cleaned)
        if match:
            price_str = match.group()
            # 移除逗号并验证长度
            clean_price = price_str.replace(',', '')

            if 7 <= len(clean_price) <= 10:
                try:
                    price = int(clean_price)
                    if self.debug:
                        print(f"🔍 识别结果: '{text}' -> {price}")
                    return price
                except ValueError:
                    pass

        if self.debug and text.strip():
            print(f"❌ 未找到有效价格: '{text}'")

        return None

    def recognize_price(self, image):
        """
        从图像中识别单个价格数字
        使用PaddleOCR的预处理和GPU加速

        Args:
            image: PIL Image、numpy数组或文件路径

        Returns:
            识别到的价格数字(int)，失败返回None
        """
        start_time = time.time()

        try:
            # 处理PIL图像输入 - 转换为numpy数组
            if isinstance(image, Image.Image):
                image = np.array(image)
                # PIL图像是RGB格式，PaddleOCR需要BGR格式
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # 使用PaddleOCR识别
            results = self.reader.ocr(image, cls=False)

            # 计算OCR处理时间
            ocr_time = (time.time() - start_time) * 1000  # 转换为毫秒

            # 解析PaddleOCR结果
            if results and results[0]:
                # 提取所有识别结果及其置信度
                ocr_results = []
                for line in results[0]:
                    if len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        ocr_results.append((text, confidence))

                # 按置信度排序，取最高的
                ocr_results.sort(key=lambda x: x[1], reverse=True)

                if ocr_results:
                    text, confidence = ocr_results[0]

                    if confidence > 0.5:  # 置信度阈值
                        price = self.clean_and_extract_price(text)
                        if price is not None:
                            # 总是打印OCR耗时和结果，无论debug模式
                            print(f"✅ OCR识别成功: {price} (置信度: {confidence:.2f}, 耗时: {ocr_time:.2f}ms)")
                            return price
                        else:
                            # 置信度足够但无法提取有效价格
                            print(
                                f"⚠️ OCR识别警告: 无法提取有效价格 (文本: '{text}', 置信度: {confidence:.2f}, 耗时: {ocr_time:.2f}ms)")
                    else:
                        # 置信度不足
                        print(
                            f"⚠️ OCR识别警告: 置信度不足 (文本: '{text}', 置信度: {confidence:.2f}, 耗时: {ocr_time:.2f}ms)")

                    # 如果debug模式，显示所有识别结果
                    if self.debug and len(ocr_results) > 1:
                        print(f"🔍 所有识别结果 (共{len(ocr_results)}个):")
                        for i, (text, conf) in enumerate(ocr_results):
                            print(f"  {i + 1}. 文本: '{text}', 置信度: {conf:.2f}")
            else:
                # 没有识别到任何结果
                ocr_time = (time.time() - start_time) * 1000
                print(f"❌ OCR识别失败: 未找到任何文本 (耗时: {ocr_time:.2f}ms)")

            return None

        except Exception as e:
            ocr_time = (time.time() - start_time) * 1000
            print(f"💥 OCR识别出错: {e} (耗时: {ocr_time:.2f}ms)")
            return None

    # 保持向后兼容的别名方法
    def recognize_market_price_from_image(self, image):
        """兼容旧接口 - 从图像识别价格"""
        return self.recognize_price(image)

    def recognize_market_price_from_path(self, image_path):
        """兼容旧接口 - 从文件路径识别价格"""
        return self.recognize_price(image_path)


# 使用示例
if __name__ == "__main__":
    # 创建识别器实例
    recognizer = Ocr1(debug=True)

    # 从文件识别
    price = recognizer.recognize_price("price_image.png")
    print(f"识别到的价格: {price}")