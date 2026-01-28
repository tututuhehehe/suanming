"""
六爻算命模拟器 - 主程序入口
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import print as rprint

from core.divination_engine import DivinationEngine, YaoResult
from core.hexagram_analyzer import HexagramAnalyzer
from core.context_loader import ContextLoader
from core.llm_client import LLMClient
from core.storage import Storage
from core.najia_engine import NajiaEngine
from core.ganzhi import GanzhiCalculator
from core.analysis_engine import AnalysisEngine


console = Console()
storage = Storage()  # 初始化存储
ganzhi_calc = GanzhiCalculator()  # 干支计算器
analysis_engine = AnalysisEngine()  # 五维分析引擎


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    六 爻 算 命 模 拟 器                        ║
║                      v1.0 · 周易智慧                          ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def show_menu():
    """显示主菜单"""
    console.print("\n请选择操作：", style="bold")
    console.print("  [1] 🎴 开始算命")
    console.print("  [2] 📜 查看历史")
    console.print("  [3] ❓ 使用说明")
    console.print("  [4] ❌ 退出")
    return Prompt.ask("\n请输入选项", choices=["1", "2", "3", "4"], default="1")


def show_help():
    """显示使用说明"""
    help_text = """
[bold cyan]六爻算命模拟器使用说明[/bold cyan]

[yellow]【什么是六爻】[/yellow]
六爻是中国传统占卜方法之一，源自《周易》。通过投掷三枚铜钱六次，
得到六个爻位，组成一个卦象，再根据卦辞、爻辞解读吉凶。

[yellow]【起卦原理】[/yellow]
本程序使用随机数模拟铜钱投掷：
  · 老阴 (━ ━ ✕)：变爻，阴变阳
  · 少阳 (━━━)  ：静爻，阳不变
  · 少阴 (━ ━)  ：静爻，阴不变
  · 老阳 (━━━ ○)：变爻，阳变阴

[yellow]【问事类型】[/yellow]
  1. 事业 - 工作、职位、发展
  2. 财运 - 投资、收入、理财
  3. 感情 - 恋爱、婚姻、人际
  4. 健康 - 身体、疾病、养生
  5. 学业 - 考试、学习、进修
  6. 其他 - 综合类问题

[yellow]【注意事项】[/yellow]
  · 心诚则灵，起卦时请专注于您的问题
  · 解读仅供参考，不应作为重大决策的唯一依据
  · 同一问题不宜反复占卜
"""
    console.print(Panel(help_text, title="使用说明", border_style="cyan"))


def show_history():
    """显示历史记录"""
    console.print("\n[bold cyan]═══════════════════ 历史记录 ═══════════════════[/bold cyan]\n")
    
    # 获取统计信息
    stats = storage.get_statistics()
    console.print(f"共有 [cyan]{stats['total_count']}[/cyan] 条记录\n")
    
    if stats['total_count'] == 0:
        console.print("[dim]暂无历史记录[/dim]\n")
        return
    
    # 显示类型分布
    if stats['by_type']:
        console.print("按类型统计：", style="bold")
        for q_type, count in stats['by_type'].items():
            console.print(f"  {q_type}: {count} 条")
        console.print()
    
    # 获取最近记录
    records = storage.get_history(limit=10)
    
    # 创建表格显示
    table = Table(title="最近10条记录", show_lines=True)
    table.add_column("ID", style="dim", width=8)
    table.add_column("时间", width=16)
    table.add_column("问题", width=20)
    table.add_column("类型", width=6)
    table.add_column("本卦", width=10)
    table.add_column("变卦", width=10)
    
    for record in records:
        created_at = record['created_at'][:16].replace('T', ' ')
        question = record['question'][:18] + "..." if len(record['question']) > 18 else record['question']
        bian_gua = record['bian_gua'] if record['bian_gua'] else "-"
        
        table.add_row(
            record['id'],
            created_at,
            question,
            record['question_type'],
            record['ben_gua'],
            bian_gua
        )
    
    console.print(table)
    console.print()
    
    # 操作菜单
    console.print("[dim]操作：[1]查看详情  [2]导出JSON  [3]导出CSV  [4]清空记录  回车返回[/dim]")
    choice = Prompt.ask("请选择", default="")
    
    if choice == "1":
        record_id = Prompt.ask("输入ID查看详情")
        record = storage.get_record_by_id(record_id)
        if record:
            show_record_detail(record)
        else:
            console.print("[red]未找到该记录[/red]")
    elif choice == "2":
        export_history("json")
    elif choice == "3":
        export_history("csv")
    elif choice == "4":
        clear_history_confirm()


def export_history(format_type: str):
    """导出历史记录"""
    try:
        if format_type == "json":
            filepath = storage.export_to_json()
            console.print(f"\n[green]✓ 已导出为JSON文件[/green]")
        else:
            filepath = storage.export_to_csv()
            console.print(f"\n[green]✓ 已导出为CSV文件[/green]")
        
        console.print(f"[dim]文件路径: {filepath}[/dim]\n")
    except Exception as e:
        console.print(f"[red]导出失败: {e}[/red]")


def clear_history_confirm():
    """确认清空历史记录"""
    confirm = Prompt.ask("\n[bold red]⚠️ 确定要清空所有历史记录吗？此操作不可恢复！[/bold red]\n输入 'yes' 确认", default="no")
    if confirm.lower() == "yes":
        storage.clear_history()
        console.print("[green]✓ 历史记录已清空[/green]\n")
    else:
        console.print("[dim]已取消[/dim]\n")


def show_record_detail(record: dict):
    """显示单条记录详情"""
    console.print(f"\n[bold cyan]═══════════════════ 记录详情 ═══════════════════[/bold cyan]\n")
    
    console.print(f"[bold]ID[/bold]: {record['id']}")
    console.print(f"[bold]时间[/bold]: {record['created_at'][:19].replace('T', ' ')}")
    console.print(f"[bold]问题[/bold]: {record['question']}")
    console.print(f"[bold]类型[/bold]: {record['question_type']}")
    console.print(f"[bold]本卦[/bold]: {record['ben_gua']}")
    console.print(f"[bold]变卦[/bold]: {record['bian_gua'] or '无'}")
    console.print(f"[bold]变爻[/bold]: {record['changing_lines'] or '无'}")
    console.print(f"[bold]六爻[/bold]: {record['yao_sequence']}")
    
    console.print(f"\n[bold]解读[/bold]:")
    console.print(record['interpretation'])
    
    # 显示追问记录
    followups = record.get('followups', [])
    if followups:
        console.print(f"\n[bold cyan]───────────────── 追问记录 ({len(followups)}条) ─────────────────[/bold cyan]\n")
        for i, fu in enumerate(followups, 1):
            console.print(f"[bold]追问 {i}[/bold]: {fu['question']}")
            console.print(f"[dim]{fu['timestamp'][:19].replace('T', ' ')}[/dim]")
            console.print(f"[bold]回答[/bold]: {fu['answer']}\n")
    
    # 提供重新解读选项
    console.print("[dim]操作：[1]重新解读  回车返回[/dim]")
    choice = Prompt.ask("请选择", default="")
    
    if choice == "1":
        reinterpret_record(record)


def reinterpret_record(record: dict):
    """对历史记录进行重新解读"""
    console.print("\n[bold cyan]═══════════════════ 重新解读 ═══════════════════[/bold cyan]\n")
    
    try:
        # 初始化模块
        analyzer = HexagramAnalyzer()
        loader = ContextLoader()
        llm_client = LLMClient()
        
        # 从记录还原卦象
        yao_list = [
            YaoResult(position=i+1, value=v, yao_type="", is_yang=v in [7,9], is_changing=v in [6,9], symbol="")
            for i, v in enumerate(record['yao_sequence'])
        ]
        
        # 创建模拟的 DivinationResult
        class MockResult:
            def __init__(self, yao_list, changing_lines):
                self.yao_list = yao_list
                self.changing_lines = changing_lines
                from datetime import datetime
                self.timestamp = datetime.now()
        
        mock_result = MockResult(yao_list, record['changing_lines'])
        
        # 分析卦象
        analysis = analyzer.analyze(mock_result)
        
        # 加载知识上下文
        context = loader.load_context(analysis, record['question_type'])
        
        # 构建Prompt
        prompt = llm_client.build_prompt(
            question=record['question'],
            question_type=record['question_type'],
            hexagram_result=mock_result,
            analysis=analysis,
            context=context
        )
        
        # 生成新解读
        console.print("[bold yellow]───────────────── 新的解读 ─────────────────[/bold yellow]\n")
        
        interpretation_text = ""
        for text in llm_client.generate(prompt):
            console.print(text, end="")
            interpretation_text += text
        console.print("\n")
        
        console.print("[bold yellow]══════════════════════════════════════════════════[/bold yellow]\n")
        
        # 询问是否保存
        if Confirm.ask("是否将新解读保存为追问记录？", default=False):
            storage.save_followup(record['id'], "[重新解读]", interpretation_text)
            console.print("[green]✓ 已保存为追问记录[/green]\n")
        
    except Exception as e:
        console.print(f"[red]重新解读失败: {e}[/red]\n")


def animate_casting(yao_list, speed=0.3):
    """动画显示摇卦过程"""
    yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    coin_faces = ["🪙", "⚪"]  # 正面、反面
    
    console.print("\n[bold yellow]═══════════════════ 摇卦中 ═══════════════════[/bold yellow]\n")
    
    for i, yao in enumerate(yao_list):
        # 模拟三枚铜钱
        if yao.value == 6:  # 老阴：三反
            coins = "⚪ ⚪ ⚪"
        elif yao.value == 7:  # 少阳：两正一反
            coins = "🪙 🪙 ⚪"
        elif yao.value == 8:  # 少阴：一正两反
            coins = "🪙 ⚪ ⚪"
        else:  # 老阳：三正
            coins = "🪙 🪙 🪙"
        
        console.print(f"  {yao_names[i]}：{coins} → {yao.yao_type} {yao.symbol}")
        time.sleep(speed)
    
    console.print()


def display_hexagram_result(engine, result, analysis):
    """显示卦象结果"""
    console.print("[bold yellow]═══════════════════ 卦象结果 ═══════════════════[/bold yellow]\n")
    
    # 本卦和变卦并排显示
    ben_gua = analysis.ben_gua
    bian_gua = analysis.bian_gua
    
    if bian_gua:
        console.print(f"        [bold]本卦：{ben_gua.full_name} {ben_gua.symbol}[/bold]            [bold]变卦：{bian_gua.full_name} {bian_gua.symbol}[/bold]")
    else:
        console.print(f"        [bold]本卦：{ben_gua.full_name} {ben_gua.symbol}[/bold]            （无变卦）")
    
    console.print()
    
    # 显示六爻图形
    yao_display = engine.format_hexagram_display(result)
    console.print(yao_display)
    
    console.print()
    
    # 基本信息
    info_table = Table(show_header=False, box=None)
    info_table.add_column(style="cyan")
    info_table.add_column()
    info_table.add_row("卦宫", ben_gua.gong)
    info_table.add_row("世爻", f"第{ben_gua.shi_yao}爻")
    info_table.add_row("应爻", f"第{ben_gua.ying_yao}爻")
    if result.changing_lines:
        info_table.add_row("变爻", f"{', '.join(str(p) for p in result.changing_lines)}爻")
    
    console.print(info_table)
    console.print()


def display_paipan(result, analysis, ganzhi_time=None):
    """显示完整排盘"""
    console.print("[bold yellow]═══════════════════ 六爻排盘 ═══════════════════[/bold yellow]\n")
    
    # 显示干支时间
    if ganzhi_time:
        console.print(f"[cyan]起卦时间：{ganzhi_time}[/cyan]")
        console.print(f"[dim]日干：{ganzhi_time.day_gan}  月建：{ganzhi_time.month_zhi}[/dim]\n")
    
    try:
        najia_engine = NajiaEngine()
        
        # 获取日干、月建、日辰（用于六神和旺衰配置）
        ri_gan = ganzhi_time.day_gan if ganzhi_time else "甲"
        month_zhi = ganzhi_time.month_zhi if ganzhi_time else ""
        day_zhi = ganzhi_time.day_zhi if ganzhi_time else ""
        
        # 获取纳甲排盘
        paipan = najia_engine.paipan(
            yao_values=[yao.value for yao in result.yao_list],
            upper_trigram=analysis.ben_gua.upper,
            lower_trigram=analysis.ben_gua.lower,
            gong=analysis.ben_gua.gong,
            shi_yao=analysis.ben_gua.shi_yao,
            ying_yao=analysis.ben_gua.ying_yao,
            ben_gua_name=analysis.ben_gua.full_name,
            bian_gua_name=analysis.bian_gua.full_name if analysis.bian_gua else None,
            bian_upper=analysis.bian_gua.upper if analysis.bian_gua else None,
            bian_lower=analysis.bian_gua.lower if analysis.bian_gua else None,
            ri_gan=ri_gan,
            month_zhi=month_zhi,
            day_zhi=day_zhi
        )
        
        # 显示排盘表格
        console.print(f"[bold]{paipan.ben_gua_name}[/bold]  {paipan.gong} ({paipan.gong_wuxing})")
        if paipan.bian_gua_name:
            console.print(f"变卦：[bold]{paipan.bian_gua_name}[/bold]")
        console.print()
        
        # 创建排盘表格
        table = Table(show_lines=True, title_style="bold cyan")
        table.add_column("六神", style="magenta", width=6)
        table.add_column("爻位", style="dim", width=6)
        table.add_column("六亲", style="green", width=6)
        table.add_column("纳甲", style="cyan", width=10)
        table.add_column("旺衰", style="red", width=4)
        table.add_column("本卦", style="yellow", width=10)
        
        if paipan.bian_gua_yaos:
            table.add_column("变卦", style="yellow", width=10)
            table.add_column("纳甲", style="cyan", width=10)
            table.add_column("旺衰", style="red", width=4)
        
        # 从上爻到初爻显示
        pos_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
        for i in range(5, -1, -1):
            ben_yao = paipan.ben_gua_yaos[i]
            
            # 世应标记
            pos_label = pos_names[i]
            if ben_yao.shi_yao:
                pos_label += " 世"
            elif ben_yao.ying_yao:
                pos_label += " 应"
            
            # 本卦爻象
            ben_symbol = "━━━" if ben_yao.is_yang else "━ ━"
            if ben_yao.is_changing:
                ben_symbol += " ○" if ben_yao.is_yang else " ✕"
            
            # 纳甲信息
            najia_info = f"{ben_yao.tiangan}{ben_yao.dizhi}{ben_yao.wuxing}"
            
            # 旺衰
            wang_shuai = ben_yao.wang_shuai if ben_yao.wang_shuai else "-"
            
            if paipan.bian_gua_yaos:
                bian_yao = paipan.bian_gua_yaos[i]
                bian_symbol = "━━━" if bian_yao.is_yang else "━ ━"
                bian_najia = f"{bian_yao.tiangan}{bian_yao.dizhi}{bian_yao.wuxing}"
                bian_wang_shuai = bian_yao.wang_shuai if bian_yao.wang_shuai else "-"
                table.add_row(
                    ben_yao.liushen,
                    pos_label,
                    ben_yao.liuqin,
                    najia_info,
                    wang_shuai,
                    ben_symbol,
                    bian_symbol,
                    bian_najia,
                    bian_wang_shuai
                )
            else:
                table.add_row(
                    ben_yao.liushen,
                    pos_label,
                    ben_yao.liuqin,
                    najia_info,
                    wang_shuai,
                    ben_symbol
                )
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[dim]排盘显示失败: {e}[/dim]\n")


def run_divination():
    """执行算命流程"""
    console.print("\n[bold cyan]═══════════════════ 起卦准备 ═══════════════════[/bold cyan]\n")
    
    # 1. 输入问题
    question = Prompt.ask("[bold]请输入您想占卜的问题[/bold]")
    if not question.strip():
        console.print("[red]问题不能为空！[/red]")
        return
    
    # 2. 选择问事类型
    console.print("\n请选择问事类型：")
    console.print("  [1] 事业  [2] 财运  [3] 感情  [4] 健康  [5] 学业  [6] 其他")
    type_choice = Prompt.ask("请选择", choices=["1", "2", "3", "4", "5", "6"], default="6")
    question_types = {"1": "事业", "2": "财运", "3": "感情", "4": "健康", "5": "学业", "6": "其他"}
    question_type = question_types[type_choice]
    
    # 3. 确认起卦
    console.print(f"\n问题：[cyan]{question}[/cyan]")
    console.print(f"类型：[cyan]{question_type}[/cyan]")
    
    if not Confirm.ask("\n确认起卦？", default=True):
        console.print("[yellow]已取消[/yellow]")
        return
    
    # 4. 初始化各模块
    try:
        engine = DivinationEngine()
        analyzer = HexagramAnalyzer()
        loader = ContextLoader()
        llm_client = LLMClient()
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        console.print("[yellow]请检查是否已设置 DASHSCOPE_API_KEY 环境变量[/yellow]")
        return
    
    # 5. 起卦
    result = engine.cast_hexagram()
    
    # 5.5 计算干支时间
    ganzhi_time = ganzhi_calc.calculate(result.timestamp)
    
    # 6. 动画显示摇卦过程
    animate_casting(result.yao_list)
    
    # 7. 分析卦象
    try:
        analysis = analyzer.analyze(result)
    except Exception as e:
        console.print(f"[red]卦象分析失败: {e}[/red]")
        return
    
    # 8. 显示卦象结果
    display_hexagram_result(engine, result, analysis)
    
    # 8.5 显示完整排盘（含干支时间）
    display_paipan(result, analysis, ganzhi_time)
    
    # 9. 执行五维专业分析
    console.print("[bold cyan]═══════════════════ 五维分析 ═══════════════════[/bold cyan]\n")
    analysis_context = ""
    try:
        najia_engine = NajiaEngine()
        ri_gan = ganzhi_time.day_gan
        month_zhi = ganzhi_time.month_zhi
        day_zhi = ganzhi_time.day_zhi
        
        # 获取纳甲排盘
        paipan = najia_engine.paipan(
            yao_values=[yao.value for yao in result.yao_list],
            upper_trigram=analysis.ben_gua.upper,
            lower_trigram=analysis.ben_gua.lower,
            gong=analysis.ben_gua.gong,
            shi_yao=analysis.ben_gua.shi_yao,
            ying_yao=analysis.ben_gua.ying_yao,
            ben_gua_name=analysis.ben_gua.full_name,
            bian_gua_name=analysis.bian_gua.full_name if analysis.bian_gua else None,
            bian_upper=analysis.bian_gua.upper if analysis.bian_gua else None,
            bian_lower=analysis.bian_gua.lower if analysis.bian_gua else None,
            ri_gan=ri_gan,
            month_zhi=month_zhi,
            day_zhi=day_zhi
        )
        
        # 执行五维分析
        report = analysis_engine.analyze(
            question=question,
            question_type=question_type,
            paipan_result=paipan,
            month_zhi=month_zhi,
            day_zhi=day_zhi,
            ri_gan=ri_gan
        )
        
        # 格式化为上下文
        analysis_context = analysis_engine.format_context(report)
        
        # 显示关键分析结果
        console.print(f"[cyan]用神[/cyan]：{report.yaos[report.yong_shen_pos-1].liuqin if report.yong_shen_pos else '世爻'} "
                     f"（第{report.yong_shen_pos}爻） 评分：[bold]{report.yong_shen_score}[/bold]/100")
        console.print(f"[cyan]状态[/cyan]：{report.yong_shen_status}")
        console.print(f"[cyan]世应[/cyan]：{report.shi_ying_relation}")
        ji_color = "green" if "吉" in report.ji_xiong else "red"
        console.print(f"[cyan]吉凶[/cyan]：[bold {ji_color}]{report.ji_xiong}[/bold {ji_color}] - {report.conclusion}")
        console.print()
        
    except Exception as e:
        console.print(f"[dim]五维分析出错: {str(e).replace('[', '(').replace(']', ')')}[/dim]\n")
    
    # 10. 加载知识上下文
    context = loader.load_context(analysis, question_type)
    
    # 11. 构建Prompt并调用LLM（整合五维分析）
    prompt = llm_client.build_prompt(
        question=question,
        question_type=question_type,
        hexagram_result=result,
        analysis=analysis,
        context=context,
        analysis_context=analysis_context
    )
    
    # 12. 流式输出解读
    console.print("[bold yellow]═══════════════════ 大师解读 ═══════════════════[/bold yellow]\n")
    
    interpretation_text = ""
    try:
        for text in llm_client.generate(prompt):
            console.print(text, end="")
            interpretation_text += text
        console.print("\n")
    except Exception as e:
        console.print(f"\n[red]解读生成失败: {e}[/red]")
    
    console.print("[bold yellow]══════════════════════════════════════════════════[/bold yellow]\n")
    
    # 13. 保存历史记录
    record_id = None
    if interpretation_text:
        try:
            record_id = storage.save_record(
                question=question,
                question_type=question_type,
                yao_sequence=[yao.value for yao in result.yao_list],
                ben_gua=analysis.ben_gua.full_name,
                bian_gua=analysis.bian_gua.full_name if analysis.bian_gua else None,
                changing_lines=result.changing_lines,
                interpretation=interpretation_text
            )
            console.print(f"[dim]记录已保存 (ID: {record_id})[/dim]\n")
        except Exception as e:
            console.print(f"[dim]记录保存失败: {e}[/dim]\n")
    
    # 14. 初始化对话历史用于追问
    llm_client.clear_history()
    # 将初始提问和解读加入历史
    llm_client.add_to_history("user", prompt)
    llm_client.add_to_history("assistant", interpretation_text)
    
    # 15. 追问环节
    followup_loop(llm_client, record_id, analysis.ben_gua.full_name)
    
    # 16. 结束提示
    console.print("提示：解读仅供参考，不应作为重大决策的唯一依据。\n")


def followup_loop(llm_client: LLMClient, record_id: str, ben_gua: str):
    """追问对话循环"""
    followup_count = 0
    max_followups = 5  # 最多追问5次
    
    while followup_count < max_followups:
        console.print("[dim]💬 输入追问内容，或按回车结束[/dim]")
        followup = Prompt.ask("追问", default="")
        
        if not followup.strip():
            break
        
        followup_count += 1
        console.print()
        
        # 生成追问回答
        try:
            followup_response = ""
            for text in llm_client.generate_followup(followup):
                console.print(text, end="")
                followup_response += text
            console.print("\n")
            
            # 保存追问记录
            if record_id and followup_response:
                try:
                    storage.save_followup(record_id, followup, followup_response)
                except Exception:
                    pass  # 追问保存失败不影响主流程
                    
        except Exception as e:
            console.print(f"\n[red]追问回答失败: {e}[/red]\n")
            break
        
        if followup_count >= max_followups:
            console.print(f"[dim]已达最大追问次数 ({max_followups}次)[/dim]\n")


def main():
    """主函数"""
    print_banner()
    
    while True:
        choice = show_menu()
        
        if choice == "1":
            run_divination()
        elif choice == "2":
            show_history()
        elif choice == "3":
            show_help()
        elif choice == "4":
            console.print("\n[cyan]感谢使用，再见！[/cyan]\n")
            break
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]已退出[/yellow]")
        sys.exit(0)
