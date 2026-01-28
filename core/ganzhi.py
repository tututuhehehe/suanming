"""
干支时间计算模块 - 计算年月日时的天干地支
"""
from datetime import datetime
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class GanzhiTime:
    """干支时间"""
    year_gan: str           # 年干
    year_zhi: str           # 年支
    month_gan: str          # 月干
    month_zhi: str          # 月支
    day_gan: str            # 日干
    day_zhi: str            # 日支
    hour_gan: str           # 时干
    hour_zhi: str           # 时支
    
    @property
    def year_ganzhi(self) -> str:
        return f"{self.year_gan}{self.year_zhi}"
    
    @property
    def month_ganzhi(self) -> str:
        return f"{self.month_gan}{self.month_zhi}"
    
    @property
    def day_ganzhi(self) -> str:
        return f"{self.day_gan}{self.day_zhi}"
    
    @property
    def hour_ganzhi(self) -> str:
        return f"{self.hour_gan}{self.hour_zhi}"
    
    def __str__(self) -> str:
        return f"{self.year_ganzhi}年 {self.month_ganzhi}月 {self.day_ganzhi}日 {self.hour_ganzhi}时"


class GanzhiCalculator:
    """干支计算器"""
    
    TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 地支五行
    DIZHI_WUXING = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木",
        "辰": "土", "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土", "亥": "水"
    }
    
    # 天干五行
    TIANGAN_WUXING = {
        "甲": "木", "乙": "木", "丙": "火", "丁": "火",
        "戊": "土", "己": "土", "庚": "金", "辛": "金",
        "壬": "水", "癸": "水"
    }
    
    # 时辰对照 (24小时制的小时 -> 地支索引)
    HOUR_TO_DIZHI = {
        23: 0, 0: 0,    # 子时 23:00-01:00
        1: 1, 2: 1,     # 丑时 01:00-03:00
        3: 2, 4: 2,     # 寅时 03:00-05:00
        5: 3, 6: 3,     # 卯时 05:00-07:00
        7: 4, 8: 4,     # 辰时 07:00-09:00
        9: 5, 10: 5,    # 巳时 09:00-11:00
        11: 6, 12: 6,   # 午时 11:00-13:00
        13: 7, 14: 7,   # 未时 13:00-15:00
        15: 8, 16: 8,   # 申时 15:00-17:00
        17: 9, 18: 9,   # 酉时 17:00-19:00
        19: 10, 20: 10, # 戌时 19:00-21:00
        21: 11, 22: 11  # 亥时 21:00-23:00
    }
    
    # 节气日期（简化版，每月两个节气的大致日期）
    # 格式: (月份, 日期, 是否为节)  节为月首，气为月中
    JIEQI = [
        (1, 6, True, "小寒"),   (1, 20, False, "大寒"),
        (2, 4, True, "立春"),   (2, 19, False, "雨水"),
        (3, 6, True, "惊蛰"),   (3, 21, False, "春分"),
        (4, 5, True, "清明"),   (4, 20, False, "谷雨"),
        (5, 6, True, "立夏"),   (5, 21, False, "小满"),
        (6, 6, True, "芒种"),   (6, 21, False, "夏至"),
        (7, 7, True, "小暑"),   (7, 23, False, "大暑"),
        (8, 7, True, "立秋"),   (8, 23, False, "处暑"),
        (9, 8, True, "白露"),   (9, 23, False, "秋分"),
        (10, 8, True, "寒露"),  (10, 23, False, "霜降"),
        (11, 7, True, "立冬"),  (11, 22, False, "小雪"),
        (12, 7, True, "大雪"),  (12, 22, False, "冬至")
    ]
    
    def __init__(self):
        pass
    
    def calc_year_ganzhi(self, year: int) -> Tuple[str, str]:
        """
        计算年干支
        以立春为年界
        """
        # 公元元年是辛酉年，以此为基准计算
        # 天干: (year - 4) % 10
        # 地支: (year - 4) % 12
        gan_index = (year - 4) % 10
        zhi_index = (year - 4) % 12
        return self.TIANGAN[gan_index], self.DIZHI[zhi_index]
    
    def calc_month_ganzhi(self, year: int, month: int, day: int) -> Tuple[str, str]:
        """
        计算月干支
        以节气为月界
        """
        # 先确定农历月（以节气为界）
        lunar_month = self._get_lunar_month(month, day)
        
        # 月支固定: 正月建寅(索引2), 二月建卯(索引3)...
        zhi_index = (lunar_month + 1) % 12  # 正月=1, 寅=2, 所以 (1+1)%12=2
        
        # 月干由年干推算（五虎遁）
        year_gan, _ = self.calc_year_ganzhi(year)
        year_gan_index = self.TIANGAN.index(year_gan)
        
        # 五虎遁口诀：
        # 甲己之年丙作首（正月为丙寅）
        # 乙庚之年戊为头（正月为戊寅）
        # 丙辛之岁寻庚上（正月为庚寅）
        # 丁壬壬寅顺水流（正月为壬寅）
        # 戊癸之年甲寅头（正月为甲寅）
        base_gan = [2, 4, 6, 8, 0]  # 丙、戊、庚、壬、甲的索引
        first_month_gan = base_gan[year_gan_index % 5]
        gan_index = (first_month_gan + lunar_month - 1) % 10
        
        return self.TIANGAN[gan_index], self.DIZHI[zhi_index]
    
    def _get_lunar_month(self, month: int, day: int) -> int:
        """
        根据公历日期获取农历月份（以节气为界）
        返回1-12
        """
        # 找到当前所在的节气月
        for i, (jie_month, jie_day, is_jie, _) in enumerate(self.JIEQI):
            if is_jie:  # 只看"节"，不看"气"
                if month == jie_month:
                    if day < jie_day:
                        # 还在上个月
                        return ((i // 2) % 12) or 12
                    else:
                        # 已经进入本月
                        return ((i // 2 + 1) % 12) or 12
                elif month < jie_month:
                    return ((i // 2) % 12) or 12
        
        # 默认返回当前月
        return month
    
    def calc_day_ganzhi(self, year: int, month: int, day: int) -> Tuple[str, str]:
        """
        计算日干支
        使用蔡勒公式的变体
        """
        # 以2000年1月1日（甲辰日）为基准
        # 计算从基准日到目标日的天数
        from datetime import date
        base_date = date(2000, 1, 1)
        target_date = date(year, month, day)
        
        days_diff = (target_date - base_date).days
        
        # 2000年1月1日是甲辰日 (甲=0, 辰=4)
        base_gan = 0   # 甲
        base_zhi = 4   # 辰
        
        gan_index = (base_gan + days_diff) % 10
        zhi_index = (base_zhi + days_diff) % 12
        
        return self.TIANGAN[gan_index], self.DIZHI[zhi_index]
    
    def calc_hour_ganzhi(self, year: int, month: int, day: int, hour: int) -> Tuple[str, str]:
        """
        计算时干支
        """
        # 获取时支
        zhi_index = self.HOUR_TO_DIZHI.get(hour, 0)
        
        # 获取日干
        day_gan, _ = self.calc_day_ganzhi(year, month, day)
        day_gan_index = self.TIANGAN.index(day_gan)
        
        # 五鼠遁（由日干推时干）
        # 甲己日起甲子时
        # 乙庚日起丙子时
        # 丙辛日起戊子时
        # 丁壬日起庚子时
        # 戊癸日起壬子时
        base_gan = [0, 2, 4, 6, 8]  # 甲、丙、戊、庚、壬的索引
        zi_hour_gan = base_gan[day_gan_index % 5]
        gan_index = (zi_hour_gan + zhi_index) % 10
        
        return self.TIANGAN[gan_index], self.DIZHI[zhi_index]
    
    def calculate(self, dt: Optional[datetime] = None) -> GanzhiTime:
        """
        计算完整的四柱干支
        """
        if dt is None:
            dt = datetime.now()
        
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        
        # 处理子时跨日问题
        if hour == 23:
            # 晚子时属于第二天
            pass  # 暂时不处理，保持当日
        
        year_gan, year_zhi = self.calc_year_ganzhi(year)
        month_gan, month_zhi = self.calc_month_ganzhi(year, month, day)
        day_gan, day_zhi = self.calc_day_ganzhi(year, month, day)
        hour_gan, hour_zhi = self.calc_hour_ganzhi(year, month, day, hour)
        
        return GanzhiTime(
            year_gan=year_gan,
            year_zhi=year_zhi,
            month_gan=month_gan,
            month_zhi=month_zhi,
            day_gan=day_gan,
            day_zhi=day_zhi,
            hour_gan=hour_gan,
            hour_zhi=hour_zhi
        )
    
    def get_wuxing(self, ganzhi: str) -> str:
        """获取干支的五行"""
        if len(ganzhi) >= 1:
            # 以地支五行为主
            if len(ganzhi) >= 2 and ganzhi[1] in self.DIZHI_WUXING:
                return self.DIZHI_WUXING[ganzhi[1]]
            elif ganzhi[0] in self.TIANGAN_WUXING:
                return self.TIANGAN_WUXING[ganzhi[0]]
        return "未知"


if __name__ == "__main__":
    calc = GanzhiCalculator()
    
    # 测试当前时间
    ganzhi = calc.calculate()
    print(f"当前时间干支: {ganzhi}")
    print(f"日干: {ganzhi.day_gan}")
    print(f"月支(月建): {ganzhi.month_zhi}")
    
    # 测试特定日期
    from datetime import datetime
    test_dt = datetime(2026, 1, 28, 14, 30)
    ganzhi2 = calc.calculate(test_dt)
    print(f"\n2026年1月28日14:30: {ganzhi2}")
