"""
知识上下文加载器 - 根据卦象动态加载相关知识
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from .hexagram_analyzer import AnalysisResult, HexagramInfo


class ContextLoader:
    """知识上下文加载器"""
    
    # 问事类型
    QUESTION_TYPES = {
        "1": "事业",
        "2": "财运", 
        "3": "感情",
        "4": "健康",
        "5": "学业",
        "6": "其他"
    }
    
    # 用神对照
    YONG_SHEN = {
        "事业": {"primary": "官鬼", "desc": "官鬼为用神，主职位、事业、上司"},
        "财运": {"primary": "妻财", "desc": "妻财为用神，主钱财、收益"},
        "感情": {"primary": "妻财/官鬼", "desc": "男问感情以妻财为用神，女问以官鬼为用神"},
        "健康": {"primary": "子孙", "desc": "子孙为用神，主医药、康复；官鬼为病"},
        "学业": {"primary": "父母", "desc": "父母为用神，主文书、学业、考试"},
        "其他": {"primary": "综合", "desc": "需根据具体问题综合判断用神"}
    }
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载知识库"""
        # 加载爻辞
        yao_ci_path = self.knowledge_dir / "yao_ci.json"
        if yao_ci_path.exists():
            with open(yao_ci_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 按卦ID和爻位索引
                self.yao_ci = {}
                for item in data["yao_ci"]:
                    key = (item["hexagram_id"], item["position"])
                    self.yao_ci[key] = item
        else:
            self.yao_ci = {}
        
        # 加载断卦规则
        rules_path = self.knowledge_dir / "divination_rules.json"
        if rules_path.exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                self.rules = json.load(f)
        else:
            self.rules = {}
        
        # 加载现代映射
        mapping_path = self.knowledge_dir / "modern_mapping.json"
        if mapping_path.exists():
            with open(mapping_path, "r", encoding="utf-8") as f:
                self.modern_mapping = json.load(f)
        else:
            self.modern_mapping = {}
    
    def load_context(self, analysis: AnalysisResult, question_type: str) -> str:
        """
        根据卦象和问事类型加载相关知识上下文
        """
        context_parts = []
        
        # 1. 本卦卦辞和大象
        context_parts.append(self._format_gua_info(analysis.ben_gua, "本卦"))
        
        # 2. 变卦信息（如有）
        if analysis.bian_gua:
            context_parts.append(self._format_gua_info(analysis.bian_gua, "变卦"))
        
        # 3. 变爻爻辞
        if analysis.changing_lines:
            yao_ci_text = self._get_yao_ci(analysis.ben_gua.id, analysis.changing_lines)
            if yao_ci_text:
                context_parts.append(f"### 变爻爻辞\n{yao_ci_text}")
        
        # 4. 用神规则（从规则库加载）
        yong_shen_text = self._get_yong_shen_rules(question_type)
        context_parts.append(f"### 用神指引\n{yong_shen_text}")
        
        # 5. 变爻数量断语
        bian_yao_text = self._get_bianyao_rules(len(analysis.changing_lines))
        if bian_yao_text:
            context_parts.append(f"### 变爻断语\n{bian_yao_text}")
        
        # 6. 特殊卦象提示
        special_notes = self._get_special_notes(analysis)
        if special_notes:
            context_parts.append(f"### 特殊提示\n{special_notes}")
        
        return "\n\n".join(context_parts)
    
    def _get_yong_shen_rules(self, question_type: str) -> str:
        """从规则库获取用神规则"""
        if not self.rules or "用神规则" not in self.rules:
            # 兜底：使用原有规则
            yong_shen_info = self.YONG_SHEN.get(question_type, self.YONG_SHEN["其他"])
            return f"问{question_type}：{yong_shen_info['desc']}"
        
        rules = self.rules["用神规则"]
        if question_type in rules:
            rule = rules[question_type]
            parts = [f"问{question_type}："]
            parts.append(f"- 用神：{rule.get('用神', '综合判断')}")
            if rule.get('原神'):
                parts.append(f"- 原神（生用神）：{rule['原神']}")
            if rule.get('忌神'):
                parts.append(f"- 忌神（克用神）：{rule['忌神']}")
            parts.append(f"- 说明：{rule.get('说明', '')}")
            return "\n".join(parts)
        else:
            return f"问{question_type}：需根据具体问题综合判断用神"
    
    def _get_bianyao_rules(self, num_changes: int) -> str:
        """获取变爻数量对应的断语"""
        if not self.rules or "变爻断语" not in self.rules:
            return ""
        
        rules = self.rules["变爻断语"]
        key_map = {
            0: "无变爻",
            1: "一爻变",
            2: "二爻变",
            3: "三爻变",
            4: "四爻变",
            5: "五爻变",
            6: "六爻变"
        }
        key = key_map.get(num_changes, "一爻变")
        
        if key in rules:
            rule = rules[key]
            text = rule.get("断语", "")
            if rule.get("细则"):
                text += f"\n{rule['细则']}"
            return text
        return ""
    
    def get_liuqin_duanyu(self, liuqin: str, is_wang: bool = True) -> str:
        """获取六亲断语"""
        if not self.rules or "六亲断语" not in self.rules:
            return ""
        
        rules = self.rules["六亲断语"]
        if liuqin in rules:
            rule = rules[liuqin]
            key = "旺相" if is_wang else "休囚"
            return rule.get(key, "")
        return ""
    
    def get_liushen_duanyu(self, liushen: str, is_ji: bool = False) -> str:
        """获取六神断语"""
        if not self.rules or "六神断语" not in self.rules:
            return ""
        
        rules = self.rules["六神断语"]
        if liushen in rules:
            rule = rules[liushen]
            key = "凶象" if is_ji else "吉象"
            return rule.get(key, "")
        return ""
    
    def get_wangshuai_duanyu(self, wang_shuai: str) -> str:
        """获取旺衰断语"""
        if not self.rules or "旺衰断语" not in self.rules:
            return ""
        
        rules = self.rules["旺衰断语"]
        if wang_shuai in rules:
            rule = rules[wang_shuai]
            duanyu_list = rule.get("断语", [])
            if duanyu_list:
                return duanyu_list[0]  # 返回第一条断语
        return ""
    
    def get_special_geju(self, analysis: AnalysisResult) -> str:
        """判断特殊格局"""
        if not self.rules or "特殊格局" not in self.rules:
            return ""
        
        rules = self.rules["特殊格局"]
        notes = []
        
        # 检查纯卦
        if analysis.ben_gua.upper == analysis.ben_gua.lower:
            gua_name = analysis.ben_gua.upper
            if gua_name in ["乾", "坤"]:
                if len(analysis.changing_lines) == 6:
                    notes.append("六爻全变，用九/用六之象。")
        
        # 检查六冲卦（简化检查：天地否、地天泰等）
        liu_chong_gua = ["天地否", "地天泰", "山泽损", "泽山咸", "雷风恒", "风雷益"]
        if analysis.ben_gua.full_name in liu_chong_gua:
            if "六冲卦" in rules:
                notes.append(rules["六冲卦"]["断语"])
        
        return "\n".join(notes)
    
    def get_modern_scene(self, question_type: str) -> str:
        """获取问事类型的现代场景映射"""
        if not self.modern_mapping or "问事场景映射" not in self.modern_mapping:
            return ""
        
        mapping = self.modern_mapping["问事场景映射"]
        if question_type in mapping:
            scenes = mapping[question_type].get("现代场景", [])
            return "、".join(scenes)
        return ""
    
    def get_liuqin_modern(self, liuqin: str) -> Dict:
        """获取六亲的现代映射"""
        if not self.modern_mapping or "六亲现代映射" not in self.modern_mapping:
            return {}
        
        mapping = self.modern_mapping["六亲现代映射"]
        if liuqin in mapping:
            return mapping[liuqin].get("现代", {})
        return {}
    
    def get_bagua_modern(self, gua_name: str) -> Dict:
        """获取八卦的现代映射"""
        if not self.modern_mapping or "八卦现代映射" not in self.modern_mapping:
            return {}
        
        return self.modern_mapping["八卦现代映射"].get(gua_name, {})
    
    def _format_gua_info(self, gua: HexagramInfo, title: str) -> str:
        """格式化卦象信息"""
        lines = [
            f"### {title}：{gua.full_name} {gua.symbol}",
            f"- 上卦：{gua.upper}，下卦：{gua.lower}",
            f"- 卦宫：{gua.gong}",
            f"- 世爻在{gua.shi_yao}爻，应爻在{gua.ying_yao}爻",
            f"\n**卦辞**：{gua.gua_ci}",
            f"\n**大象**：{gua.da_xiang}"
        ]
        if gua.tuan_zhuan:
            lines.append(f"\n**彖传**：{gua.tuan_zhuan}")
        return "\n".join(lines)
    
    def _get_yao_ci(self, hexagram_id: int, positions: List[int]) -> str:
        """获取指定位置的爻辞"""
        yao_texts = []
        yao_names = ["初", "二", "三", "四", "五", "上"]
        
        for pos in positions:
            key = (hexagram_id, pos)
            if key in self.yao_ci:
                item = self.yao_ci[key]
                yao_texts.append(f"**{item['name']}**：{item['text']}")
                if item.get('xiang_zhuan'):
                    yao_texts.append(f"  象曰：{item['xiang_zhuan']}")
        
        return "\n".join(yao_texts) if yao_texts else ""
    
    def _get_special_notes(self, analysis: AnalysisResult) -> str:
        """获取特殊卦象提示"""
        notes = []
        
        # 检查是否纯卦（上下卦相同）
        if analysis.ben_gua.upper == analysis.ben_gua.lower:
            notes.append(f"此为纯卦（{analysis.ben_gua.upper}为{analysis.ben_gua.upper}），卦气纯粹，主事专一。")
        
        # 变爻数量提示
        num_changes = len(analysis.changing_lines)
        if num_changes == 0:
            notes.append("六爻皆静，以本卦卦辞为主断。")
        elif num_changes == 1:
            notes.append(f"一爻变动，以该变爻爻辞为主断。")
        elif num_changes == 2:
            notes.append("二爻变动，以上变爻爻辞为主，参考下变爻。")
        elif num_changes == 3:
            notes.append("三爻变动，本卦变卦卦辞并参，变化较大。")
        elif num_changes >= 4:
            notes.append("多爻变动，局势不稳，变数较多，以变卦卦辞为主参考。")
        
        return "\n".join(notes) if notes else ""


if __name__ == "__main__":
    from .divination_engine import DivinationEngine
    from .hexagram_analyzer import HexagramAnalyzer
    
    engine = DivinationEngine()
    result = engine.cast_hexagram()
    
    analyzer = HexagramAnalyzer()
    analysis = analyzer.analyze(result)
    
    loader = ContextLoader()
    context = loader.load_context(analysis, "事业")
    print(context)
