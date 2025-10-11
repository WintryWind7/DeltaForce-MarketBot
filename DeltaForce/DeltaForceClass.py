from DeltaForceRecognize import DeltaForceRecognize
import pyautogui
import time
import numpy as np
from PIL import Image

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
        
        # 初始化窗口属性为默认值，等待手动切换
        self.target_window_handle = None
        self.window_width = 1920  # 默认宽度
        self.window_height = 1080  # 默认高度
        self.window_x = 0  # 默认X位置
        self.window_y = 0  # 默认Y位置
    
    def get_balance(self, m3_ratio=(0.8066, 0.0866), m4_ratio=(0.7555, 0.2777), m5_ratio=(0.8566, 0.2914)):
        """
        自动识别游戏内账户余额
        
        该方法通过以下步骤自动获取账户余额：
        1. 点击指定位置触发余额显示界面
        2. 截取包含余额信息的屏幕区域
        3. 使用OCR技术识别数字内容
        4. 解析并返回余额数值
        
        所有坐标使用相对于游戏窗口的比例坐标，确保在不同分辨率下的兼容性。
        
        Args:固定值
            m3_ratio (tuple): 触发余额显示的点击位置比例坐标 (x_ratio, y_ratio)
                            默认值 (0.8066, 0.0866) 对应游戏界面中的余额按钮位置
            m4_ratio (tuple): 余额显示区域左上角的比例坐标 (x_ratio, y_ratio)
                            默认值 (0.7555, 0.2777) 定义截图区域的起始点
            m5_ratio (tuple): 余额显示区域右下角的比例坐标 (x_ratio, y_ratio)
                            默认值 (0.8566, 0.2914) 定义截图区域的结束点
            
        Returns:
            int: 成功识别时返回账户余额数值
            None: 识别失败时返回None，可能的失败原因包括：
                 - 游戏界面未正确显示
                 - OCR识别失败
                 - 截图区域无有效数字内容
                 
        Raises:
            Exception: 当操作过程中发生错误时，会捕获异常并打印错误信息
            
        Example:
            >>> delta = DeltaForceClass()
            >>> balance = delta.get_balance()
            >>> if balance is not None:
            ...     print(f"当前余额: {balance}")
            ... else:
            ...     print("余额识别失败")
        """
        # 验证窗口聚焦状态
        if not self.verify_window_focus():
            error_msg = f"❌ [get_balance] 窗口验证失败，拒绝执行余额识别"
            print(error_msg)
            if self.log_callback:
                self.log_callback(error_msg)
            return None
        
        try:
            # 步骤1: 点击余额按钮位置，触发余额显示界面
            time.sleep(0.2)  # 预等待，确保界面稳定
            self.click_ratio(m3_ratio[0], m3_ratio[1])
            time.sleep(0.3)  # 等待游戏界面响应，确保余额信息完全加载
            
            # 步骤2: 将比例坐标转换为屏幕绝对坐标
            m4_screen = self.ratio_to_screen_coords(m4_ratio[0], m4_ratio[1])  # 截图区域左上角
            m5_screen = self.ratio_to_screen_coords(m5_ratio[0], m5_ratio[1])  # 截图区域右下角
            
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
            
            # 步骤6: 处理OCR识别结果并提取余额数值
            if results:
                # 合并所有识别到的数字文本片段
                combined_text = ""
                for (bbox, text, confidence) in results:
                    # 过滤非数字字符，只保留数字
                    filtered_text = ''.join(char for char in text if char.isdigit())
                    combined_text += filtered_text
                
                # 将合并后的数字字符串转换为整数
                if combined_text:
                    balance = int(combined_text)
                    # print(f"成功识别账户余额: {balance}")  # 调试用输出
                    return balance
                else:
                    # print("余额识别失败：OCR结果中未找到有效数字")
                    return None
            else:
                # print("余额识别失败：OCR未返回任何识别结果")
                return None
                
        except Exception as e:
            # 捕获并处理所有可能的异常情况
            print(f"余额识别过程中发生错误: {e}")
            return None

    def get_bar_price(self):
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
        try:
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
                    return combined_text
                else:
                    # print("价格条识别失败：未识别到有效数字")
                    return None
            else:
                # print("价格条识别失败：OCR无结果")
                return None
                
        except Exception as e:
            print(f"价格条识别过程中发生错误: {e}")
            return None

    def get_sell_price(self):
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
        try:
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
                    return combined_text
                else:
                    # print("出售价格识别失败：未识别到有效数字")
                    return None
            else:
                # print("出售价格识别失败：OCR无结果")
                return None
                
        except Exception as e:
            print(f"出售价格识别过程中发生错误: {e}")
            return None

    def get_ammo_price(self, ammo_position):
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
        # 验证窗口聚焦状态
        if not self.verify_window_focus():
            error_msg = f"❌ [get_ammo_price] 窗口验证失败，拒绝执行价格识别"
            print(error_msg)
            if self.log_callback:
                self.log_callback(error_msg)
            return None
        
        return self._get_ammo_price_internal(ammo_position)
    
    def _get_ammo_price_internal(self, ammo_position):
        """
        获取配装界面子弹价格的内部实现（跳过窗口验证）
        """
        try:
            # 检查是否传入了必需的参数
            if ammo_position is None:
                raise ValueError("必须传入ammo_position参数，无默认值")
            
            # 根据子弹位置确定识别区域的比例坐标
            # 区域大小：宽度0.0377，高度0.0191 (基于1号位置计算)
            width = 0.0377
            height = 0.0191
            
            if ammo_position == 1:
                # 第1个位置的子弹价格区域坐标
                bottom_right_ratio = (0.7577, 0.3464)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 2:
                # 第2个位置的子弹价格区域坐标
                bottom_right_ratio = (0.9333, 0.3464)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 3:
                # 第3个位置的子弹价格区域坐标
                bottom_right_ratio = (0.7577, 0.4435)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 4:
                # 第4个位置的子弹价格区域坐标
                bottom_right_ratio = (0.9333, 0.4435)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 5:
                # 第5个位置的子弹价格区域坐标
                bottom_right_ratio = (0.7577, 0.5428)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            elif ammo_position == 6:
                # 第6个位置的子弹价格区域坐标
                bottom_right_ratio = (0.9333, 0.5428)
                top_left_ratio = (bottom_right_ratio[0] - width, bottom_right_ratio[1] - height)
            else:
                # 不支持的位置参数
                raise ValueError(f"不支持的子弹位置: {ammo_position}，当前支持位置: 1, 2, 3, 4, 5, 6")
            
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
                    print(f"成功识别第{ammo_position}个位置子弹价格: {combined_text}")
                    return combined_text
                else:
                    # print(f"第{ammo_position}个位置子弹价格识别失败：未识别到有效数字")
                    return None
            else:
                # print(f"第{ammo_position}个位置子弹价格识别失败：OCR无结果")
                return None
                
        except ValueError as ve:
            # 参数错误
            print(f"参数错误: {ve}")
            return None
        except Exception as e:
            print(f"第{ammo_position}个位置子弹价格识别过程中发生错误: {e}")
            return None

    def click_ammo(self):
        """
        在战备界面点击子弹
        
        该方法在战备界面中点击子弹按钮，用于进入子弹配装界面。
        使用固定的比例坐标进行点击操作。
        
        Returns:
            bool: 点击成功返回True，失败返回False
            
        Example:
            >>> delta = DeltaForceClass()
            >>> if delta.click_ammo():
            ...     print("成功点击子弹按钮")
            ... else:
            ...     print("点击子弹按钮失败")
        """
        # 验证窗口聚焦状态
        if not self.verify_window_focus():
            error_msg = f"❌ [click_ammo] 窗口验证失败，拒绝执行子弹点击"
            print(error_msg)
            if self.log_callback:
                self.log_callback(error_msg)
            return False
        
        # 直接使用click_ratio方法点击子弹按钮
        return self.click_ratio(0.8400, 0.7000)

    def click_ratio(self, x_ratio, y_ratio, do_after=0.0, do_wait=0.0):
        """
        根据比例坐标进行点击的封装方法
        
        该方法提供了一个统一的接口来处理基于比例坐标的点击操作。
        自动将比例坐标转换为屏幕坐标，然后执行点击操作。
        
        Args:
            x_ratio (float): X轴比例坐标，范围0.0-1.0
            y_ratio (float): Y轴比例坐标，范围0.0-1.0
            do_after (float): 点击前等待时间，默认0.0秒（立即点击）
            do_wait (float): 点击后等待时间，默认0.3秒
        
        Returns:
            bool: 点击成功返回True，失败返回False
            
        Example:
            >>> delta = DeltaForceClass()
            >>> # 立即点击屏幕中心位置
            >>> delta.click_ratio(0.5, 0.5)
            >>> # 等待1秒后点击右上角，点击后等待2秒
            >>> delta.click_ratio(0.9, 0.1, do_after=1.0, do_wait=2.0)
        """
        # 验证窗口聚焦状态
        if not self.verify_window_focus():
            error_msg = f"❌ [click_ratio] 窗口验证失败，拒绝执行点击操作 ({x_ratio}, {y_ratio})"
            print(error_msg)
            if self.log_callback:
                self.log_callback(error_msg)
            return False
        
        return self._click_ratio_internal(x_ratio, y_ratio, do_after, do_wait)
    
    def _click_ratio_internal(self, x_ratio, y_ratio, do_after=0.0, do_wait=0.0):
        """
        根据比例坐标进行点击的内部实现（跳过窗口验证）
        """
        try:
            # 验证坐标范围
            if not (0.0 <= x_ratio <= 1.0 and 0.0 <= y_ratio <= 1.0):
                print(f"坐标超出范围: x_ratio={x_ratio}, y_ratio={y_ratio}")
                return False
            
            # 点击前等待
            if do_after > 0:
                time.sleep(do_after)
            
            # 将比例坐标转换为屏幕坐标
            screen_coords = self.ratio_to_screen_coords(x_ratio, y_ratio)
            
            # 执行点击操作
            pyautogui.moveTo(screen_coords[0], screen_coords[1])
            pyautogui.click(screen_coords[0], screen_coords[1])
            
            # 点击后等待
            if do_wait > 0:
                time.sleep(do_wait)
            
            print(f"成功点击比例坐标 ({x_ratio}, {y_ratio}) -> 屏幕坐标 {screen_coords}")
            return True
            
        except Exception as e:
            print(f"点击操作失败: {e}")
            return False

    def goto(self, action):
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
            return self.click_ratio(0.8066, 0.0866)
             
        elif action == "开始游戏":
            # 点击开始游戏按钮
            return self.click_ratio(0.1057, 0.0866)
            
        elif action == "交易行":
            # 点击交易行按钮
            return self.click_ratio(0.3727, 0.0866)
            
        elif action == "仓库":
            # 点击仓库按钮
            return self.click_ratio(0.1718, 0.0866)
            
        elif action == "出售":
            # 出售操作：先点击交易行，延迟1秒后点击出售位置
            # 第一步：点击交易行
            if not self.click_ratio(0.3727, 0.0866):
                return False
            # 第二步：延迟1秒后点击出售位置
            return self.click_ratio(0.1760, 0.1362, do_after=1.0)
            
        else:
            # 不支持的操作类型
            print(f"不支持的操作类型: {action}")
            return False
    
    def get_buy_price(self):
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
                return price
            else:
                return None
                
        except Exception as e:
            print(f"获取购买价格失败: {e}")
            return None
    
    def bind_to_window(self, hwnd):
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
            return True
            
        except Exception as e:
            print(f"❌ 绑定窗口 {hwnd} 失败: {e}")
            return False
    
    def set_log_callback(self, callback):
        """
        设置日志回调函数，用于将验证失败信息传递给GUI
        
        Args:
            callback: 回调函数，接受一个字符串参数（日志消息）
        """
        self.log_callback = callback
    
    def focus_window(self):
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
            
            print(f"✅ 已聚焦窗口: {self.target_window_handle}")
            return True
            
        except Exception as e:
            print(f"❌ 聚焦窗口失败: {e}")
            return False
    
    def get_foreground_window_handle(self):
        """
        获取当前前台窗口的句柄
        
        Returns:
            int: 前台窗口句柄，失败返回None
        """
        try:
            import ctypes
            return ctypes.windll.user32.GetForegroundWindow()
        except Exception as e:
            print(f"❌ 获取前台窗口句柄失败: {e}")
            return None
    
    def verify_window_focus(self, loop=False):
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
        
        if loop:
            print(f"🔍 [窗口验证] 开始循环验证窗口聚焦状态 (目标窗口: {self.target_window_handle})")
        else:
            print(f"🔍 [窗口验证] 开始验证窗口聚焦状态 (目标窗口: {self.target_window_handle})")
        
        retry_count = 0
        max_retries = 1 if not loop else float('inf')  # 非循环模式只尝试1次
        
        while retry_count < max_retries:
            retry_count += 1
            
            if loop and retry_count > 1:
                print(f"🔄 [窗口验证] 第 {retry_count} 次重试...")
            
            # 1. 尝试聚焦到目标窗口
            focus_success = self.focus_window()
            if not focus_success:
                if loop:
                    print(f"⚠️ [窗口验证] 第 {retry_count} 次聚焦操作失败，等待后重试...")
                    time.sleep(0.5)  # 等待0.5秒后重试
                    continue
                else:
                    print(f"❌ [窗口验证] 聚焦操作失败")
                    return False
            
            # 2. 短暂等待聚焦生效
            time.sleep(0.1)
            
            # 3. 检测当前前台窗口
            current_foreground = self.get_foreground_window_handle()
            if current_foreground is None:
                if loop:
                    print(f"⚠️ [窗口验证] 第 {retry_count} 次无法获取前台窗口句柄，等待后重试...")
                    time.sleep(0.5)
                    continue
                else:
                    print(f"❌ [窗口验证] 无法获取当前前台窗口句柄")
                    return False
            
            # 4. 验证是否为目标窗口
            if current_foreground == self.target_window_handle:
                if loop and retry_count > 1:
                    success_msg = f"✅ [窗口验证] 循环验证成功! 第 {retry_count} 次尝试成功 (当前前台: {current_foreground})"
                    print(success_msg)
                    if self.log_callback:
                        self.log_callback(success_msg)
                else:
                    print(f"✅ [窗口验证] 窗口聚焦验证成功 (当前前台: {current_foreground})")
                return True
            else:
                if loop:
                    print(f"⚠️ [窗口验证] 第 {retry_count} 次验证失败 - 目标: {self.target_window_handle}, 实际: {current_foreground}")
                    time.sleep(0.5)  # 等待0.5秒后重试
                    continue
                else:
                    error_msg = f"❌ [窗口验证] 窗口聚焦验证失败! 目标窗口: {self.target_window_handle}, 实际前台: {current_foreground}"
                    print(error_msg)
                    print(f"   建议: 检查窗口是否被其他程序覆盖或最小化")
                    
                    # 如果设置了日志回调，将失败信息发送到GUI
                    if self.log_callback:
                        self.log_callback(error_msg)
                    
                    return False
        
        # 这里不应该到达，但为了安全起见
        return False
    
    def verify_window_focus_loop(self):
        """
        循环验证窗口聚焦状态 - 持续重试直到成功
        
        这是 verify_window_focus(loop=True) 的便捷方法，
        专门用于需要确保窗口聚焦成功的场景。
        
        Returns:
            bool: 总是返回True（会持续重试直到成功）
        """
        return self.verify_window_focus(loop=True)
    
    # 为自定义行为创建专门的验证方法
    def get_ammo_price_with_loop(self, ammo_position):
        """
        获取配装界面子弹价格 - 循环验证版本
        专门用于自定义子弹行为，会持续重试窗口验证直到成功
        """
        # 循环验证窗口聚焦状态
        if not self.verify_window_focus(loop=True):
            # 理论上不会到达这里，因为loop=True会持续重试
            return None
        
        # 调用原始方法，但跳过验证（因为已经验证过了）
        return self._get_ammo_price_internal(ammo_position)
    
    def click_ratio_with_loop(self, x_ratio, y_ratio, do_after=0.0, do_wait=0.0):
        """
        根据比例坐标进行点击 - 循环验证版本
        专门用于自定义子弹行为，会持续重试窗口验证直到成功
        """
        # 循环验证窗口聚焦状态
        if not self.verify_window_focus(loop=True):
            # 理论上不会到达这里，因为loop=True会持续重试
            return False
        
        # 调用原始方法，但跳过验证（因为已经验证过了）
        return self._click_ratio_internal(x_ratio, y_ratio, do_after, do_wait)
    
    def click_ammo_with_loop(self):
        """
        在战备界面点击子弹 - 循环验证版本
        专门用于自定义子弹行为，会持续重试窗口验证直到成功
        """
        # 循环验证窗口聚焦状态
        if not self.verify_window_focus(loop=True):
            # 理论上不会到达这里，因为loop=True会持续重试
            return False
        
        # 直接使用click_ratio方法点击子弹按钮（跳过验证）
        return self._click_ratio_internal(0.8400, 0.7000)

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
    
