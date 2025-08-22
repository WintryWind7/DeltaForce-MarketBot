import time
import datetime
from behavior import behavior
from recognition.ClassRecognition import recognition
from log import log
from safe_mode import start_safe_mode

class Bot(object):

    def __init__(self):
        start_safe_mode()
        log.write('初始化BOT', level='info')

    def auto_buy_ammo_by_low_price(self):
        """
        夜晚低价购买子弹程序
        需要手动切换至购买子弹界面
        """
        def reset():
            for i in range(5):
                behavior.press_esc()
            time.sleep(0.2)
            for i in range(3):
                behavior.goto_above_market()
            time.sleep(0.2)
            if recognition.get_buy_price():
                behavior.press_esc()
            elif recognition.get_record_price():
                behavior.goto_current_market()
            log.write('调和', level='warning')

        reset()
        while True:
            # 点进子弹页面
            behavior.move_mouse(1329, 218)
            behavior.press_left()
            price1 = recognition.get_buy_price()
            if price1:
                behavior.buy()
                behavior.press_esc()
                behavior.goto_record()
                price2 = recognition.get_record_price(save_image=True)
                if price2 and price2>200:
                    log.write(f'当前购买价格：{price2}', level='info')
                    if price2 <=690:
                        behavior.goto_current_market()
                        behavior.move_mouse(1329, 218)
                        behavior.press_left()

                        behavior.max_prebuy()
                        for i in range(7):
                            behavior.buy()

                        log.write(f'尝试买入 页面价格{price1} 实际价格{price2}', level='buy')
                        behavior.press_esc()
                        behavior.goto_record()
                    time.sleep(9)
                    behavior.goto_current_market()
                else:
                    reset()
            else:
                reset()
            time.sleep(1)


    def auto_buy_ammo_by_low_price_on_time(self, start_time:tuple[int, int], end_time:tuple[int, int], freq=5):
        """
        夜晚低价购买子弹程序
        需要手动切换至购买子弹界面
        """
        start_time = datetime.time(start_time[0], start_time[1])  # 每天9:00开始
        end_time = datetime.time(end_time[0], end_time[1])  # 每天17:00结束


        def reset():
            for i in range(5):
                behavior.press_esc()
            time.sleep(0.2)
            for i in range(3):
                behavior.goto_above_market()
            time.sleep(0.2)
            if recognition.get_buy_price():
                behavior.press_esc()
            elif recognition.get_record_price():
                behavior.goto_current_market()
            log.write('调和', level='warning')

        reset()
        while True:
            # 获取当前时间
            now = datetime.datetime.now().time()

            # 检查当前时间是否在指定范围内
            if start_time <= now <= end_time:
                # 点进子弹页面
                behavior.move_mouse(1329, 218)
                behavior.press_left()
                price1 = recognition.get_buy_price()
                if price1:
                    behavior.buy()
                    behavior.press_esc()
                    behavior.goto_record()
                    price2 = recognition.get_record_price(save_image=True)
                    if price2 and price2>200:
                        log.write(f'当前购买价格：{price2}', level='info')
                        if price2 <=550:
                            behavior.goto_current_market()
                            behavior.move_mouse(1329, 218)
                            behavior.press_left()

                            behavior.max_prebuy()
                            for i in range(8):
                                behavior.buy()

                            log.write(f'尝试买入 页面价格{price1} 实际价格{price2}', level='buy')
                            behavior.press_esc()
                            behavior.goto_record()
                        if freq > 1:
                            time.sleep(freq-1)
                        behavior.goto_current_market()
                    else:
                        reset()
                else:
                    reset()
                time.sleep(1)
            else:
                if now > end_time:
                    break
                time.sleep(60)
                log.write(f'不在指定时间内。', level='badtime')

    def auto_sell_ammo(self):
        def reset():
            behavior.goto_above_market()
            time.sleep(0.2)
            behavior.goto_sell_market()
            time.sleep(0.1)
            behavior.move_mouse(1000, 220)
            behavior.press_left()
        while True:
            behavior.goto_sell_market()
            behavior.move_mouse(1060, 300)
            behavior.press_left()
            time.sleep(1)
            price = recognition.get_sell_price()
            if price:
                while price <= 752:
                    behavior.move_mouse(1245, 550)
                    behavior.press_left()
                behavior.move_mouse(1090, 633)
                behavior.press_left()
                time.sleep(0.3)
                behavior.move_mouse(1000, 810)
                behavior.press_left()
                time.sleep(0.3)
                behavior.move_mouse(1456, 810)
                behavior.press_left()
                time.sleep(0.3)
            else:
                reset()




    def reset_market(self):
        if recognition.get_buy_price():
            behavior.press_esc()
        time.sleep(0.5)
        behavior.goto_other()
        behavior.goto_above_market()
        behavior.goto_above_market()
        time.sleep(0.3)
        behavior.reset_market()


if __name__ == "__main__":
    bot = Bot()
    bot.auto_buy_ammo_by_low_price_on_time((0, 1), (2, 1), freq=3)
    bot.auto_buy_ammo_by_low_price_on_time((2, 1), (3, 1), freq=5)
    bot.auto_buy_ammo_by_low_price_on_time((4, 59), (5, 15), freq=1)
    bot.auto_buy_ammo_by_low_price_on_time((6, 50), (7, 0))
    # bot.auto_sell_ammo()