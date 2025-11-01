# 尝试相对导入，如果失败则使用绝对导入
try:
    from .DeltaForceRecognize import DeltaForceRecognize
except ImportError:
    from DeltaForceRecognize import DeltaForceRecognize

# 导入协议装饰器
try:
    from base.decorators import protocol_handler
except ImportError:
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(current_dir, '..', 'base')
    sys.path.insert(0, base_dir)
    from decorators import protocol_handler

import pyautogui
import time
import numpy as np
from PIL import Image
import pyautogui

class DeltaForceClass(DeltaForceRecognize):
    """
    主类/行为类 - DeltaForce游戏自动化操作核心
    
    该类继承自底层识别类DeltaForceRecognize，专门用于实现游戏内的各种自动化行为。
    新架构下，每个实例只绑定到一个特定的游戏窗口，不支持窗口切换。
    
    主要功能包括：
    - 绑定到指定游戏窗口
    - 游戏界面元素的识别和交互
    - 账户余额的自动识别
    - 其他游戏内单个具体行为的自动化实现
    
    使用方式：
        # 创建实例
        delta = DeltaForceClass()
        
        # 绑定到特定窗口
        success = delta.bind_to_window(hwnd)
        
        # 聚焦窗口（需要时）
        delta.focus_window()
        
        # 执行自动化操作
        balance = delta.get_balance()
    
    该类将底层识别功能与实际操作功能结合，提供完整的游戏自动化解决方案。
    所有的操作都基于屏幕坐标比例，确保在不同分辨率下的兼容性。
    
    Attributes:
        继承自DeltaForceRecognize的所有属性，包括：
        - ocr: OCR识别器实例
        - target_window_handle: 绑定的窗口句柄
        - window_width, window_height: 窗口尺寸
        - window_x, window_y: 窗口位置
        - 其他识别相关的配置参数
    
    Methods:
        bind_to_window(hwnd): 绑定到指定窗口句柄
        focus_window(): 聚焦当前绑定的窗口
        get_balance(): 识别并获取游戏内账户余额
        get_bar_price(): 识别价格条区域的数字
        get_sell_price(): 识别出售价格区域的数字
        get_ammo_price(ammo_position): 获取配装界面指定位置的子弹价格
        click_ammo(): 在战备界面点击子弹按钮
        click_ratio(x_ratio, y_ratio, do_after, do_wait): 根据比例坐标进行点击的封装方法
        move_ratio(x_ratio, y_ratio, do_after): 根据比例坐标移动鼠标的封装方法
        press_key(key, loop): 按键操作方法，包含窗口聚焦验证
        buy_in_market(buyin, maxin, times, delay, buy, loop): 交易行购买操作，支持数量选择和循环点击
        goto(action): 通用位置点击方法，支持多种预定义操作
        其他自动化操作方法将在此基础上扩展
    """
    
    def __init__(self):
        """
        初始化DeltaForce自动化操作类
        
        执行以下初始化步骤：
        1. 调用父类DeltaForceRecognize的初始化方法，设置OCR识别器
        2. 导入并配置pyautogui库，用于自动化鼠标和键盘操作
        3. 初始化窗口属性（不自动查找窗口，等待手动切换）
        
        窗口绑定通过bind_to_window(hwnd)方法实现，每个实例只管理一个窗口。
        """
        super().__init__()
        
        # 日志回调函数，用于将验证失败信息传递给GUI
        self.log_callback = None
        
        # 导入pyautogui并借用其DPI感知功能，确保在高DPI显示器上正确工作
        import pyautogui
        
        # 禁用pyautogui的默认延迟，让我们的脚本完全控制延迟时间
        pyautogui.PAUSE = 0
        
        # 初始化窗口属性为默认值，等待手动切换
        self.target_window_handle = None
        self.window_width = 1920  # 默认宽度
        self.window_height = 1080  # 默认高度
        self.window_x = 0  # 默认X位置
        self.window_y = 0  # 默认Y位置
    
    @protocol_handler()
    def get_balance(self, protocol, where="default", loop=False, return_json=False) -> bool:
        """
        自动识别游戏内账户余额
        
        该方法通过以下步骤自动获取账户余额：
        1. 点击指定位置触发余额显示界面
        2. 截取包含余额信息的屏幕区域
        3. 使用OCR技术识别数字内容
        4. 解析并返回余额数值
        
        所有坐标使用相对于游戏窗口的比例坐标，确保在不同分辨率下的兼容性。
        
        Args:
            where (str): 余额位置类型，支持以下选项：
                        "default" - 默认位置（原有位置）
                        "market" - 交易行位置
            loop (bool): 是否循环验证窗口聚焦直到成功，默认False
            return_json (bool): 是否返回JSON格式的详细调试信息，默认False
            
        Returns:
            当return_json=False时:
                int: 成功识别时返回账户余额数值
                None: 识别失败时返回None
            当return_json=True时:
                dict: 包含详细调试信息的字典，格式如下：
                    {
                        "success": bool,           # 识别是否成功
                        "balance": int or None,    # 识别出的余额数值
                        "ocr_results": list,       # OCR原始识别结果
                        "merged_text": str,        # 合并后的文本
                        "screenshot_base64": str,  # 截图的base64编码
                        "region_coords": dict,     # 识别区域坐标
                        "timestamp": str,          # 识别时间戳
                        "where": str              # 识别位置类型
                    }
            
        可能的失败原因包括：
                 - 游戏界面未正确显示
                 - OCR识别失败
                 - 截图区域无有效数字内容
                 
        Raises:
            Exception: 当操作过程中发生错误时，会捕获异常并打印错误信息
            
        Example:
            >>> delta = DeltaForceClass()
            >>> balance = delta.get_balance("default")  # 默认位置
            >>> balance = delta.get_balance("market")   # 交易行位置
        """
        # 根据where参数选择对应的位置配置
        if where == "market":
            # 交易行位置配置
            m3_ratio = (0.8665, 0.0845)  # 交易行余额点击位置
            # 交易行的识别区域需要相应偏移，保持y轴不变，x轴偏移，手动偏移
            m4_ratio = (0.7855, 0.2750)  # 余额显示区域左上角（加上偏移）
            m5_ratio = (0.9066, 0.2914)  # 余额显示区域右下角（加上偏移）
            print(f"🎯 交易行位置配置: 点击({m3_ratio[0]:.4f}, {m3_ratio[1]:.4f}), 识别区域({m4_ratio[0]:.4f}, {m4_ratio[1]:.4f}) 到 ({m5_ratio[0]:.4f}, {m5_ratio[1]:.4f})")
        else:  # where == "default" 或其他值
            # 默认位置配置
            m3_ratio = (0.8066, 0.0866)  # 默认余额点击位置
            m4_ratio = (0.7555, 0.2777)  # 余额显示区域左上角
            m5_ratio = (0.8566, 0.2914)  # 余额显示区域右下角
            print(f"🎯 默认位置配置: 点击({m3_ratio[0]:.4f}, {m3_ratio[1]:.4f}), 识别区域({m4_ratio[0]:.4f}, {m4_ratio[1]:.4f}) 到 ({m5_ratio[0]:.4f}, {m5_ratio[1]:.4f})")
        
        # 移除窗口验证逻辑
        
        try:
            # 步骤1: 点击余额按钮位置，触发余额显示界面
            click_result = self.click_ratio(m3_ratio[0], m3_ratio[1])
            protocol <<= click_result
            time.sleep(0.030)  # 最小等待，确保界面响应
            
            # 步骤2: 将比例坐标转换为屏幕绝对坐标
            m4_screen = self.ratio_to_screen_coords(m4_ratio[0], m4_ratio[1])  # 截图区域左上角
            m5_screen = self.ratio_to_screen_coords(m5_ratio[0], m5_ratio[1])  # 截图区域右下角
            if not m4_screen or not m5_screen:
                protocol.error_message = "坐标转换失败"
                return False
            
            # 步骤3: 计算截图区域的边界坐标
            # 确保left < right 和 top < bottom，处理可能的坐标顺序问题
            left = min(m4_screen[0], m5_screen[0])
            top = min(m4_screen[1], m5_screen[1])
            right = max(m4_screen[0], m5_screen[0])
            bottom = max(m4_screen[1], m5_screen[1])
            
            # 步骤4: 截取包含余额信息的屏幕区域
            screenshot = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
            screenshot_array = np.array(screenshot)  # 转换为numpy数组供OCR使用
            
            # 步骤5: 使用OCR技术识别截图中的数字内容
            # 配置OCR参数以优化数字识别准确性
            results = self.ocr.reader.readtext(
                screenshot_array,
                allowlist='1234567890',  # 限制只识别数字字符，提高准确性
                width_ths=0.7,          # 文本框宽度阈值
                height_ths=0.7,         # 文本框高度阈值
                text_threshold=0.5,     # 文本置信度阈值
                decoder='beamsearch'    # 使用束搜索解码器提高识别准确性
            )
            
            # 准备JSON返回数据（如果需要）
            if return_json:
                import base64
                from io import BytesIO
                from datetime import datetime
                
                # 将截图转换为base64编码
                buffer = BytesIO()
                screenshot.save(buffer, format='PNG')
                screenshot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # 准备OCR结果数据
                ocr_results_data = []
                for bbox, text, confidence in results:
                    ocr_results_data.append({
                        "bbox": bbox.tolist() if hasattr(bbox, 'tolist') else bbox,
                        "text": text,
                        "confidence": float(confidence)
                    })
            
            # 步骤6: 处理OCR识别结果并提取余额数值
            if results:
                # 记录详细的OCR调试信息
                print(f"🔍 OCR识别结果 ({where}位置):")
                for i, (bbox, text, confidence) in enumerate(results):
                    print(f"  结果{i+1}: 文本='{text}', 置信度={confidence:.3f}, 位置={bbox}")
                
                # 合并所有识别到的数字文本片段
                combined_text = ""
                for (bbox, text, confidence) in results:
                    # 过滤非数字字符，只保留数字
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                print(f"📊 合并后的数字文本: '{combined_text}'")
                
                # 将合并后的数字字符串转换为整数
                if combined_text:
                    balance = int(combined_text)
                    print(f"✅ 成功识别账户余额: {balance}")
                    
                    # 将结果存储到协议中
                    protocol.balance = balance
                    protocol.where = where
                    protocol.combined_text = combined_text
                    
                    
                    if return_json:
                        protocol.json_result = {
                            "success": True,
                            "balance": balance,
                            "ocr_results": ocr_results_data,
                            "merged_text": combined_text,
                            "screenshot_base64": screenshot_base64,
                            "region_coords": {
                                "left": left,
                                "top": top,
                                "right": right,
                                "bottom": bottom,
                                "m4_ratio": m4_ratio,
                                "m5_ratio": m5_ratio
                            },
                            "timestamp": datetime.now().isoformat(),
                            "where": where
                        }
                    
                    return True
                else:
                    print("❌ 余额识别失败：OCR结果中未找到有效数字")
                    
                    protocol.error_message = "OCR结果中未找到有效数字"
                    protocol.where = where
                    protocol.combined_text = combined_text
                    
                    if return_json:
                        protocol.json_result = {
                            "success": False,
                            "balance": None,
                            "ocr_results": ocr_results_data,
                            "merged_text": combined_text,
                            "screenshot_base64": screenshot_base64,
                            "region_coords": {
                                "left": left,
                                "top": top,
                                "right": right,
                                "bottom": bottom,
                                "m4_ratio": m4_ratio,
                                "m5_ratio": m5_ratio
                            },
                            "timestamp": datetime.now().isoformat(),
                            "where": where,
                            "error": "OCR结果中未找到有效数字"
                        }
                    
                    return False
            else:
                print("❌ 余额识别失败：OCR未返回任何识别结果")
                protocol.error_message = "OCR未返回任何识别结果"
                protocol.where = where
                
                if return_json:
                    import base64
                    from io import BytesIO
                    from datetime import datetime
                    
                    # 将截图转换为base64编码
                    buffer = BytesIO()
                    screenshot.save(buffer, format='PNG')
                    screenshot_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    return {
                        "success": False,
                        "balance": None,
                        "ocr_results": [],
                        "merged_text": "",
                        "screenshot_base64": screenshot_base64,
                        "region_coords": {
                            "left": left,
                            "top": top,
                            "right": right,
                            "bottom": bottom,
                            "m4_ratio": m4_ratio,
                            "m5_ratio": m5_ratio
                        },
                        "timestamp": datetime.now().isoformat(),
                        "where": where,
                        "error": "OCR未返回任何识别结果"
                    }
                else:
                    protocol.error_message = "OCR未返回任何识别结果"
                    return False
                
        except Exception as e:
            # 捕获并处理所有可能的异常情况
            print(f"余额识别过程中发生错误: {e}")
            
            if return_json:
                from datetime import datetime
                return {
                    "success": False,
                    "balance": None,
                    "ocr_results": [],
                    "merged_text": "",
                    "screenshot_base64": "",
                    "region_coords": {},
                    "timestamp": datetime.now().isoformat(),
                    "where": where,
                    "error": str(e)
                }
            else:
                protocol.error_message = "处理异常"
                return False

    @protocol_handler()
    def get_bar_price(self, protocol) -> bool:
        """
        识别价格条区域的数字
        
        该方法识别屏幕上指定区域(2305.6938到2862.7101)的数字内容。
        使用OCR技术只识别数字字符，适用于价格、数量等数值的识别。
        
        Returns:
            str: 成功识别时返回数字字符串
            None: 识别失败时返回None，可能的失败原因包括：
                 - 指定区域无有效数字内容
                 - OCR识别失败
                 - 截图操作失败
                 
        Example:
            >>> delta = DeltaForceClass()
            >>> price = delta.get_bar_price()
            >>> if price is not None:
            ...     print(f"识别到的价格: {price}")
            ... else:
            ...     print("价格识别失败")
        """
        # 定义识别区域的比例坐标
        top_left_ratio = (0.2305, 0.6938)      # 左上角坐标
        bottom_right_ratio = (0.2862, 0.7101)  # 右下角坐标
        
        # 将比例坐标转换为屏幕坐标
        screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        # 截图指定区域
        screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
        screenshot_array = np.array(screenshot)
        
        # 使用OCR识别，只识别数字
        results = self.ocr.reader.readtext(
            screenshot_array,
            allowlist='1234567890',  # 限制只识别数字字符
            width_ths=0.7,
            height_ths=0.7,
            text_threshold=0.5,
            decoder='beamsearch'
        )
        
        # 处理识别结果
        if results:
            # 合并所有识别到的数字
            combined_text = ""
            for (bbox, text, confidence) in results:
                # 只保留数字字符
                filtered_text = ''.join(char for char in text if char.isdigit())
                combined_text += filtered_text
            
            if combined_text:
                print(f"成功识别价格条数字: {combined_text}")
                protocol.price = combined_text
                return True
            else:
                protocol.error_message = "未识别到有效数字"
                return False
        else:
            protocol.error_message = "OCR无结果"
            return False

    @protocol_handler()
    def get_sell_price(self, protocol) -> bool:
        """
        识别出售价格区域的数字
        
        该方法识别屏幕上指定区域(6366.5935到7237.6156)的数字内容。
        使用OCR技术只识别数字字符，适用于出售价格等数值的识别。
        
        Returns:
            str: 成功识别时返回数字字符串
            None: 识别失败时返回None，可能的失败原因包括：
                 - 指定区域无有效数字内容
                 - OCR识别失败
                 - 截图操作失败
                 
        Example:
            >>> delta = DeltaForceClass()
            >>> sell_price = delta.get_sell_price()
            >>> if sell_price is not None:
            ...     print(f"识别到的出售价格: {sell_price}")
            ... else:
            ...     print("出售价格识别失败")
        """
        # 定义识别区域的比例坐标
        top_left_ratio = (0.6366, 0.5935)      # 左上角坐标
        bottom_right_ratio = (0.7237, 0.6156)  # 右下角坐标
        
        # 将比例坐标转换为屏幕坐标
        screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        # 截图指定区域
        screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
        screenshot_array = np.array(screenshot)
        
        # 使用OCR识别，只识别数字
        results = self.ocr.reader.readtext(
            screenshot_array,
            allowlist='1234567890',  # 限制只识别数字字符
            width_ths=0.7,
            height_ths=0.7,
            text_threshold=0.5,
            decoder='beamsearch'
        )
        
        # 处理识别结果
        if results:
            # 合并所有识别到的数字
            combined_text = ""
            for (bbox, text, confidence) in results:
                # 只保留数字字符
                filtered_text = ''.join(char for char in text if char.isdigit())
                combined_text += filtered_text
            
            if combined_text:
                print(f"成功识别出售价格: {combined_text}")
                protocol.sell_price = combined_text
                return True
            else:
                protocol.error_message = "未识别到有效数字"
                return False
        else:
            protocol.error_message = "OCR无结果"
            return False

    @protocol_handler()
    def get_ammo_price(self, protocol, ammo_position, loop=False) -> bool:
        """
        获取配装界面子弹价格
        
        该方法识别配装界面中指定位置的子弹价格。
        根据传入的位置参数，识别对应位置的价格数字。
        
        Args:
            ammo_position (int): 子弹位置编号，必须传入，无默认值
                               1 - 第1个位置的子弹价格 (0.7200,0.3273 到 0.7577,0.3464)
                               2 - 第2个位置的子弹价格 (0.8962,0.3273 到 0.9339,0.3464)
                               3 - 第3个位置的子弹价格 (0.7200,0.4244 到 0.7577,0.4435)
                               4 - 第4个位置的子弹价格 (0.8956,0.4265 到 0.9333,0.4456)
                               5 - 第5个位置的子弹价格 (0.7194,0.5237 到 0.7571,0.5428)
                               6 - 第6个位置的子弹价格 (0.8956,0.5237 到 0.9333,0.5428)
            loop (bool): 是否循环验证窗口聚焦直到成功，默认False
        
        Returns:
            str: 成功识别时返回价格数字字符串
            None: 识别失败时返回None，可能的失败原因包括：
                 - 传入的位置参数无效
                 - 指定区域无有效数字内容
                 - OCR识别失败
                 - 截图操作失败
        
        Raises:
            ValueError: 当未传入ammo_position参数或参数无效时抛出异常
        
        Example:
            >>> delta = DeltaForceClass()
            >>> # 获取第1个位置的子弹价格
            >>> price1 = delta.get_ammo_price(1)
            >>> if price1 is not None:
            ...     print(f"第1个位置子弹价格: {price1}")
            >>> # 获取第2个位置的子弹价格
            >>> price2 = delta.get_ammo_price(2)
            >>> if price2 is not None:
            ...     print(f"第2个位置子弹价格: {price2}")
            >>> # 获取第6个位置的子弹价格
            >>> price6 = delta.get_ammo_price(6)
            >>> if price6 is not None:
            ...     print(f"第6个位置子弹价格: {price6}")
        """
        # 移除窗口验证逻辑
        
        try:
            # 检查是否传入了必需的参数
            if ammo_position is None:
                protocol.error_message = "必须传入ammo_position参数，无默认值"
                return False
            
            # 根据子弹位置确定识别区域的比例坐标
            # 区域大小：宽度0.0377，高度0.0191 (基于1号位置计算)
            width = 0.0377
            height = 0.0191
            
            if ammo_position == 1:
                bottom_right_ratio = (0.7577, 0.3464)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 2:
                bottom_right_ratio = (0.9333, 0.3464)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 3:
                bottom_right_ratio = (0.7577, 0.4435)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 4:
                bottom_right_ratio = (0.9333, 0.4435)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 5:
                bottom_right_ratio = (0.7577, 0.5428)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 6:
                bottom_right_ratio = (0.9333, 0.5428)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            else:
                protocol.error_message = f"不支持的子弹位置: {ammo_position}，当前支持位置: 1, 2, 3, 4, 5, 6"
                return False
            
            # 将比例坐标转换为屏幕坐标
            screen_left, screen_top = self.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
            screen_right, screen_bottom = self.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
            
            # 截图指定区域
            screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
            screenshot_array = np.array(screenshot)
            
            # 使用OCR识别，只识别数字
            results = self.ocr.reader.readtext(
                screenshot_array,
                allowlist='1234567890',
                width_ths=0.7,
                height_ths=0.7,
                text_threshold=0.5,
                decoder='beamsearch'
            )
            
            # 处理识别结果
            if results:
                combined_text = ""
                for (bbox, text, confidence) in results:
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                if combined_text:
                    protocol.ammo_price = combined_text
                    return True
                else:
                    protocol.error_message = f"第{ammo_position}个位置子弹价格识别失败：未识别到有效数字"
                    return False
            else:
                protocol.error_message = f"第{ammo_position}个位置子弹价格识别失败：OCR无结果"
                return False
                
        except Exception as e:
            protocol.error_message = f"第{ammo_position}个位置子弹价格识别过程中发生错误: {e}"
            return False
    

    @protocol_handler()
    def click_ammo(self, protocol, loop=False) -> bool:
        """
        在战备界面点击子弹
        
        该方法在战备界面中点击子弹按钮，用于进入子弹配装界面。
        使用固定的比例坐标进行点击操作。
        
        Args:
            loop (bool): 是否循环验证窗口聚焦直到成功，默认False
        
        Returns:
            bool: 点击成功返回True，失败返回False
            
        Example:
            >>> delta = DeltaForceClass()
            >>> if delta.click_ammo():
            ...     print("成功点击子弹按钮")
            ... else:
            ...     print("点击子弹按钮失败")
        """
        # 移除窗口验证逻辑
        
        # 直接使用click_ratio方法点击子弹按钮
        click_result = self.click_ratio(0.8400, 0.7000)
        if click_result:
            protocol <<= click_result
            return True
        else:
            protocol.error_message = "点击子弹按钮失败"
            return False

    @protocol_handler()
    def click_ratio(self, protocol, x_ratio, y_ratio, do_after=0.0, do_wait=0.0) -> bool:
        """
        根据比例坐标进行点击的方法
        
        Args:
            x_ratio (float): X轴比例坐标，范围0.0-1.0
            y_ratio (float): Y轴比例坐标，范围0.0-1.0
            do_after (float): 点击前等待时间，默认0.0秒
            do_wait (float): 点击后等待时间，默认0.0秒
        
        Returns:
            bool: 点击成功返回True，失败返回False
        """
        try:
            # 验证坐标范围
            if not (0.0 <= x_ratio <= 1.0 and 0.0 <= y_ratio <= 1.0):
                protocol.error_message = f"坐标超出范围: x_ratio={x_ratio}, y_ratio={y_ratio}"
                return False
            
            # 移动前等待
            if do_after > 0:
                time.sleep(do_after)
            
            # 将比例坐标转换为屏幕坐标
            screen_coords = self.ratio_to_screen_coords(x_ratio, y_ratio)
            if not screen_coords:
                protocol.error_message = "坐标转换失败"
                return False
            
            # 移动鼠标到目标位置
            pyautogui.moveTo(screen_coords[0], screen_coords[1])
            
            # 移动和点击之间添加短暂延迟
            time.sleep(0.009)
            
            # 执行点击
            pyautogui.click()
            
            # 点击后等待
            if do_wait > 0:
                time.sleep(do_wait)
            
            protocol.click_success = True
            return True
            
        except Exception as e:
            protocol.error_message = f"点击操作失败: {e}"
            return False
    
    @protocol_handler()
    def move_ratio(self, protocol, x_ratio, y_ratio, do_after=0.0) -> bool:
        """
        根据比例坐标移动鼠标的方法
        
        Args:
            x_ratio (float): X轴比例坐标，范围0.0-1.0
            y_ratio (float): Y轴比例坐标，范围0.0-1.0
            do_after (float): 移动前等待时间，默认0.0秒
        
        Returns:
            bool: 移动成功返回True，失败返回False
        """
        try:
            # 验证坐标范围
            if not (0.0 <= x_ratio <= 1.0 and 0.0 <= y_ratio <= 1.0):
                protocol.error_message = f"坐标超出范围: x_ratio={x_ratio}, y_ratio={y_ratio}"
                return False
            
            # 移动前等待
            if do_after > 0:
                time.sleep(do_after)
            
            # 将比例坐标转换为屏幕坐标
            screen_coords = self.ratio_to_screen_coords(x_ratio, y_ratio)
            if not screen_coords:
                protocol.error_message = "坐标转换失败"
                return False
            
            # 执行移动操作
            pyautogui.moveTo(screen_coords[0], screen_coords[1])
            
            protocol.move_success = True
            return True
            
        except Exception as e:
            protocol.error_message = f"移动操作失败: {e}"
            return False
    
    @protocol_handler()
    def click(self, protocol) -> bool:
        """
        简单的左键点击方法
        在当前鼠标位置执行左键点击，不进行任何坐标转换或窗口验证
        """
        try:
            pyautogui.click()
            return True
        except Exception as e:
            print(f"点击操作失败: {e}")
            return False
    
    

    @protocol_handler()
    @protocol_handler()
    def press_key(self, protocol, key) -> bool:
        """
        按键操作方法
        
        Args:
            key (str): 要按的键名（如 'esc', 'enter', 'space' 等）
        
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        try:
            import pyautogui
            pyautogui.press(key)
            protocol.key_pressed = key
            return True
            
        except Exception as e:
            protocol.error_message = f"按键操作失败: {e}"
            return False

    @protocol_handler()
    def buy_in_market(self, protocol, buyin, maxin, times=1, delay=0.1, buy=True, loop=False) -> bool:
        """
        交易行购买操作
        
        在交易行界面执行购买操作，包括数量选择、预备点击和循环购买点击。
        
        Args:
            buyin (int): 购买数量（必须参数）
            maxin (int): 最大数量（必须参数）
            times (int): 循环点击购买按钮的次数，默认1次（不循环）
            delay (float): 每次点击之间的延迟时间（秒），默认0.1秒
            buy (bool): 是否执行实际购买操作，默认True。False时仅选择数量，用于测试
            loop (bool): 是否循环验证窗口聚焦直到成功，默认False
        
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        # 验证参数
        if buyin <= 0 or maxin <= 0:
            print(f"❌ [buy_in_market] 参数错误: buyin={buyin}, maxin={maxin}")
            return False
        
        if buyin > maxin:
            print(f"❌ [buy_in_market] 购买数量({buyin})不能超过最大数量({maxin})")
            return False
        
        # 移除窗口验证逻辑
        
        try:
            # 计算数量选择条的点击位置
            left_ratio = 0.7890   # 最左侧位置
            right_ratio = 0.9036  # 最右侧位置
            y_ratio = 0.7233      # 纵坐标位置
            
            # 计算购买比例 - 直接映射逻辑
            # 31/200 -> 除去两端后映射到 30/199 的位置
            
            if maxin == 1:
                quantity_ratio = 0.0
            else:
                # 直接比例映射：buyin在1-maxin范围内映射到0%-100%
                quantity_ratio = (buyin - 1) / (maxin - 1)
            
            # 计算实际点击的X坐标比例
            click_x_ratio = left_ratio + (right_ratio - left_ratio) * quantity_ratio
            
            print(f"📊 [buy_in_market] 数量选择: {buyin}/{maxin}")
            print(f"🔍 [buy_in_market] 计算过程: ({buyin}-1)/({maxin}-1) = {buyin-1}/{maxin-1} = {quantity_ratio:.4f} ({quantity_ratio:.2%})")
            print(f"🎯 [buy_in_market] 点击位置: ({click_x_ratio:.4f}, {y_ratio})")
            
            # 点击数量选择条
            click_result = self.click_ratio(click_x_ratio, y_ratio)
            protocol <<= click_result
            if not click_result.success:
                protocol.error_message = "数量选择点击失败"
                return False
            
            print(f"✅ [buy_in_market] 数量选择完成: {buyin}/{maxin}")
            
            # 如果buy为False，则只进行数量选择，不执行购买
            if not buy:
                print("🧪 [buy_in_market] 测试模式，跳过购买操作")
                return True
            
            # 短暂延迟后执行购买操作
            time.sleep(0.005)
            
            # 先点击预备位置 (0.0711, 0.1985) - 已被用户注释掉
            # if not self._click_ratio_internal(0.0711, 0.1985):
            #     print("❌ [buy_in_market] 预备点击失败")
            #     return False
            
            # print("✅ [buy_in_market] 预备点击完成")
            # import time
            # time.sleep(0.02)  # 预备点击后的短暂延迟
            
            # 循环点击购买按钮 (0.8511, 0.7994)
            for i in range(times):
                buy_click_result = self.click_ratio(0.8511, 0.7994)
                protocol <<= buy_click_result
                if not buy_click_result.success:
                    protocol.error_message = f"第 {i+1} 次购买点击失败"
                    return False
                
                print(f"✅ [buy_in_market] 完成第 {i+1}/{times} 次购买点击")
                
                # 除了最后一次，都需要延迟
                if i < times - 1:
                    time.sleep(delay)
            
            print(f"✅ [buy_in_market] 购买操作完成，数量: {buyin}/{maxin}，点击 {times} 次")
            return True
            
        except Exception as e:
            print(f"❌ [buy_in_market] 购买操作失败: {e}")
            return False

    @protocol_handler()
    def goto(self, protocol, action) -> bool:
        """
        通用位置点击方法，根据action参数执行相应的点击操作
        
        Args:
            action (str): 指定要执行的操作类型
        
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        # 根据action参数执行相应操作
        if action == "555":
            # 点击余额按钮
            click_result = self.click_ratio(0.8066, 0.0866)
            if click_result:
                protocol <<= click_result
                return True
            else:
                protocol.error_message = "点击555按钮失败"
                return False
             
        elif action == "开始游戏":
            # 点击开始游戏按钮
            click_result = self.click_ratio(0.1057, 0.0866)
            if click_result:
                protocol <<= click_result
                return True
            else:
                protocol.error_message = "点击开始游戏按钮失败"
                return False
            
        elif action == "交易行":
            # 点击交易行按钮
            click_result = self.click_ratio(0.3727, 0.0866)
            if click_result:
                protocol <<= click_result
                return True
            else:
                protocol.error_message = "点击交易行按钮失败"
                return False
            
        elif action == "仓库":
            # 点击仓库按钮
            click_result = self.click_ratio(0.1718, 0.0866)
            if click_result:
                protocol <<= click_result
                return True
            else:
                protocol.error_message = "点击仓库按钮失败"
                return False
            
        elif action == "出售":
            # 出售操作：先点击交易行，延迟1秒后点击出售位置
            # 第一步：点击交易行
            if not self.click_ratio(0.3727, 0.0866):
                return False
            # 第二步：延迟1秒后点击出售位置
            click_result = self.click_ratio(0.1760, 0.1362, do_after=1.0)
            if click_result:
                protocol <<= click_result
                return True
            else:
                protocol.error_message = "点击出售位置失败"
                return False
            
        else:
            # 不支持的操作类型
            print(f"不支持的操作类型: {action}")
            return False
    
    @protocol_handler()
    def get_buy_price(self, protocol) -> bool:
        """
        获取购买价格
        识别指定区域的数字
        
        Returns:
            int: 识别到的价格数字，识别失败返回None
        """
        try:
            # 定义识别区域的比例坐标
            top_left_ratio = (0.8368, 0.8015)
            bottom_right_ratio = (0.9023, 0.8163)
            
            # 使用OCR识别该区域的数字
            result = self.recognize(
                top_left_ratio=top_left_ratio,
                bottom_right_ratio=bottom_right_ratio,
                allow_list='0123456789',  # 只识别数字
                preprocess_type='peizhuang'  # 使用配装价格的预处理
            )
            
            if result and result.strip():
                # 尝试转换为整数
                price = int(result.strip())
                protocol.buy_price = price
                return True
            else:
                protocol.error_message = "无法获取购买价格"
                return False
                
        except Exception as e:
            print(f"获取购买价格失败: {e}")
            protocol.error_message = str(e)
            return False
    
    @protocol_handler()
    def bind_to_window(self, protocol, hwnd) -> bool:
        """
        绑定到指定的窗口句柄（不切换焦点，只获取窗口信息）
        
        新架构下每个DeltaForce实例只管理一个窗口，不需要切换功能
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            bool: 绑定是否成功
        """
        try:
            # 直接设置目标窗口句柄
            self.target_window_handle = hwnd
            
            # 更新窗口信息（不切换焦点）
            self._update_window_info()
            
            # 验证窗口信息是否有效
            if self.window_width <= 0 or self.window_height <= 0:
                print(f"⚠️ 窗口 {hwnd} 信息无效: {self.window_width}x{self.window_height}")
                return False
            
            print(f"✅ 成功绑定到窗口 {hwnd} (尺寸: {self.window_width}x{self.window_height})")
            protocol.window_handle = hwnd
            protocol.window_size = (self.window_width, self.window_height)
            return True
            
        except Exception as e:
            print(f"❌ 绑定窗口 {hwnd} 失败: {e}")
            protocol.error_message = str(e)
            return False
    
    @protocol_handler()
    def set_log_callback(self, protocol, callback) -> bool:
        """
        设置日志回调函数，用于将验证失败信息传递给GUI
        
        Args:
            callback: 回调函数，接受一个字符串参数（日志消息）
        """
        self.log_callback = callback
        protocol.callback_set = True
        return True
    
    @protocol_handler()
    def focus_window(self, protocol) -> bool:
        """
        聚焦当前绑定的窗口
        
        Returns:
            bool: 聚焦是否成功
        """
        if self.target_window_handle is None:
            print("❌ 未绑定任何窗口")
            return False
        
        try:
            import ctypes
            ctypes.windll.user32.SetForegroundWindow(self.target_window_handle)
            ctypes.windll.user32.ShowWindow(self.target_window_handle, 9)  # SW_RESTORE
            
            protocol.focus_success = True
            return True
            
        except Exception as e:
            print(f"❌ 聚焦窗口失败: {e}")
            protocol.error_message = str(e)
            return False
    
    @protocol_handler()
    def get_foreground_window_handle(self, protocol) -> bool:
        """
        获取当前前台窗口的句柄
        
        Returns:
            int: 前台窗口句柄，失败返回None
        """
        try:
            import ctypes
            handle = ctypes.windll.user32.GetForegroundWindow()
            protocol.foreground_handle = handle
            return True
        except Exception as e:
            print(f"❌ 获取前台窗口句柄失败: {e}")
            protocol.error_message = str(e)
            return False
    
    @protocol_handler()
    def verify_window_focus(self, protocol, loop=False) -> bool:
        """
        验证窗口聚焦状态 - 在每个行为执行前调用此函数进行验证
        
        该函数会：
        1. 尝试聚焦到当前绑定的窗口
        2. 检测聚焦后的实际前台窗口是否为目标窗口
        3. 如果不匹配，打印调试信息
        4. 根据loop参数决定是否循环重试
        
        Args:
            loop (bool): 是否循环重试直到成功
                        False - 只执行一次验证（默认）
                        True - 持续重试直到窗口聚焦成功
        
        Returns:
            bool: True表示窗口聚焦正确，False表示聚焦失败（仅在loop=False时可能返回False）
        """
        if self.target_window_handle is None:
            print("❌ [窗口验证] 未绑定任何窗口")
            return False
        
        # 静默验证，不输出日志
        
        if not loop:
            # 非循环模式：只尝试1次
            retry_count = 0
            max_retries = 1
            
            while retry_count < max_retries:
                retry_count += 1
                
                # 1. 尝试聚焦到目标窗口
                focus_success = self.focus_window()
                if not focus_success:
                    print(f"❌ [窗口验证] 聚焦操作失败")
                    return False
                
                # 2. 短暂等待聚焦生效
                time.sleep(0.01)
                
                # 3. 检测当前前台窗口
                current_foreground_result = self.get_foreground_window_handle()
                if not current_foreground_result:
                    print(f"❌ [窗口验证] 无法获取当前前台窗口句柄")
                    protocol <<= current_foreground_result
                    return False
                protocol <<= current_foreground_result
                current_foreground = current_foreground_result.foreground_handle
                
                # 4. 验证是否为目标窗口
                if current_foreground == self.target_window_handle:
                    protocol.window_handle = current_foreground
                    return True
                else:
                    error_msg = f"❌ [窗口验证] 窗口聚焦验证失败! 目标窗口: {self.target_window_handle}, 实际前台: {current_foreground}"
                    print(error_msg)
                    print(f"   建议: 检查窗口是否被其他程序覆盖或最小化")
                    
                    # 如果设置了日志回调，将失败信息发送到GUI
                    if self.log_callback:
                        self.log_callback(error_msg)
                    
                    return False
        else:
            # 循环模式：先尝试正常验证，失败时进入缓冲循环
            retry_count = 0
            max_normal_retries = 50  # 正常重试次数
            
            # 第一阶段：正常循环重试
            while retry_count < max_normal_retries:
                retry_count += 1
                
                if retry_count > 1:
                    print(f"🔄 [窗口验证] 第 {retry_count} 次重试...")
                
                # 1. 尝试聚焦到目标窗口
                focus_success = self.focus_window()
                if not focus_success:
                    print(f"⚠️ [窗口验证] 第 {retry_count} 次聚焦操作失败，等待后重试...")
                    time.sleep(0.5)
                    continue
                
                # 2. 短暂等待聚焦生效
                time.sleep(0.01)
                
                # 3. 检测当前前台窗口
                current_foreground_result = self.get_foreground_window_handle()
                if not current_foreground_result:
                    print(f"⚠️ [窗口验证] 第 {retry_count} 次无法获取前台窗口句柄，等待后重试...")
                    protocol <<= current_foreground_result
                    time.sleep(0.5)
                    continue
                protocol <<= current_foreground_result
                current_foreground = current_foreground_result.foreground_handle
                
                # 4. 验证是否为目标窗口
                if current_foreground == self.target_window_handle:
                    protocol.window_handle = current_foreground
                    return True  # 验证成功，正常返回True
                else:
                    print(f"⚠️ [窗口验证] 第 {retry_count} 次验证失败 - 目标: {self.target_window_handle}, 实际: {current_foreground}")
                    time.sleep(0.5)
            
            # 第二阶段：正常重试失败，进入缓冲循环模式
            print(f"⚠️ [窗口验证] 正常重试 {max_normal_retries} 次失败，进入缓冲循环模式")
            
            buffer_cycles = 5  # 缓冲循环次数
            verifications_per_cycle = 10  # 每个缓冲循环的验证次数
            
            print(f"🔄 [窗口验证] 进入缓冲模式，将执行 {buffer_cycles} 个缓冲循环以防止程序出错")
            print(f"⚠️ [窗口验证] 注意：由于时效性问题，缓冲模式最终将返回失败")
            
            for buffer_cycle in range(buffer_cycles):
                print(f"🔄 [窗口验证] 开始第 {buffer_cycle + 1}/{buffer_cycles} 个缓冲循环")
                
                # 每个缓冲循环内进行10次验证
                for verification in range(verifications_per_cycle):
                    # 1. 尝试聚焦到目标窗口
                    focus_success = self.focus_window()
                    if not focus_success:
                        print(f"⚠️ [窗口验证] 缓冲循环 {buffer_cycle + 1} - 第 {verification + 1} 次聚焦操作失败")
                        time.sleep(0.5)
                        continue
                    
                    # 2. 短暂等待聚焦生效
                    time.sleep(0.01)
                    
                    # 3. 检测当前前台窗口
                    current_foreground = self.get_foreground_window_handle()
                    if current_foreground is None:
                        print(f"⚠️ [窗口验证] 缓冲循环 {buffer_cycle + 1} - 第 {verification + 1} 次无法获取前台窗口句柄")
                        time.sleep(0.5)
                        continue
                    
                    # 4. 验证是否为目标窗口
                    if current_foreground == self.target_window_handle:
                        print(f"✅ [窗口验证] 缓冲循环 {buffer_cycle + 1} - 第 {verification + 1} 次验证成功，但由于时效性问题返回失败")
                        # 注意：缓冲模式下即使验证成功也返回False（时效性问题）
                        break  # 跳出内层验证循环
                    else:
                        print(f"⚠️ [窗口验证] 缓冲循环 {buffer_cycle + 1} - 第 {verification + 1} 次验证失败 - 目标: {self.target_window_handle}, 实际: {current_foreground}")
                        time.sleep(0.5)
                
                # 如果当前缓冲循环的10次验证都失败了
                if buffer_cycle < buffer_cycles - 1:  # 不是最后一个缓冲循环
                    print(f"🔄 [窗口验证] 缓冲循环 {buffer_cycle + 1} 的10次验证完成，执行Alt+Tab窗口切换")
                    
                    # 执行3次Alt+Tab操作
                    try:
                        import pyautogui
                        for alt_tab_count in range(3):
                            print(f"⌨️ [窗口验证] 执行第 {alt_tab_count + 1}/3 次 Alt+Tab 操作")
                            pyautogui.hotkey('alt', 'tab')
                            time.sleep(0.5)  # 每次Alt+Tab之间等待0.5秒
                        
                        print(f"✅ [窗口验证] Alt+Tab操作完成，准备进入下个缓冲循环")
                        time.sleep(1.0)  # Alt+Tab操作后等待1秒
                        
                    except Exception as e:
                        print(f"❌ [窗口验证] Alt+Tab操作失败: {e}")
                else:
                    # 最后一个缓冲循环完成
                    print(f"🔄 [窗口验证] 所有 {buffer_cycles} 个缓冲循环已完成")
            
            # 缓冲循环完成，返回False
            error_msg = f"❌ [窗口验证] 缓冲模式完成，窗口验证最终失败 (目标窗口: {self.target_window_handle})"
            print(error_msg)
            print(f"   说明: 经过正常重试和缓冲循环，仍无法验证窗口聚焦")
            
            # 如果设置了日志回调，将失败信息发送到GUI
            if self.log_callback:
                self.log_callback(error_msg)
            
            return False
        
        # 这里不应该到达，但为了安全起见
        return False

# 模块测试代码
if __name__ == "__main__":
    # 创建DeltaForceClass实例
    delta = DeltaForceClass()
    
    # 测试余额识别功能
    # print("=== 测试余额识别功能 ===")
    # balance = delta.get_balance()
    # if balance is not None:
    #     print(f"测试成功 - 当前账户余额: {balance}")
    # else:
    #     print("测试失败 - 无法识别账户余额")
    
    print("\n=== 测试get_bar_price方法功能 ===")
    
    print("测试价格条数字识别:")
    bar_price = delta.get_bar_price()
    if bar_price is not None:
        print(f"✓ 价格条识别成功: {bar_price}")
    else:
        print("✗ 价格条识别失败")
    
    # 测试get_sell_price方法功能
    print("\n=== 测试get_sell_price方法功能 ===")
    
    print("测试出售价格数字识别:")
    sell_price = delta.get_sell_price()
    if sell_price is not None:
        print(f"✓ 出售价格识别成功: {sell_price}")
    else:
        print("✗ 出售价格识别失败")
    
    print("\n=== 测试完成 ===")
    
