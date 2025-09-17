from DeltaForceClass import DeltaForceClass
import time
import pyautogui
import easyocr
import numpy as np

# 初始化DeltaForce实例
delta = DeltaForceClass()

# 初始化中文OCR识别器（使用繁体中文模型）
chinese_reader = easyocr.Reader(['ch_sim'])

def generate_grid_coords():
    """
    生成9x9网格的中心坐标
    
    网格范围：
    - 左上角中心: (6600, 2302)
    - 右下角中心: (9234, 6779)
    - 总共9x9 = 81个网格点
    
    Returns:
        list: 包含81个坐标点的列表，每个坐标为(x, y)元组
    """
    # 定义网格边界（比例坐标，0.xxxx格式）
    left_x = 0.6600
    top_y = 0.2302
    right_x = 0.9234
    bottom_y = 0.6779
    
    # 计算网格间距
    grid_width = (right_x - left_x) / 8  # 9个点需要8个间距
    grid_height = (bottom_y - top_y) / 8  # 9个点需要8个间距
    
    # 生成所有网格点坐标（直接生成比例坐标）
    grid_coords = []
    for row in range(9):
        for col in range(9):
            x = left_x + col * grid_width
            y = top_y + row * grid_height
            grid_coords.append((x, y))
    
    return grid_coords

def check_waiting_status():
    """
    检查指定区域是否显示"等待上架"
    
    Returns:
        bool: 如果识别到"等待上架"返回True，否则返回False
    """
    try:
        # 定义识别区域的比例坐标
        top_left_ratio = (0.2497, 0.2524)
        bottom_right_ratio = (0.2917, 0.2724)
        
        # 转换为屏幕坐标
        screen_left, screen_top = delta.ratio_to_screen_coords(top_left_ratio[0], top_left_ratio[1])
        screen_right, screen_bottom = delta.ratio_to_screen_coords(bottom_right_ratio[0], bottom_right_ratio[1])
        
        # 截图指定区域
        screenshot = pyautogui.screenshot(region=(screen_left, screen_top, screen_right-screen_left, screen_bottom-screen_top))
        screenshot_array = np.array(screenshot)
        
        # 使用中文OCR识别
        results = chinese_reader.readtext(screenshot_array)
        
        # 检查是否有长度为4的文本（简化检测逻辑）
        for (bbox, text, confidence) in results:
            print(f"识别到文本: '{text}' (长度: {len(text)}, 置信度: {confidence:.4f})")
            if len(text) == 4:
                print(f"✓ 识别到长度为4的文本: {text}")
                return True
        
        return False
        
    except Exception as e:
        print(f"状态检查出错: {e}")
        return False

def main():
    """主要执行流程"""
    print("=== 开始执行出售流程 ===")
    
    # 第一步：点击仓库
    print("步骤1: 点击仓库")
    if delta.goto("仓库"):
        print("✓ 成功点击仓库")
        
        # 第二步：延迟2秒
        print("步骤2: 延迟2秒")
        time.sleep(2)
        
        # 第三步：按下Ctrl+F
        print("步骤3: 按下Ctrl+F")
        delta.click_ratio(0.1576,0.9609)
        
        # 第四步：延迟1秒
        print("步骤4: 延迟1秒")
        time.sleep(1)
        
        # 第五步：执行goto出售操作
        print("步骤5: 执行goto出售操作")
        if not delta.goto("出售"):
            print("✗ goto出售操作失败，程序退出")
            return False
        
        print("✓ goto出售操作成功")
        time.sleep(1)  # 等待界面加载
    else:
        print("✗ 点击仓库失败，程序退出")
        return False
    
    # 第六步：生成9x9网格坐标
    print("步骤6: 生成9x9网格坐标")
    grid_coords = generate_grid_coords()
    print(f"✓ 生成了{len(grid_coords)}个网格点")
    
    # 记录点击成功次数和位置
    success_count = 0
    target_count = 2  # 需要确认点击到2次
    first_success_index = -1  # 第一次成功的位置索引
    
    # 第七步：遍历网格点击并检测
    print("步骤7: 开始遍历网格点击")
    
    # 开始遍历的起始位置
    start_index = 0
    
    while success_count < target_count:
        found_in_this_round = False
        
        # 从指定位置开始遍历
        for i in range(start_index, len(grid_coords)):
            x_ratio, y_ratio = grid_coords[i]
            print(f"正在点击第{i+1}/81个网格点: 比例坐标({x_ratio:.4f}, {y_ratio:.4f})")
            
            # 点击网格点
            if delta.click_ratio(x_ratio, y_ratio, do_wait=0.2):
                # 检测是否出现柱形价格图
                bar_price = delta.get_bar_price()
                
                if bar_price is not None:
                    success_count += 1
                    found_in_this_round = True
                    print(f"✓ 第{success_count}次成功点击到目标！在第{i+1}个网格点检测到柱形价格图")
                    print(f"✓ 识别到的价格: {bar_price}")
                    
                    if success_count == 1:
                        # 记录第一次成功的位置
                        first_success_index = i
                        
                        # 第一次识别到bar价格后的操作流程
                        print("开始执行第一次识别后的操作流程...")
                        
                        # 1. 点击第一个位置
                        print("操作1: 点击位置(0.7040, 0.5343)")
                        delta.click_ratio(0.7040, 0.5343)
                        time.sleep(0.3)
                        
                        # 2. 点击第二个位置
                        print("操作2: 点击位置(0.6891, 0.6051)")
                        delta.click_ratio(0.6891, 0.6051)
                        time.sleep(0.2)
                        
                        # 3. 按下Ctrl+A
                        print("操作3: 按下Ctrl+A")
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.2)
                        
                        # 4. 输入数字（bar价格-10）
                        price_value = int(bar_price)
                        input_price = price_value - 10
                        print(f"操作4: 输入数字 {input_price} (原价格 {price_value} - 10)")
                        pyautogui.typewrite(str(input_price))
                        time.sleep(0.2)
                        
                        # 5. 点击确认位置
                        print("操作5: 点击确认位置(0.6823, 0.6990)")
                        delta.click_ratio(0.6823, 0.6990)
                        time.sleep(2)  # 延迟2秒
                        
                        # 6. 等待"等待上架"状态
                        print("操作6: 等待上架状态确认...")
                        while not check_waiting_status():
                            print("等待状态确认中...")
                            time.sleep(1)
                        
                        print("✓ 第一次识别后的操作流程完成，继续寻找第二个目标")
                        # 下一轮搜索从前两格开始，但不会超过初始格(0)
                        start_index = max(0, first_success_index - 2)
                        break
                        
                    elif success_count == 2:
                        # 第二次识别到，使用不同的点击位置
                        print("开始执行第二次识别后的操作流程...")
                        
                        # 1. 点击第一个位置（修改后的坐标）
                        print("操作1: 点击位置(0.7546, 0.5343)")
                        delta.click_ratio(0.7546, 0.5343)
                        time.sleep(0.3)
                        
                        # 2-5. 其余操作相同
                        print("操作2: 点击位置(0.6891, 0.6051)")
                        delta.click_ratio(0.6891, 0.6051)
                        time.sleep(0.2)
                        
                        print("操作3: 按下Ctrl+A")
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.2)
                        
                        price_value = int(bar_price)
                        input_price = price_value - 10
                        print(f"操作4: 输入数字 {input_price} (原价格 {price_value} - 10)")
                        pyautogui.typewrite(str(input_price))
                        time.sleep(0.2)
                        
                        print("操作5: 点击确认位置(0.6823, 0.6990)")
                        delta.click_ratio(0.6823, 0.6990)
                        
                        print(f"✓ 已完成{target_count}次确认点击，程序完成")
                        return True
                else:
                    print(f"第{i+1}个网格点未检测到柱形价格图，继续下一个")
            else:
                print(f"✗ 第{i+1}个网格点点击失败")
            
            # 短暂延迟，避免操作过快
            time.sleep(0.3)
        
        # 如果这一轮没有找到目标，且不是第一次搜索，则重新从头开始
        if not found_in_this_round and start_index > 0:
            print("从第一次成功位置到结尾未找到第二个目标，重新从头开始搜索")
            start_index = 0
        elif not found_in_this_round and start_index == 0:
            # 从头开始也没找到，退出循环
            break

    # 如果遍历完所有网格点
    if success_count > 0:
        print(f"✓ 遍历完成，成功识别到{success_count}次柱形价格图")
        if success_count >= target_count:
            return True
        else:
            print(f"✗ 未达到目标次数{target_count}次")
            return False
    else:
        print("✗ 遍历完所有81个网格点，未找到目标")
        return False

if __name__ == "__main__":
    try:
        print("DeltaForce出售自动化程序启动")
        print("网格范围: 左上角(0.6600, 0.2302) -> 右下角(0.9234, 0.6779)")
        print("网格规模: 9x9 = 81个点")
        print("-" * 50)
        
        success = main()
        
        print("-" * 50)
        if success:
            print("程序执行成功！")
        else:
            print("程序执行失败。")
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
