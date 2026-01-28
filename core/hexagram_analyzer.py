"""
卦象分析器 - 识别卦象、计算排盘信息
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .divination_engine import HexagramResult


@dataclass
class HexagramInfo:
    """卦象信息"""
    id: int
    name: str
    full_name: str
    symbol: str
    upper: str          # 上卦名
    lower: str          # 下卦名
    gong: str           # 卦宫
    shi_yao: int        # 世爻位置
    ying_yao: int       # 应爻位置
    gua_ci: str         # 卦辞
    da_xiang: str       # 大象
    tuan_zhuan: str     # 彖传


@dataclass 
class AnalysisResult:
    """排盘分析结果"""
    ben_gua: HexagramInfo       # 本卦信息
    bian_gua: Optional[HexagramInfo]  # 变卦信息
    changing_lines: List[int]   # 变爻位置
    has_change: bool            # 是否有变爻


class HexagramAnalyzer:
    """卦象分析器"""
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载知识库"""
        # 加载八卦数据
        bagua_path = self.knowledge_dir / "bagua.json"
        with open(bagua_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.bagua = {g["binary"]: g for g in data["bagua"]}
            self.bagua_by_name = {g["name"]: g for g in data["bagua"]}
        
        # 加载六十四卦数据
        hexagrams_path = self.knowledge_dir / "hexagrams.json"
        with open(hexagrams_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 按二进制索引
            self.hexagrams = {h["binary"]: h for h in data["hexagrams"]}
            # 按ID索引
            self.hexagrams_by_id = {h["id"]: h for h in data["hexagrams"]}
    
    def _binary_to_hexagram_info(self, binary: str) -> HexagramInfo:
        """根据二进制获取卦象信息"""
        hex_data = self.hexagrams.get(binary)
        if not hex_data:
            raise ValueError(f"未找到二进制为 {binary} 的卦象")
        
        return HexagramInfo(
            id=hex_data["id"],
            name=hex_data["name"],
            full_name=hex_data["full_name"],
            symbol=hex_data["symbol"],
            upper=hex_data["upper"],
            lower=hex_data["lower"],
            gong=hex_data["gong"],
            shi_yao=hex_data["shi_yao"],
            ying_yao=hex_data["ying_yao"],
            gua_ci=hex_data["gua_ci"],
            da_xiang=hex_data["da_xiang"],
            tuan_zhuan=hex_data.get("tuan_zhuan", "")
        )
    
    def analyze(self, result: HexagramResult) -> AnalysisResult:
        """分析起卦结果"""
        # 获取本卦信息
        ben_gua = self._binary_to_hexagram_info(result.ben_gua_binary)
        
        # 获取变卦信息（如有变爻）
        bian_gua = None
        has_change = len(result.changing_lines) > 0
        if has_change and result.ben_gua_binary != result.bian_gua_binary:
            bian_gua = self._binary_to_hexagram_info(result.bian_gua_binary)
        
        return AnalysisResult(
            ben_gua=ben_gua,
            bian_gua=bian_gua,
            changing_lines=result.changing_lines,
            has_change=has_change
        )
    
    def get_upper_lower_gua(self, binary: str) -> Tuple[Dict, Dict]:
        """获取上下卦信息"""
        lower_binary = binary[:3]  # 初二三爻为内卦
        upper_binary = binary[3:]  # 四五六爻为外卦
        
        lower_gua = self.bagua.get(lower_binary)
        upper_gua = self.bagua.get(upper_binary)
        
        return upper_gua, lower_gua


if __name__ == "__main__":
    from .divination_engine import DivinationEngine
    
    engine = DivinationEngine()
    result = engine.cast_hexagram()
    
    analyzer = HexagramAnalyzer()
    analysis = analyzer.analyze(result)
    
    print(f"本卦: {analysis.ben_gua.full_name} {analysis.ben_gua.symbol}")
    print(f"卦辞: {analysis.ben_gua.gua_ci}")
    if analysis.bian_gua:
        print(f"变卦: {analysis.bian_gua.full_name} {analysis.bian_gua.symbol}")
