"""
专业解卦分析引擎 - 实现人类六爻大师的五维分析逻辑

五个核心维度：
1. 取用神 (Target Selection) - 根据问事类型锁定主角爻
2. 看旺衰 (Environmental Analysis) - 月建日辰的环境分析
3. 看动爻 (Dynamic Interaction) - 动态博弈分析
4. 看世应 (Subject vs Object) - 敌我形势分析
5. 看六神 (Flavor Details) - 细节描绘
"""
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path


@dataclass
class YaoAnalysis:
    """单爻分析结果"""
    position: int           # 爻位 1-6
    liuqin: str            # 六亲
    liushen: str           # 六神
    tiangan: str           # 天干
    dizhi: str             # 地支
    wuxing: str            # 五行
    wang_shuai: str        # 旺衰状态
    is_dong: bool          # 是否动爻
    is_shi: bool           # 是否世爻
    is_ying: bool          # 是否应爻
    is_yong_shen: bool = False      # 是否用神
    is_yuan_shen: bool = False      # 是否原神
    is_ji_shen: bool = False        # 是否忌神
    is_chou_shen: bool = False      # 是否仇神
    bian_dizhi: str = ""            # 变爻地支
    bian_wuxing: str = ""           # 变爻五行
    hui_tou_sheng: bool = False     # 是否回头生
    hui_tou_ke: bool = False        # 是否回头克
    ri_sheng: bool = False          # 日辰生
    ri_ke: bool = False             # 日辰克
    yue_sheng: bool = False         # 月建生
    yue_ke: bool = False            # 月建克
    score: int = 0                  # 综合评分


@dataclass
class AnalysisReport:
    """完整分析报告"""
    # 基础信息
    question: str
    question_type: str
    month_zhi: str          # 月建
    day_zhi: str            # 日辰
    ri_gan: str             # 日干
    
    # 卦象信息
    ben_gua: str
    bian_gua: Optional[str]
    gong: str
    gong_wuxing: str
    
    # 六爻分析
    yaos: List[YaoAnalysis]
    
    # 核心判断
    yong_shen_pos: int = 0          # 用神爻位
    yong_shen_status: str = ""      # 用神状态（旺/衰/空/破）
    yong_shen_score: int = 0        # 用神综合评分
    
    # 世应分析
    shi_pos: int = 0
    ying_pos: int = 0
    shi_ying_relation: str = ""     # 世应关系（相生/相克/比和）
    
    # 动爻分析
    dong_yao_analysis: List[str] = field(default_factory=list)
    
    # 特殊状态
    kong_wang: List[int] = field(default_factory=list)  # 空亡爻位
    yue_po: List[int] = field(default_factory=list)     # 月破爻位
    
    # 综合判断
    ji_xiong: str = ""              # 吉凶判断
    conclusion: str = ""            # 结论


class AnalysisEngine:
    """专业解卦分析引擎"""
    
    # 五行相生
    WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    # 五行相克
    WUXING_KE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
    # 五行被生
    WUXING_BEI_SHENG = {"火": "木", "土": "火", "金": "土", "水": "金", "木": "水"}
    # 五行被克
    WUXING_BEI_KE = {"土": "木", "金": "火", "水": "土", "木": "金", "火": "水"}
    
    # 地支五行
    DIZHI_WUXING = {
        "子": "水", "丑": "土", "寅": "木", "卯": "木",
        "辰": "土", "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土", "亥": "水"
    }
    
    # 用神对照表
    YONG_SHEN_MAP = {
        "事业": {"用神": "官鬼", "原神": "妻财", "忌神": "子孙", "仇神": "兄弟"},
        "财运": {"用神": "妻财", "原神": "子孙", "忌神": "兄弟", "仇神": "父母"},
        "感情": {"用神": "妻财", "原神": "子孙", "忌神": "兄弟", "仇神": "父母"},  # 默认男问女
        "健康": {"用神": "子孙", "原神": "兄弟", "忌神": "官鬼", "仇神": "妻财"},
        "学业": {"用神": "父母", "原神": "官鬼", "忌神": "妻财", "仇神": "子孙"},
        "出行": {"用神": "世爻", "原神": "父母", "忌神": "官鬼", "仇神": "兄弟"},
        "其他": {"用神": "世爻", "原神": "", "忌神": "官鬼", "仇神": ""}
    }
    
    # 旺衰评分表
    WANG_SHUAI_SCORE = {"旺": 100, "相": 80, "休": 50, "囚": 30, "死": 10}
    
    # 月建旺衰
    MONTH_WUXING = {
        "寅": "木", "卯": "木", "辰": "土",
        "巳": "火", "午": "火", "未": "土",
        "申": "金", "酉": "金", "戌": "土",
        "亥": "水", "子": "水", "丑": "土"
    }
    
    # 空亡表（按日支）
    KONG_WANG_TABLE = {
        "甲子": ["戌", "亥"], "甲戌": ["申", "酉"], "甲申": ["午", "未"],
        "甲午": ["辰", "巳"], "甲辰": ["寅", "卯"], "甲寅": ["子", "丑"],
    }
    
    def __init__(self, rules_path: str = "knowledge/divination_rules.json"):
        self.rules = self._load_rules(rules_path)
    
    def _load_rules(self, path: str) -> dict:
        """加载断卦规则"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    
    def analyze(
        self,
        question: str,
        question_type: str,
        paipan_result,  # PaipanResult from najia_engine
        month_zhi: str,
        day_zhi: str,
        ri_gan: str
    ) -> AnalysisReport:
        """
        执行完整的五维分析
        """
        # 初始化报告
        report = AnalysisReport(
            question=question,
            question_type=question_type,
            month_zhi=month_zhi,
            day_zhi=day_zhi,
            ri_gan=ri_gan,
            ben_gua=paipan_result.ben_gua_name,
            bian_gua=paipan_result.bian_gua_name,
            gong=paipan_result.gong,
            gong_wuxing=paipan_result.gong_wuxing,
            yaos=[]
        )
        
        # 第一步：构建六爻基础分析
        yong_shen_config = self.YONG_SHEN_MAP.get(question_type, self.YONG_SHEN_MAP["其他"])
        
        for yao in paipan_result.ben_gua_yaos:
            yao_analysis = YaoAnalysis(
                position=yao.position,
                liuqin=yao.liuqin,
                liushen=yao.liushen,
                tiangan=yao.tiangan,
                dizhi=yao.dizhi,
                wuxing=yao.wuxing,
                wang_shuai=yao.wang_shuai,
                is_dong=yao.is_changing,
                is_shi=yao.shi_yao,
                is_ying=yao.ying_yao
            )
            
            # 标记用神/原神/忌神/仇神
            if yong_shen_config["用神"] == "世爻":
                yao_analysis.is_yong_shen = yao.shi_yao
            else:
                yao_analysis.is_yong_shen = (yao.liuqin == yong_shen_config["用神"])
            
            yao_analysis.is_yuan_shen = (yao.liuqin == yong_shen_config.get("原神", ""))
            yao_analysis.is_ji_shen = (yao.liuqin == yong_shen_config.get("忌神", ""))
            yao_analysis.is_chou_shen = (yao.liuqin == yong_shen_config.get("仇神", ""))
            
            # 计算日月生克
            self._calc_ri_yue_shengke(yao_analysis, month_zhi, day_zhi)
            
            # 如果是动爻，分析变爻
            if yao.is_changing and paipan_result.bian_gua_yaos:
                bian_yao = paipan_result.bian_gua_yaos[yao.position - 1]
                yao_analysis.bian_dizhi = bian_yao.dizhi
                yao_analysis.bian_wuxing = bian_yao.wuxing
                
                # 判断回头生/克
                if self.WUXING_SHENG.get(bian_yao.wuxing) == yao.wuxing:
                    yao_analysis.hui_tou_sheng = True
                elif self.WUXING_KE.get(bian_yao.wuxing) == yao.wuxing:
                    yao_analysis.hui_tou_ke = True
            
            # 计算综合评分
            yao_analysis.score = self._calc_yao_score(yao_analysis)
            
            report.yaos.append(yao_analysis)
        
        # 第二步：找出用神并分析其状态
        self._analyze_yong_shen(report)
        
        # 第三步：分析世应关系
        self._analyze_shi_ying(report)
        
        # 第四步：分析动爻
        self._analyze_dong_yao(report)
        
        # 第五步：综合判断吉凶
        self._make_conclusion(report)
        
        return report
    
    def _calc_ri_yue_shengke(self, yao: YaoAnalysis, month_zhi: str, day_zhi: str):
        """计算日月生克"""
        yao_wuxing = yao.wuxing
        month_wuxing = self.MONTH_WUXING.get(month_zhi, "土")
        day_wuxing = self.DIZHI_WUXING.get(day_zhi, "土")
        
        # 月建生克
        if self.WUXING_SHENG.get(month_wuxing) == yao_wuxing:
            yao.yue_sheng = True
        elif self.WUXING_KE.get(month_wuxing) == yao_wuxing:
            yao.yue_ke = True
        
        # 日辰生克
        if self.WUXING_SHENG.get(day_wuxing) == yao_wuxing:
            yao.ri_sheng = True
        elif self.WUXING_KE.get(day_wuxing) == yao_wuxing:
            yao.ri_ke = True
    
    def _calc_yao_score(self, yao: YaoAnalysis) -> int:
        """计算单爻综合评分"""
        # 基础分：旺衰
        score = self.WANG_SHUAI_SCORE.get(yao.wang_shuai, 50)
        
        # 日月生扶加分
        if yao.yue_sheng:
            score += 20
        if yao.ri_sheng:
            score += 15
        
        # 日月克制减分
        if yao.yue_ke:
            score -= 25
        if yao.ri_ke:
            score -= 15
        
        # 动爻影响
        if yao.is_dong:
            if yao.hui_tou_sheng:
                score += 30  # 回头生大加分
            elif yao.hui_tou_ke:
                score -= 40  # 回头克大减分
        
        return max(0, min(150, score))  # 限制在0-150
    
    def _analyze_yong_shen(self, report: AnalysisReport):
        """分析用神状态"""
        yong_shen_yaos = [y for y in report.yaos if y.is_yong_shen]
        
        if yong_shen_yaos:
            # 取最强的用神（如有多个）
            yong = max(yong_shen_yaos, key=lambda x: x.score)
            report.yong_shen_pos = yong.position
            report.yong_shen_score = yong.score
            
            # 判断状态
            status_parts = []
            if yong.wang_shuai in ["旺", "相"]:
                status_parts.append("旺相有力")
            elif yong.wang_shuai in ["休", "囚", "死"]:
                status_parts.append("休囚无力")
            
            if yong.ri_sheng:
                status_parts.append("得日生扶")
            if yong.ri_ke:
                status_parts.append("受日克制")
            if yong.yue_sheng:
                status_parts.append("得月生扶")
            if yong.yue_ke:
                status_parts.append("受月克制")
            
            if yong.is_dong:
                if yong.hui_tou_sheng:
                    status_parts.append("动化回头生，力量增强")
                elif yong.hui_tou_ke:
                    status_parts.append("动化回头克，自取灭亡")
            
            report.yong_shen_status = "，".join(status_parts) if status_parts else "状态中平"
    
    def _analyze_shi_ying(self, report: AnalysisReport):
        """分析世应关系"""
        shi_yao = None
        ying_yao = None
        
        for yao in report.yaos:
            if yao.is_shi:
                shi_yao = yao
                report.shi_pos = yao.position
            if yao.is_ying:
                ying_yao = yao
                report.ying_pos = yao.position
        
        if shi_yao and ying_yao:
            shi_wx = shi_yao.wuxing
            ying_wx = ying_yao.wuxing
            
            if self.WUXING_SHENG.get(shi_wx) == ying_wx:
                report.shi_ying_relation = "世生应，我方主动付出"
            elif self.WUXING_SHENG.get(ying_wx) == shi_wx:
                report.shi_ying_relation = "应生世，对方有利于我"
            elif self.WUXING_KE.get(shi_wx) == ying_wx:
                report.shi_ying_relation = "世克应，我方占优势"
            elif self.WUXING_KE.get(ying_wx) == shi_wx:
                report.shi_ying_relation = "应克世，对方压制我方"
            elif shi_wx == ying_wx:
                report.shi_ying_relation = "世应比和，双方势均力敌"
            else:
                report.shi_ying_relation = "世应无直接生克"
    
    def _analyze_dong_yao(self, report: AnalysisReport):
        """分析动爻"""
        dong_yaos = [y for y in report.yaos if y.is_dong]
        
        if not dong_yaos:
            report.dong_yao_analysis.append("六爻皆静，以静制动，按本卦断")
            return
        
        # 找出用神
        yong_shen = next((y for y in report.yaos if y.is_yong_shen), None)
        
        for dong in dong_yaos:
            pos_name = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][dong.position - 1]
            analysis = f"{pos_name}动（{dong.liuqin}{dong.liushen}）"
            
            # 分析动爻对用神的影响
            if yong_shen and dong.position != yong_shen.position:
                dong_wx = dong.wuxing
                yong_wx = yong_shen.wuxing
                
                if self.WUXING_SHENG.get(dong_wx) == yong_wx:
                    analysis += f"，生扶用神，为吉"
                elif self.WUXING_KE.get(dong_wx) == yong_wx:
                    analysis += f"，克制用神，为忌"
            
            # 分析变爻
            if dong.bian_wuxing:
                analysis += f"，化{dong.bian_wuxing}"
                if dong.hui_tou_sheng:
                    analysis += "（回头生，力量持续）"
                elif dong.hui_tou_ke:
                    analysis += "（回头克，动而无功）"
            
            report.dong_yao_analysis.append(analysis)
    
    def _make_conclusion(self, report: AnalysisReport):
        """综合判断吉凶"""
        score = report.yong_shen_score
        
        # 根据评分判断吉凶
        if score >= 100:
            report.ji_xiong = "大吉"
            report.conclusion = "用神旺相有力，所求之事顺利可成"
        elif score >= 80:
            report.ji_xiong = "吉"
            report.conclusion = "用神得力，事情发展顺利，但需把握时机"
        elif score >= 60:
            report.ji_xiong = "中平"
            report.conclusion = "用神力量中等，事情可成但需付出努力"
        elif score >= 40:
            report.ji_xiong = "小凶"
            report.conclusion = "用神休囚，事情有阻碍，需谨慎行事"
        else:
            report.ji_xiong = "凶"
            report.conclusion = "用神衰弱无力，此事难成，宜暂缓或另谋他路"
        
        # 考虑动爻影响
        dong_yaos = [y for y in report.yaos if y.is_dong]
        ji_dong = [y for y in dong_yaos if y.is_yuan_shen]  # 原神动
        xiong_dong = [y for y in dong_yaos if y.is_ji_shen]  # 忌神动
        
        if ji_dong and not xiong_dong:
            report.conclusion += "，且有原神发动生扶，更添助力"
        elif xiong_dong and not ji_dong:
            report.conclusion += "，但有忌神发动克制，需防小人阻碍"
    
    def format_context(self, report: AnalysisReport) -> str:
        """将分析报告格式化为 LLM 上下文"""
        lines = []
        
        # ===== 第一维度：用神分析 =====
        lines.append("## 第一维度：用神分析（Target Selection）")
        lines.append(f"问事类型：{report.question_type}")
        
        yong_shen_config = self.YONG_SHEN_MAP.get(report.question_type, self.YONG_SHEN_MAP["其他"])
        lines.append(f"用神：{yong_shen_config['用神']}")
        lines.append(f"原神（生用神）：{yong_shen_config.get('原神', '无')}")
        lines.append(f"忌神（克用神）：{yong_shen_config.get('忌神', '无')}")
        lines.append(f"仇神（生忌神）：{yong_shen_config.get('仇神', '无')}")
        
        if report.yong_shen_pos:
            yong = report.yaos[report.yong_shen_pos - 1]
            lines.append(f"\n**用神所在**：第{report.yong_shen_pos}爻 {yong.tiangan}{yong.dizhi}{yong.wuxing}")
            lines.append(f"**用神状态**：{report.yong_shen_status}")
            lines.append(f"**用神评分**：{report.yong_shen_score}/100")
        
        # ===== 第二维度：旺衰分析 =====
        lines.append("\n## 第二维度：旺衰分析（Environmental Analysis）")
        lines.append(f"月建：{report.month_zhi}（{self.MONTH_WUXING.get(report.month_zhi, '土')}旺）")
        lines.append(f"日辰：{report.day_zhi}（{self.DIZHI_WUXING.get(report.day_zhi, '土')}）")
        
        lines.append("\n各爻旺衰评分：")
        for yao in report.yaos:
            pos_name = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][yao.position - 1]
            role = ""
            if yao.is_yong_shen:
                role = "【用神】"
            elif yao.is_yuan_shen:
                role = "【原神】"
            elif yao.is_ji_shen:
                role = "【忌神】"
            
            extras = []
            if yao.ri_sheng:
                extras.append("得日生")
            if yao.ri_ke:
                extras.append("受日克")
            if yao.yue_sheng:
                extras.append("得月生")
            if yao.yue_ke:
                extras.append("受月克")
            
            extra_str = f"（{', '.join(extras)}）" if extras else ""
            lines.append(f"- {pos_name} {yao.liuqin}{yao.tiangan}{yao.dizhi}{yao.wuxing} {yao.wang_shuai} 评分:{yao.score} {role}{extra_str}")
        
        # ===== 第三维度：动爻分析 =====
        lines.append("\n## 第三维度：动爻分析（Dynamic Interaction）")
        if report.dong_yao_analysis:
            for analysis in report.dong_yao_analysis:
                lines.append(f"- {analysis}")
        else:
            lines.append("- 六爻皆静")
        
        # ===== 第四维度：世应分析 =====
        lines.append("\n## 第四维度：世应分析（Subject vs Object）")
        shi_yao = report.yaos[report.shi_pos - 1] if report.shi_pos else None
        ying_yao = report.yaos[report.ying_pos - 1] if report.ying_pos else None
        
        if shi_yao:
            lines.append(f"世爻（自己）：第{report.shi_pos}爻 {shi_yao.liuqin}{shi_yao.tiangan}{shi_yao.dizhi} {shi_yao.wang_shuai} 评分:{shi_yao.score}")
        if ying_yao:
            lines.append(f"应爻（对方）：第{report.ying_pos}爻 {ying_yao.liuqin}{ying_yao.tiangan}{ying_yao.dizhi} {ying_yao.wang_shuai} 评分:{ying_yao.score}")
        lines.append(f"世应关系：{report.shi_ying_relation}")
        
        # ===== 第五维度：六神细节 =====
        lines.append("\n## 第五维度：六神细节（Flavor Details）")
        lines.append(f"日干：{report.ri_gan}")
        
        # 找出关键爻的六神
        for yao in report.yaos:
            if yao.is_yong_shen or yao.is_dong:
                pos_name = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][yao.position - 1]
                liushen_desc = self._get_liushen_meaning(yao.liushen)
                role = "用神" if yao.is_yong_shen else "动爻"
                lines.append(f"- {pos_name}（{role}）临{yao.liushen}：{liushen_desc}")
        
        # ===== 综合判断 =====
        lines.append("\n## 综合判断")
        lines.append(f"**吉凶**：{report.ji_xiong}")
        lines.append(f"**断语**：{report.conclusion}")
        
        return "\n".join(lines)
    
    def _get_liushen_meaning(self, liushen: str) -> str:
        """获取六神的简要含义"""
        meanings = {
            "青龙": "主喜庆、高贵、正当、左方",
            "朱雀": "主口舌、文书、信息、争吵",
            "勾陈": "主迟缓、田土、阻滞、官司",
            "螣蛇": "主惊恐、怪异、变化、暗中",
            "白虎": "主凶猛、血光、疾病、刚强",
            "玄武": "主暧昧、欺骗、私情、盗贼"
        }
        return meanings.get(liushen, "")
