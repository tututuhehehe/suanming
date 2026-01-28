"""
LLM客户端 - 调用通义千问API生成解读
"""
import os
import json
from typing import Generator, List, Dict, Optional
from pathlib import Path

from openai import OpenAI

from .hexagram_analyzer import AnalysisResult
from .divination_engine import HexagramResult, DivinationEngine


class LLMClient:
    """LLM客户端"""
    
    SYSTEM_PROMPT = """你是一位专业的周易六爻预测大师，精通纳甲筮法。你的解卦遵循严格的六爻分析逻辑。

你解卦时必须按照以下五个维度进行分析：

1. **取用神**：根据问事类型确定主角爻（用神），这是分析的核心
2. **看旺衰**：根据月建、日辰判断用神的能量强弱
3. **看动爻**：分析动爻对用神的生克影响，以及回头生/克
4. **看世应**：判断求测人（世爻）与对方/目标（应爻）的关系
5. **看六神**：根据六神临爻来描绘事情的具体细节

输出格式要求（总字数400-600字）：

📌 **卦象总论**：本卦核心含义 + 变卦趋势（如有）

🎯 **用神分析**：
- 用神是什么、在哪一爻
- 用神旺衰状态如何（得令/失令、得日生/受日克）
- 用神的综合能量评估

⚡ **动态分析**（如有动爻）：
- 动爻对用神的影响（生扶/克制）
- 变爻是回头生还是回头克
- 事态发展趋势

👥 **世应关系**：
- 世爻（自己）的状态
- 应爻（对方/目标）的状态
- 双方关系如何

🔮 **吉凶断语**：直接给出判断（大吉/吉/中平/小凶/凶）+ 理由

💡 **具体建议**：
- 结合六神描绘事情的具体细节
- 给出可操作的建议

风格要求：
- 像一位经验丰富的老师傅，用通俗的语言解释专业的内容
- 断语要有依据，说清楚"因为XXX，所以XXX"
- 不要模棱两可，敢于给出明确判断"""

    FOLLOWUP_PROMPT = """你是一位周易六爻大师，用户正在针对之前的卦象解读进行追问。

请基于已给出的卦象信息和解读，回答用户的追问。回答要求：
- 简洁明了，控制在200字以内
- 紧扣卦象本身来回答
- 如追问涉及卦象未涵盖的内容，坦诚说明
- 可以深入解释某一爻或卦辞的含义"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self._init_client()
        self.conversation_history: List[Dict[str, str]] = []
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置"""
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        # 优先从配置文件读取API Key，其次从环境变量读取
        api_key = self.config["llm"].get("api_key")
        if not api_key:
            api_key_env = self.config["llm"].get("api_key_env", "DASHSCOPE_API_KEY")
            api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError("请在config.json中设置api_key，或设置环境变量DASHSCOPE_API_KEY")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.config["llm"]["api_base"]
        )
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def build_prompt(
        self, 
        question: str, 
        question_type: str,
        hexagram_result: HexagramResult,
        analysis: AnalysisResult,
        context: str,
        analysis_context: str = ""
    ) -> str:
        """
        构建完整的Prompt
        
        参数:
            analysis_context: 五维分析引擎生成的专业分析上下文
        """
        engine = DivinationEngine()
        
        # 构建卦象显示
        hexagram_display = engine.format_hexagram_display(hexagram_result)
        
        # 构建变爻描述
        if analysis.changing_lines:
            changing_desc = f"变爻位置：{', '.join(str(p) for p in analysis.changing_lines)}爻"
        else:
            changing_desc = "无变爻（六爻皆静）"
        
        # 变卦信息
        bian_gua_info = ""
        if analysis.bian_gua:
            bian_gua_info = f"\n### 变卦：{analysis.bian_gua.full_name} {analysis.bian_gua.symbol}"
        
        prompt = f"""## 求卦信息
**问题**：{question}
**问事类型**：{question_type}
**起卦时间**：{hexagram_result.timestamp.strftime('%Y年%m月%d日 %H:%M')}

## 卦象信息

### 本卦：{analysis.ben_gua.full_name} {analysis.ben_gua.symbol}

```
{hexagram_display}
```

{changing_desc}
{bian_gua_info}

## 专业六爻分析（五维分析法）

{analysis_context if analysis_context else "（无详细分析）"}

## 周易典籍参考

{context}

---

请根据以上**五维分析结果**和典籍参考，为求卦者解读此卦。

重点关注：
1. 用神的旺衰评分，这决定了事情的基本走向
2. 动爻对用神的影响，这决定了事情的变化趋势
3. 世应关系，这决定了双方的态势

针对问题「{question}」给出专业、有据可依的分析和建议。"""

        return prompt
    
    def generate(self, prompt: str) -> Generator[str, None, None]:
        """流式生成解读"""
        try:
            response = self.client.chat.completions.create(
                model=self.config["llm"]["model"],
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["llm"]["temperature"],
                max_tokens=self.config["llm"]["max_tokens"],
                stream=self.config["llm"]["stream"]
            )
            
            if self.config["llm"]["stream"]:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            yield f"\n\n[解读生成出错: {str(e)}]"
    
    def generate_full(self, prompt: str) -> str:
        """一次性生成完整解读"""
        return "".join(self.generate(prompt))
    
    def generate_followup(self, followup_question: str) -> Generator[str, None, None]:
        """生成追问回答（使用对话历史）"""
        # 将追问加入对话历史
        self.conversation_history.append({
            "role": "user",
            "content": followup_question
        })
        
        try:
            # 构建消息列表
            messages = [{"role": "system", "content": self.FOLLOWUP_PROMPT}]
            messages.extend(self.conversation_history)
            
            response = self.client.chat.completions.create(
                model=self.config["llm"]["model"],
                messages=messages,
                temperature=self.config["llm"]["temperature"],
                max_tokens=800,  # 追问回答限制较短
                stream=self.config["llm"]["stream"]
            )
            
            assistant_response = ""
            if self.config["llm"]["stream"]:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        assistant_response += content
                        yield content
            else:
                assistant_response = response.choices[0].message.content
                yield assistant_response
            
            # 将回答加入对话历史
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
                
        except Exception as e:
            yield f"\n\n[追问回答出错: {str(e)}]"
    
    def add_to_history(self, role: str, content: str):
        """将消息加入对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })


if __name__ == "__main__":
    # 测试
    client = LLMClient()
    
    from .divination_engine import DivinationEngine
    from .hexagram_analyzer import HexagramAnalyzer
    from .context_loader import ContextLoader
    
    engine = DivinationEngine()
    result = engine.cast_hexagram()
    
    analyzer = HexagramAnalyzer()
    analysis = analyzer.analyze(result)
    
    loader = ContextLoader()
    context = loader.load_context(analysis, "事业")
    
    prompt = client.build_prompt(
        question="最近工作会有变动吗？",
        question_type="事业",
        hexagram_result=result,
        analysis=analysis,
        context=context
    )
    
    print("生成解读中...\n")
    for text in client.generate(prompt):
        print(text, end="", flush=True)
    print()
