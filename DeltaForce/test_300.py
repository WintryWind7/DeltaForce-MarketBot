from DeltaForceClass import DeltaForceClass
import os
import easyocr
import numpy as np

# 初始化DeltaForce实例
delta = DeltaForceClass()

# 初始化中文OCR识别器
chinese_reader = easyocr.Reader(['ch_sim'])

# 配置参数
max_buy_number = 25*60
low_price = 1600      # 目标价格上限 1600
min_price = 900      # 价格下限保护，防止识别错误 1100

# 创建image文件夹
image_folder = "image"
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

def generate_grid_coords():
    """生成9x9网格的中心坐标"""
    left_x = 0.6600
    top_y = 0.2302
    right_x = 0.9234
    bottom_y = 0.6779
    
    grid_width = (right_x - left_x) / 8
    grid_height = (bottom_y - top_y) / 8
    
    grid_coords = []
    for row in range(9):
        for col in range(9):
            x = left_x + col * grid_width
            y = top_y + row * grid_height
            grid_coords.append((x, y))
    
    return grid_coords

def check_waiting_status():
    """检查指定区域是否显示长度为4的文本"""
    try:
        top_left_ratio = (0.2497, 0.2524)
        bottom_right_ratio = (0.2917, 0.2724)
        
        screen_left, screen_top = delta.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = delta.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
        screenshot_array = np.array(screenshot)
        
        results = chinese_reader.readtext(screenshot_array)
        
        for (bbox, text, confidence) in results:
            if len(text) == 4:
                return True
        
        return False
        
    except Exception as e:
        return False

if __name__ == "__main__":
    import pyautogui
    import time
    import keyboard
    
    # 鼠标点击坐标（比例坐标）
    m1 = (0.1000, 0.4900)
    m2 = (0.8727, 0.7888)
    
    # 检查账户余额
    print("正在检查账户余额...")
    initial_balance = delta.get_balance()
    time.sleep(0.5)
    if initial_balance is not None:
        print(f"初始余额: {initial_balance}")
    else:
        print("余额获取失败，继续运行程序")
    
    print(f"程序启动 - 目标价格: {min_price}-{low_price} (按q键退出)")
    
    # 设置退出标志
    exit_flag = False
    
    def on_q_press(e):
        global exit_flag
        if e.name == 'q':
            exit_flag = True
            print("程序退出")
    
    # 注册键盘监听
    keyboard.on_press(on_q_press)
    
    def main_process():
        """主要处理流程"""
        try:
            # 按下L键
            pyautogui.press('l')
            time.sleep(0.04)
            
            # 点击m1位置
            m1_screen = delta.ratio_to_screen_coords(m1[0], m1[1])
            pyautogui.click(m1_screen[0], m1_screen[1])
            time.sleep(0.08)
            
            # 识别价格区域并获取图片（使用与test_recognize.py相同的方法）
            # 获取屏幕坐标
            screen_left, screen_top = delta.ratio_to_screen_coords(0.8225, 0.7962)
            screen_right, screen_bottom = delta.ratio_to_screen_coords(0.9300, 0.8200)
            
            # 获取预处理后的图像
            processed_image = delta.ocr._preprocess_image(
                delta.ocr._screenshot((screen_left, screen_top), (screen_right, screen_bottom)), 
                "peizhuang"
            )
            
            # 使用正确的EasyOCR参数（与test_recognize.py保持一致）
            raw_results = delta.ocr.reader.readtext(processed_image, allowlist='1234567890', width_ths=0.7, height_ths=0.7, decoder='beamsearch', text_threshold=0.5)
            
            # 合并文本
            combined_text = "".join(text for _, text, _ in raw_results)
            
            # 保存调试图片
            from PIL import Image
            processed_pil = Image.fromarray(processed_image)
            debug_filename = f"debug_{combined_text if combined_text else 'empty'}.jpg"
            debug_filepath = os.path.join(image_folder, debug_filename)
            processed_pil.save(debug_filepath, "JPEG", quality=95)
            
            if combined_text:  # 如果识别成功
                recognized_text = combined_text
                current_full_price = int(recognized_text)
                current_price = int(current_full_price / max_buy_number)
                
                # 保存识别图片到image文件夹，以识别结果命名（只有数字）
                filename = f"{current_full_price}.jpg"
                filepath = os.path.join(image_folder, filename)
                
                # 保存图片到image文件夹
                processed_pil.save(filepath, "JPEG", quality=95)
                
                # 判断是否满足条件（必须在价格区间内）
                if min_price <= current_price <= low_price:
                    print(f"✓ 条件满足！总价={current_full_price}, 单价={current_price} (预设区间: {min_price}-{low_price})")
                    # 二次确认识别
                    
                    # 获取二次确认的预处理图像
                    confirm_processed_image = delta.ocr._preprocess_image(
                        delta.ocr._screenshot((screen_left, screen_top), (screen_right, screen_bottom)), 
                        "peizhuang"
                    )
                    
                    # 使用相同的EasyOCR参数
                    confirm_raw_results = delta.ocr.reader.readtext(confirm_processed_image, allowlist='1234567890', width_ths=0.7, height_ths=0.7, decoder='beamsearch', text_threshold=0.5)
                    
                    # 合并文本
                    confirm_combined_text = "".join(text for _, text, _ in confirm_raw_results)
                    
                    if confirm_combined_text:  # 如果二次识别成功
                        confirm_text = confirm_combined_text
                        confirm_full_price = int(confirm_text)
                        confirm_price = int(confirm_full_price / max_buy_number)
                        
                        
                        if min_price <= confirm_price <= low_price:
                            print(f"✓ 二次确认通过！总价={confirm_full_price}, 单价={confirm_price} (预设区间: {min_price}-{low_price})")
                            # 点击m2
                            m2_screen = delta.ratio_to_screen_coords(m2[0], m2[1])
                            pyautogui.moveTo(m2_screen[0], m2_screen[1])
                            for i in range(5):
                                pyautogui.click(m2_screen[0], m2_screen[1])
                                time.sleep(0.2)
                            time.sleep(3)
                            for i in range(2):
                                delta.goto("仓库")
                                time.sleep(1)
                                pyautogui.press('esc')
                                time.sleep(1)
                            return "purchase_success"  # 返回购买成功标识
                        else:
                            if confirm_price < min_price:
                                print(f"✗ 二次确认失败：总价={confirm_full_price}, 单价={confirm_price} < 最低价格: {min_price}")
                            else:
                                print(f"✗ 二次确认失败：总价={confirm_full_price}, 单价={confirm_price} > 目标价格: {low_price}")
                            pyautogui.press('esc')
                            time.sleep(0.05)
                            return False
                    else:
                        # 二次识别失败，按ESC继续
                        pyautogui.press('esc')
                        time.sleep(0.05)
                        return False
                else:
                    if current_price < min_price:
                        print(f"✗ 价格异常：总价={current_full_price}, 单价={current_price} < 最低价格: {min_price}")
                    else:
                        print(f"✗ 条件不满足：总价={current_full_price}, 单价={current_price} > 目标价格: {low_price}")
                    pyautogui.press('esc')
                    time.sleep(0.05)
                    return False  # 不满足条件，继续循环
            else:
                # 识别失败
                pyautogui.press('esc')
                time.sleep(0.05)
                return False
                
        except Exception as e:
            # 异常处理
            pyautogui.press('esc')
            time.sleep(0.05)
            return False
    
    # 主循环
    while True:
        try:
            # 检查是否按下q键退出
            if exit_flag:
                break
            
            # 执行主要处理流程
            result = main_process()
            if result == "purchase_success":
                # 购买成功后检查余额变化
                print("购买完成，检查余额变化...")
                time.sleep(1)  # 等待余额更新
                current_balance = delta.get_balance()
                time.sleep(0.5)
                
                if current_balance is not None and initial_balance is not None:
                    balance_change = initial_balance - current_balance
                    if balance_change > 0:
                        print(f"✓ 余额已变化！初始: {initial_balance} → 当前: {current_balance} (消费: {balance_change})")
                        print("购买成功，开始执行后续操作...")
                        
                        # 购买成功后的自动化流程
                        try:
                            # 检查退出标志
                            if exit_flag:
                                break
                                
                            # 1. 点击仓库
                            print("步骤1: 点击仓库")
                            if delta.goto("仓库"):
                                print("✓ 成功点击仓库")
                                
                                # 2. 延迟1秒
                                print("步骤2: 延迟1秒")
                                time.sleep(2)
                                
                                # 3. 按下Ctrl+F
                                print("步骤3: 按下Ctrl+F")
                                delta.click_ratio(0.1576,0.9609)
                                
                                # 4. 延迟1秒
                                print("步骤4: 延迟1秒")
                                time.sleep(1)
                                
                                # 5. 执行出售操作和网格搜索
                                if delta.goto("出售"):
                                    # 开始网格搜索逻辑（从左上角开始）
                                    grid_coords = generate_grid_coords()
                                    success_count = 0
                                    target_count = 1  # 只需要找到一个物品
                                    
                                    # 从左上角（索引0）开始搜索，只搜索前三行（0-26索引，即前27个位置）
                                    for i in range(min(27, len(grid_coords))):  # 前三行：9*3=27个位置
                                        # 检查退出标志
                                        if exit_flag:
                                            break
                                            
                                        x_ratio, y_ratio = grid_coords[i]
                                        
                                        if delta.click_ratio(x_ratio, y_ratio, do_wait=0.2):
                                            bar_price = delta.get_bar_price()
                                            
                                            if bar_price is not None:
                                                success_count += 1
                                                
                                                # 直接执行第二轮确认操作
                                                delta.click_ratio(0.7546, 0.5343)
                                                time.sleep(0.3)
                                                delta.click_ratio(0.6891, 0.6051)
                                                time.sleep(0.2)
                                                pyautogui.hotkey('ctrl', 'a')
                                                time.sleep(0.2)
                                                
                                                price_value = int(bar_price)
                                                input_price = price_value - 35  # 改为原价-35
                                                pyautogui.typewrite(str(input_price))
                                                time.sleep(0.2)
                                                
                                                delta.click_ratio(0.6823, 0.6990)
                                                time.sleep(2)
                                                
                                                # 等待出售状态确认
                                                print("等待出售状态确认...")
                                                while not check_waiting_status():
                                                    if exit_flag:
                                                        break
                                                    time.sleep(1)
                                                print("✓ 出售状态确认完成")
                                                break
                                        
                                        time.sleep(0.1)
                                    
                                    # 无论成功与否，都进入下一大轮任务
                                    if success_count >= target_count:
                                        print("✓ 出售操作完成")
                                    else:
                                        print("✗ 出售操作未完全完成，网格搜索已完成")
                                else:
                                    print("✗ 出售操作失败")
                            else:
                                print("✗ 点击仓库失败")
                        except Exception as e:
                            print(f"后续操作执行失败: {e}")
                        
                        # 无论操作成功与否，都开始下一大轮任务
                        print("当前轮次完成，开始下一大轮任务...")
                        time.sleep(1)  # 延迟1秒
                        
                        # 预处理操作
                        delta.click_ratio(0.9036, 0.0855)
                        time.sleep(2)
                        delta.click_ratio(0.1082, 0.8782)
                        time.sleep(3)
                        delta.click_ratio(0.1082, 0.8782)
                        time.sleep(1)
                        pyautogui.press('esc')
                        time.sleep(3)
                        
                        # 点击开始游戏
                        if delta.goto("开始游戏"):
                            print("✓ 点击开始游戏")
                            time.sleep(5)
                            print("开始下一大轮任务...")
                        else:
                            print("✗ 点击开始游戏失败")
                        
                        # 不要break，继续主循环
                    else:
                        print(f"✗ 余额未变化：初始: {initial_balance} → 当前: {current_balance}")
                        print("继续执行程序...")
                        # 更新初始余额为当前余额
                        initial_balance = current_balance
                else:
                    print("余额检查失败，继续执行程序...")
            
            # 循环间隔
            time.sleep(0.05)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(1)
    
    # 清理键盘监听器
    keyboard.unhook_all()
