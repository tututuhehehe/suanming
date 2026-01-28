"""
纳甲排盘模块 - 实现六爻的天干地支、六亲、六神配置
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class YaoNajia:
    """单爻纳甲信息"""
    position: int           # 爻位 1-6
    yao_value: int          # 爻值 6/7/8/9
    is_yang: bool           # 是否阳爻
    is_changing: bool       # 是否变爻
    tiangan: str            # 天干
    dizhi: str              # 地支
    wuxing: str             # 五行
    liuqin: str             # 六亲
    liushen: str            # 六神
    shi_yao: bool           # 是否世爻
    ying_yao: bool          # 是否应爻
    wang_shuai: str = ""    # 旺衰状态：旺/相/休/囚/死


@dataclass  
class PaipanResult:
    """完整排盘结果"""
    ben_gua_name: str                   # 本卦名
    bian_gua_name: Optional[str]        # 变卦名
    gong: str                           # 卦宫
    gong_wuxing: str                    # 卦宫五行
    shi_yao: int                        # 世爻位置
    ying_yao: int                       # 应爻位置
    ben_gua_yaos: List[YaoNajia]        # 本卦六爻
    bian_gua_yaos: Optional[List[YaoNajia]]  # 变卦六爻
    month_jian: str = ""                # 月建地支
    day_chen: str = ""                  # 日辰地支


class WangShuaiCalculator:
    """旺衰计算器"""
    
    # 五行旺相休囚死对照表
    # 格式: {月建五行: {爻五行: 旺衰状态}}
    WANGSHUAI_TABLE = {
        "木": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
        "火": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
        "土": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"},
        "金": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
        "水": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"}
    }
    
    # 地支五行
    DIZHI_WUXING = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木",
        "辰": "土", "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土", "亥": "水"
    }
    
    # 地支季节对应的五行
    # 寅卯辰=春(木旺), 巳午未=夏(火旺), 申酉戌=秋(金旺), 亥子丑=冬(水旺)
    # 辰戌丑未月中土旺
    MONTH_WUXING = {
        "寅": "木", "卯": "木", "辰": "土",
        "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土",
        "亥": "水", "子": "水", "丑": "土"
    }
    
    @classmethod
    def calc_wangshuai(cls, yao_wuxing: str, month_zhi: str) -> str:
        """
        计算爻的旺衰状态
        
        参数:
            yao_wuxing: 爻的五行
            month_zhi: 月建地支
        返回:
            旺/相/休/囚/死
        """
        month_wuxing = cls.MONTH_WUXING.get(month_zhi, "土")
        return cls.WANGSHUAI_TABLE.get(month_wuxing, {}).get(yao_wuxing, "休")
    
    @classmethod
    def is_ri_sheng(cls, yao_dizhi: str, day_zhi: str) -> bool:
        """判断是否日辰生爻"""
        day_wuxing = cls.DIZHI_WUXING.get(day_zhi, "土")
        yao_wuxing = cls.DIZHI_WUXING.get(yao_dizhi, "土")
        # 五行相生
        sheng_map = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        return sheng_map.get(day_wuxing) == yao_wuxing
    
    @classmethod
    def is_ri_ke(cls, yao_dizhi: str, day_zhi: str) -> bool:
        """判断是否日辰克爻"""
        day_wuxing = cls.DIZHI_WUXING.get(day_zhi, "土")
        yao_wuxing = cls.DIZHI_WUXING.get(yao_dizhi, "土")
        # 五行相克
        ke_map = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
        return ke_map.get(day_wuxing) == yao_wuxing
    
    @classmethod
    def get_status_symbol(cls, wang_shuai: str) -> str:
        """获取旺衰状态符号"""
        symbols = {"旺": "🔥", "相": "✨", "休": "💤", "囚": "⛓️", "死": "💀"}
        return symbols.get(wang_shuai, "")


class NajiaEngine:
    """纳甲排盘引擎"""
    
    def __init__(self, najia_path: str = "knowledge/najia.json"):
        self.najia_data = self._load_najia(najia_path)
        self.bagua_najia = self.najia_data["八卦纳甲"]
        self.dizhi_wuxing = self.najia_data["地支五行"]
        self.gong_wuxing = self.najia_data["卦宫对照"]
        self.liushen_config = self.najia_data["六神配置"]
        
        # 八卦名到序号的映射
        self.gua_to_binary = {
            "乾": "111", "兑": "110", "离": "101", "震": "100",
            "巽": "011", "坎": "010", "艮": "001", "坤": "000"
        }
        self.binary_to_gua = {v: k for k, v in self.gua_to_binary.items()}
    
    def _load_najia(self, path: str) -> dict:
        """加载纳甲配置"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_trigram_najia(self, trigram: str, is_upper: bool) -> List[Tuple[str, str]]:
        """
        获取单卦（三爻）的纳甲
        返回: [(天干, 地支), ...] 三个爻
        """
        config = self.bagua_najia[trigram]
        tiangan = config["天干"]
        dizhi_list = config["地支"]
        
        if is_upper:
            # 上卦取后三个地支 (四五六爻)
            return [(tiangan, dizhi_list[3]), (tiangan, dizhi_list[4]), (tiangan, dizhi_list[5])]
        else:
            # 下卦取前三个地支 (初二三爻)
            return [(tiangan, dizhi_list[0]), (tiangan, dizhi_list[1]), (tiangan, dizhi_list[2])]
    
    def calc_liuqin(self, yao_wuxing: str, gong_wuxing: str) -> str:
        """
        计算六亲关系
        以卦宫五行为"我"
        """
        wuxing_sheng = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        wuxing_ke = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
        
        if yao_wuxing == gong_wuxing:
            return "兄弟"
        elif wuxing_sheng.get(gong_wuxing) == yao_wuxing:
            return "子孙"  # 我生者
        elif wuxing_sheng.get(yao_wuxing) == gong_wuxing:
            return "父母"  # 生我者
        elif wuxing_ke.get(gong_wuxing) == yao_wuxing:
            return "妻财"  # 我克者
        elif wuxing_ke.get(yao_wuxing) == gong_wuxing:
            return "官鬼"  # 克我者
        else:
            return "未知"
    
    def get_liushen(self, ri_gan: str) -> List[str]:
        """
        根据日干获取六神配置
        返回初爻到上爻的六神列表
        """
        if ri_gan in ["甲", "乙"]:
            return self.liushen_config["甲乙日"]
        elif ri_gan in ["丙", "丁"]:
            return self.liushen_config["丙丁日"]
        elif ri_gan == "戊":
            return self.liushen_config["戊日"]
        elif ri_gan == "己":
            return self.liushen_config["己日"]
        elif ri_gan in ["庚", "辛"]:
            return self.liushen_config["庚辛日"]
        elif ri_gan in ["壬", "癸"]:
            return self.liushen_config["壬癸日"]
        else:
            # 默认返回甲乙日配置
            return self.liushen_config["甲乙日"]
    
    def paipan(
        self, 
        yao_values: List[int],
        upper_trigram: str,
        lower_trigram: str,
        gong: str,
        shi_yao: int,
        ying_yao: int,
        ben_gua_name: str,
        bian_gua_name: Optional[str] = None,
        bian_upper: Optional[str] = None,
        bian_lower: Optional[str] = None,
        ri_gan: str = "甲",
        month_zhi: str = "",
        day_zhi: str = ""
    ) -> PaipanResult:
        """
        完整排盘
        
        参数:
            yao_values: 六爻值列表 [初爻, 二爻, ..., 上爻]
            upper_trigram: 上卦名 (如 "乾")
            lower_trigram: 下卦名 (如 "坤")
            gong: 卦宫 (如 "乾宫")
            shi_yao: 世爻位置 1-6
            ying_yao: 应爻位置 1-6
            ben_gua_name: 本卦全名
            bian_gua_name: 变卦全名 (可选)
            bian_upper: 变卦上卦名 (可选)
            bian_lower: 变卦下卦名 (可选)
            ri_gan: 日干，用于配置六神
            month_zhi: 月建地支，用于旺衰判断
            day_zhi: 日辰地支
        """
        # 获取卦宫五行
        gong_wuxing = self.gong_wuxing.get(gong, "金")
        
        # 获取六神
        liushen_list = self.get_liushen(ri_gan)
        
        # 获取本卦纳甲
        lower_najia = self.get_trigram_najia(lower_trigram, is_upper=False)
        upper_najia = self.get_trigram_najia(upper_trigram, is_upper=True)
        
        # 识别变爻
        changing_positions = []
        for i, val in enumerate(yao_values):
            if val in [6, 9]:  # 老阴、老阳为变爻
                changing_positions.append(i + 1)
        
        # 构建本卦六爻
        ben_gua_yaos = []
        for i in range(6):
            pos = i + 1
            yao_val = yao_values[i]
            is_yang = yao_val in [7, 9]  # 7少阳, 9老阳
            is_changing = pos in changing_positions
            
            # 获取纳甲
            if i < 3:
                tiangan, dizhi = lower_najia[i]
            else:
                tiangan, dizhi = upper_najia[i - 3]
            
            # 获取五行
            wuxing = self.dizhi_wuxing[dizhi]
            
            # 计算六亲
            liuqin = self.calc_liuqin(wuxing, gong_wuxing)
            
            # 获取六神
            liushen = liushen_list[i]
            
            # 计算旺衰
            wang_shuai = ""
            if month_zhi:
                wang_shuai = WangShuaiCalculator.calc_wangshuai(wuxing, month_zhi)
            
            yao = YaoNajia(
                position=pos,
                yao_value=yao_val,
                is_yang=is_yang,
                is_changing=is_changing,
                tiangan=tiangan,
                dizhi=dizhi,
                wuxing=wuxing,
                liuqin=liuqin,
                liushen=liushen,
                shi_yao=(pos == shi_yao),
                ying_yao=(pos == ying_yao),
                wang_shuai=wang_shuai
            )
            ben_gua_yaos.append(yao)
        
        # 构建变卦六爻 (如果有)
        bian_gua_yaos = None
        if bian_gua_name and bian_upper and bian_lower:
            bian_lower_najia = self.get_trigram_najia(bian_lower, is_upper=False)
            bian_upper_najia = self.get_trigram_najia(bian_upper, is_upper=True)
            
            bian_gua_yaos = []
            for i in range(6):
                pos = i + 1
                # 变爻阴阳互换
                original_val = yao_values[i]
                if pos in changing_positions:
                    is_yang = original_val in [6]  # 老阴变阳
                    if original_val == 9:
                        is_yang = False  # 老阳变阴
                else:
                    is_yang = original_val in [7, 9]
                
                # 获取变卦纳甲
                if i < 3:
                    tiangan, dizhi = bian_lower_najia[i]
                else:
                    tiangan, dizhi = bian_upper_najia[i - 3]
                
                wuxing = self.dizhi_wuxing[dizhi]
                liuqin = self.calc_liuqin(wuxing, gong_wuxing)
                
                # 变卦也计算旺衰
                bian_wang_shuai = ""
                if month_zhi:
                    bian_wang_shuai = WangShuaiCalculator.calc_wangshuai(wuxing, month_zhi)
                
                yao = YaoNajia(
                    position=pos,
                    yao_value=7 if is_yang else 8,  # 变卦都是静爻
                    is_yang=is_yang,
                    is_changing=False,
                    tiangan=tiangan,
                    dizhi=dizhi,
                    wuxing=wuxing,
                    liuqin=liuqin,
                    liushen=liushen_list[i],
                    shi_yao=(pos == shi_yao),
                    ying_yao=(pos == ying_yao),
                    wang_shuai=bian_wang_shuai
                )
                bian_gua_yaos.append(yao)
        
        return PaipanResult(
            ben_gua_name=ben_gua_name,
            bian_gua_name=bian_gua_name,
            gong=gong,
            gong_wuxing=gong_wuxing,
            shi_yao=shi_yao,
            ying_yao=ying_yao,
            ben_gua_yaos=ben_gua_yaos,
            bian_gua_yaos=bian_gua_yaos,
            month_jian=month_zhi,
            day_chen=day_zhi
        )
    
    def format_paipan_table(self, result: PaipanResult) -> str:
        """格式化排盘结果为表格字符串"""
        lines = []
        lines.append(f"【{result.ben_gua_name}】 {result.gong} ({result.gong_wuxing})")
        lines.append("=" * 60)
        
        # 表头
        if result.bian_gua_yaos:
            lines.append(f"{'六神':<6}{'本卦':<20}{'变卦':<20}")
        else:
            lines.append(f"{'六神':<6}{'卦象':<40}")
        
        lines.append("-" * 60)
        
        # 从上爻到初爻显示
        for i in range(5, -1, -1):
            ben_yao = result.ben_gua_yaos[i]
            
            # 爻位标记
            pos_name = ["初", "二", "三", "四", "五", "上"][i]
            shi_ying = ""
            if ben_yao.shi_yao:
                shi_ying = "世"
            elif ben_yao.ying_yao:
                shi_ying = "应"
            
            # 爻象
            yao_symbol = "━━━" if ben_yao.is_yang else "━ ━"
            if ben_yao.is_changing:
                yao_symbol += " ○" if ben_yao.is_yang else " ✕"
            
            # 本卦信息
            ben_info = f"{pos_name}{shi_ying:<2} {ben_yao.liuqin:<4} {ben_yao.tiangan}{ben_yao.dizhi}{ben_yao.wuxing} {yao_symbol}"
            
            # 六神
            liushen = ben_yao.liushen
            
            if result.bian_gua_yaos:
                bian_yao = result.bian_gua_yaos[i]
                bian_symbol = "━━━" if bian_yao.is_yang else "━ ━"
                bian_info = f"{bian_yao.liuqin:<4} {bian_yao.tiangan}{bian_yao.dizhi}{bian_yao.wuxing} {bian_symbol}"
                lines.append(f"{liushen:<6}{ben_info:<20}{bian_info:<20}")
            else:
                lines.append(f"{liushen:<6}{ben_info:<40}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    engine = NajiaEngine()
    
    # 模拟天水讼卦 (乾上坎下)
    result = engine.paipan(
        yao_values=[7, 8, 7, 9, 7, 7],  # 有一个变爻
        upper_trigram="乾",
        lower_trigram="坎",
        gong="乾宫",
        shi_yao=4,
        ying_yao=1,
        ben_gua_name="天水讼",
        bian_gua_name="天火同人",
        bian_upper="乾",
        bian_lower="离",
        ri_gan="甲"
    )
    
    print(engine.format_paipan_table(result))
