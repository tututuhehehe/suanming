"""
起卦引擎 - 模拟铜钱起卦生成六爻
"""
import random
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class YaoResult:
    """单爻结果"""
    position: int       # 爻位 1-6
    value: int          # 爻值 6,7,8,9
    yao_type: str       # 类型名称
    is_yang: bool       # 是否阳爻
    is_changing: bool   # 是否变爻
    symbol: str         # 显示符号


@dataclass
class HexagramResult:
    """起卦结果"""
    timestamp: datetime
    yao_list: List[YaoResult]
    ben_gua_binary: str     # 本卦二进制 (阳=1, 阴=0)
    bian_gua_binary: str    # 变卦二进制
    changing_lines: List[int]  # 变爻位置列表


class DivinationEngine:
    """起卦引擎"""
    
    # 爻值映射
    YAO_MAPPING = {
        6: {"name": "老阴", "is_yang": False, "is_changing": True, "symbol": "━ ━ ✕"},
        7: {"name": "少阳", "is_yang": True, "is_changing": False, "symbol": "━━━"},
        8: {"name": "少阴", "is_yang": False, "is_changing": False, "symbol": "━ ━"},
        9: {"name": "老阳", "is_yang": True, "is_changing": True, "symbol": "━━━ ○"},
    }
    
    # 爻位名称
    YAO_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    
    def __init__(self):
        pass
    
    def _random_to_yao(self, rand: int) -> int:
        """
        将0-7的随机数转换为爻值
        概率: 老阴(6)=1/8, 少阳(7)=3/8, 少阴(8)=3/8, 老阳(9)=1/8
        """
        if rand == 0:
            return 6   # 老阴 (变爻)
        elif rand <= 3:
            return 7   # 少阳 (静爻)
        elif rand <= 6:
            return 8   # 少阴 (静爻)
        else:
            return 9   # 老阳 (变爻)
    
    def cast_single_yao(self, position: int) -> YaoResult:
        """投掷一次，生成单爻"""
        rand = random.randint(0, 7)
        value = self._random_to_yao(rand)
        mapping = self.YAO_MAPPING[value]
        
        return YaoResult(
            position=position,
            value=value,
            yao_type=mapping["name"],
            is_yang=mapping["is_yang"],
            is_changing=mapping["is_changing"],
            symbol=mapping["symbol"]
        )
    
    def cast_hexagram(self) -> HexagramResult:
        """完整起卦，生成六爻"""
        yao_list = []
        
        # 从初爻到上爻，依次投掷
        for i in range(1, 7):
            yao = self.cast_single_yao(i)
            yao_list.append(yao)
        
        # 计算本卦二进制
        ben_gua_binary = "".join(
            "1" if yao.is_yang else "0" 
            for yao in yao_list
        )
        
        # 计算变卦二进制（变爻阴阳互换）
        bian_gua_bits = []
        for yao in yao_list:
            if yao.is_changing:
                bian_gua_bits.append("0" if yao.is_yang else "1")
            else:
                bian_gua_bits.append("1" if yao.is_yang else "0")
        bian_gua_binary = "".join(bian_gua_bits)
        
        # 找出变爻位置
        changing_lines = [yao.position for yao in yao_list if yao.is_changing]
        
        return HexagramResult(
            timestamp=datetime.now(),
            yao_list=yao_list,
            ben_gua_binary=ben_gua_binary,
            bian_gua_binary=bian_gua_binary,
            changing_lines=changing_lines
        )
    
    def format_hexagram_display(self, result: HexagramResult) -> str:
        """格式化卦象显示"""
        lines = []
        # 从上爻到初爻显示
        for yao in reversed(result.yao_list):
            change_mark = " →" if yao.is_changing else "  "
            lines.append(f"  {self.YAO_NAMES[yao.position-1]}: {yao.symbol}{change_mark}")
        return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    engine = DivinationEngine()
    result = engine.cast_hexagram()
    print("起卦结果:")
    print(engine.format_hexagram_display(result))
    print(f"\n本卦二进制: {result.ben_gua_binary}")
    print(f"变卦二进制: {result.bian_gua_binary}")
    print(f"变爻位置: {result.changing_lines}")
