from DeltaForceClass import DeltaForceClass
import os

# 初始化DeltaForce实例
delta = DeltaForceClass()

# 配置参数
max_buy_number = (45+5+24)*60
low_price = 480      # 目标价格上限
min_price = 200      # 价格下限保护，防止识别错误

# 创建image文件夹
image_folder = "image"
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

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
            time.sleep(0.03)
            
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
                    time.sleep(0.1)
                    
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
                            for i in range(10):
                                pyautogui.click(m2_screen[0], m2_screen[1])
                                time.sleep(0.05)
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
                        print("程序结束")
                        break
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
