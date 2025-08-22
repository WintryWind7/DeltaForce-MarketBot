import time
from .ClassAuto import Auto


class Behavior(Auto):


    def max_prebuy(self):
        """
        将预备购买量拉满
        """
        self.move_mouse(1450, 715)
        time.sleep(0.15)
        self.press_left()
        time.sleep(0.05)


    def buy(self):
        """执行购买操作"""
        self.move_mouse(1371, 776)
        self.press_left()


    def goto_record(self):
        """交易记录"""
        self.move_mouse(379, 112)
        self.press_left()


    def goto_current_market(self):
        """商品陈列界面"""
        self.move_mouse(168, 112)
        self.press_left()


    def goto_above_market(self):
        """交易行"""
        self.move_mouse(594, 58)
        self.press_left()


    def goto_other(self):
        self.move_mouse(480, 58)
        self.press_left()


    def reset_market(self):
        """重置交易行为基础界面"""
        for i in range(5):
            self.move_mouse(210, 230)
            self.press_left()

    def goto_current_shop(self, pos1, pos2):
        self.move_mouse(200, 230)


    def goto_sell_market(self):
        """前往出售界面"""
        self.move_mouse(270, 112)
        self.press_left()

