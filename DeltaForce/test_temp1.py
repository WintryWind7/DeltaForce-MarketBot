from DeltaForceClass import DeltaForceClass
delta = DeltaForceClass()
# print(delta.recognize((0.8158, 0.2746), (0.8844, 0.2940), save=True, allow_list="0123456789")) 

 # 获取总价
max_buy_number = (45+5+24)*60

low_price = 540
# current_full_price = int(delta.recognize((0.8225, 0.7962), (0.9300, 0.8200), allow_list="0123456789"))
# current_price = int(current_full_price/max_buy_number)
# ready_full_price = low_price*max_buy_number
# print(current_price)
# print(f"实际价格:{current_price}，预期价格:{low_price}")

# m1 = (0.1500,0.9600)
# m2 = (0.1000,0.4900)

if __name__ == "__main__":
    import pyautogui
    import time
    import keyboard
    
    # 鼠标点击坐标（比例坐标）
    m1 = (0.1050, 0.6300)
    m2 = (0.1000, 0.4900)
    
    print("开始自动交易循环...")
    print(f"预期价格: {low_price}")
    
    # 设置退出标志
    exit_flag = False
    
    def on_q_press(e):
        global exit_flag
        if e.name == 'q':
            exit_flag = True
            print("检测到q键按下，准备退出循环...")
    
    # 注册键盘监听
    keyboard.on_press(on_q_press)
    
    print("按q键可以随时退出循环")
    
    while True:
        try:
            # 检查是否按下q键退出
            if exit_flag:
                print("用户选择退出循环")
                break
                
            # 点击m1
            m1_screen = delta.ratio_to_screen_coords(m1[0], m1[1])
            pyautogui.click(m1_screen[0], m1_screen[1])
            time.sleep(0.1)
            
            # 点击m2
            m2_screen = delta.ratio_to_screen_coords(m2[0], m2[1])
            pyautogui.click(m2_screen[0], m2_screen[1])
            time.sleep(0.1)
            
            # 获取当前价格
            current_full_price = int(delta.recognize((0.8225, 0.7962), (0.9300, 0.8200), allow_list="0123456789"))
            current_price = int(current_full_price/max_buy_number)
            
            print(f"当前价格: {current_price}")
            
            # 如果实际价格低于预期，则停止
            if current_price < low_price:
                print(f"价格达到目标！当前价格: {current_price} < 预期价格: {low_price}")
                break
            else:
                print(f"价格未达目标，继续循环... 当前价格: {current_price} >= 预期价格: {low_price}")
                
        except Exception as e:
            print(f"循环中出错: {e}")
            time.sleep(1)
            continue
    
    print("自动交易完成！")
    
    # 清理键盘监听器
    keyboard.unhook_all()
