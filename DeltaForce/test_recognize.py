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

def debug_recognize(coordinates, preprocess_type="peizhuang"):
    """调试识别函数，只显示置信度信息"""
    try:
        # 获取屏幕坐标
        screen_left, screen_top = delta.ratio_to_screen_coords(coordinates[0][0], coordinates[0][1])
        screen_right, screen_bottom = delta.ratio_to_screen_coords(coordinates[1][0], coordinates[1][1])
        
        # 获取原始EasyOCR结果（含置信度）
        processed_image = delta.ocr._preprocess_image(
            delta.ocr._screenshot((screen_left, screen_top), (screen_right, screen_bottom)), 
            preprocess_type
        )
        
        # 使用正确的EasyOCR参数（与_recognize_text保持一致）
        if preprocess_type == "peizhuang":
            raw_results = delta.ocr.reader.readtext(processed_image, allowlist='1234567890', width_ths=0.7, height_ths=0.7, decoder='beamsearch', text_threshold=0.5)
        else:
            raw_results = delta.ocr.reader.readtext(processed_image, width_ths=0.2, height_ths=0.5, decoder='beamsearch', text_threshold=0.5)
        
        # 显示置信度和字符尺寸信息
        for i, (bbox, text, confidence) in enumerate(raw_results):
            # 计算字符的精确位置和尺寸
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            left = int(min(x_coords))
            right = int(max(x_coords))
            top = int(min(y_coords))
            bottom = int(max(y_coords))
            width = right - left
            height = bottom - top
            
            print(f"[{i+1}] '{text}' 置信度: {confidence:.3f}")
            print(f"     位置: 列{left}-{right} (宽{width}px) 行{top}-{bottom} (高{height}px)")
        
        # 合并文本
        combined_text = "".join(text for _, text, _ in raw_results)
        
        # 保存预处理后的调试图片
        if len(combined_text) > 0:
            from PIL import Image
            processed_pil = Image.fromarray(processed_image)
            debug_filename = f"debug_{combined_text}.jpg"
            debug_filepath = os.path.join(image_folder, debug_filename)
            processed_pil.save(debug_filepath, "JPEG", quality=95)
        
        return True, combined_text, raw_results
            
    except Exception as e:
        print(f"识别出错: {e}")
        return False, "", []

if __name__ == "__main__":
    import pyautogui
    import time
    import keyboard
    
    # 鼠标点击坐标（比例坐标）
    m1 = (0.1000, 0.4900)
    m2 = (0.8800, 0.8100)
    
    print(f"🚀 调试程序启动 - 目标价格: {min_price}-{low_price}")
    print("按q键退出，按s键进行单次调试识别")
    
    # 设置退出标志
    exit_flag = False
    debug_flag = False
    
    def on_key_press(e):
        global exit_flag, debug_flag
        if e.name == 'q':
            exit_flag = True
            print("程序退出")
        elif e.name == 's':
            debug_flag = True
            print("触发调试识别...")
    
    # 注册键盘监听
    keyboard.on_press(on_key_press)
    
    def main_debug_process():
        """主要调试流程 - 直接识别指定区域"""
        try:
            print("\n🔍 开始执行调试识别...")
            
            # 直接识别价格区域
            print("🔍 开始识别价格区域...")
            success, text, raw_results = debug_recognize(
                ((0.8225, 0.7962), (0.9300, 0.8200)), 
                "peizhuang"
            )
            
            if success:
                print(f"识别: '{text}' ({len(text)}位)")
                
                # 二次确认
                time.sleep(0.1)
                confirm_success, confirm_text, confirm_raw = debug_recognize(
                    ((0.8225, 0.7962), (0.9300, 0.8200)), 
                    "peizhuang"
                )
                
                if confirm_success:
                    print(f"确认: '{confirm_text}' ({len(confirm_text)}位)")
                    return True
                else:
                    print("❌ 二次确认失败")
                    return False
            else:
                print("❌ 第一次识别失败")
                return False
                
        except Exception as e:
            print(f"❌ 调试流程出错: {e}")
            return False
    
    # 主循环
    while True:
        try:
            # 检查是否按下q键退出
            if exit_flag:
                break
            
            # 检查是否按下s键进行调试
            if debug_flag:
                debug_flag = False  # 重置标志
                main_debug_process()
                print("\n" + "="*60)
                print("调试完成，按s键继续调试，按q键退出")
                print("="*60)
            
            time.sleep(0.1)  # 避免CPU占用过高
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"主循环出错: {e}")
            time.sleep(1)
    
    # 清理键盘监听器
    keyboard.unhook_all()
    print("调试程序结束")