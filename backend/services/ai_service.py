import json
import re
import logging
from typing import List, Optional, Generator
from openai import OpenAI
from config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
)

SYSTEM_PROMPT = (
    "你是HTML5游戏生成器。严格遵循以下规则：\n"
    "1. 只输出纯HTML代码，输出会被直接放入iframe渲染\n"
    "2. 禁止输出任何非HTML内容：不要解释、不要注释说明、不要说\"这是你要的游戏\"等任何文字\n"
    "3. 禁止用```html或```包裹代码\n"
    "4. HTML必须完整独立，包含<style>和<script>，可直接在iframe中运行\n"
    "5. 代码紧凑、功能完整、界面美观\n"
    "6. 记住用户上一轮生成的游戏内容，支持修改、优化、微调\n"
    "违反以上规则会导致页面渲染崩溃。"
)

ANALYSIS_PROMPT = (
    "# 角色\n"
    "你是一个专业的游戏需求分析器。你的任务是根据用户输入，判断用户是想生成一个全新的游戏，还是对当前游戏添加功能或修改。\n"
    "# 分类标准\n"
    "## game（生成新游戏）\n"
    "用户明确提出了一个具体的游戏类型、玩法机制或游戏名称，意图是创建一个全新的游戏。\n"
    "典型特征：\n"
    "- 包含具体的游戏类型词（射击、赛车、格斗、益智、策略、模拟、RPG、动作、休闲等）\n"
    "- 包含具体的游戏名称（五子棋、俄罗斯方块、贪吃蛇、扫雷、2048、Flappy Bird等）\n"
    "- 包含创建性动词（做一个、生成、创建、开发、写一个、来一个、帮我做个等）\n"
    "- 描述了一个完整的游戏玩法或规则\n"
    "## feature（添加功能/修改）\n"
    "用户在当前游戏基础上要求增加功能、修改玩法、调整参数、美化界面或改变风格。\n"
    "典型特征：\n"
    "- 只包含风格/主题/颜色词（科技感、复古风、暗黑模式、红色主题、简约风格等）\n"
    "- 只包含功能词（增加计分、添加音效、优化性能、修复bug、调整速度等）\n"
    "- 只包含修改词（改一下、换个、调整、优化、改进、美化、继续等）\n"
    "- 只包含界面词（布局、按钮、颜色、字体、大小、位置等）\n"
    "# 判断规则（按优先级从高到低）\n"
    "1. 如果输入中包含具体的游戏类型或游戏名称 → game\n"
    "2. 如果输入中只有风格/主题/颜色/特效等修饰词，没有具体游戏类型 → feature\n"
    "3. 如果输入中只有功能/修改/优化相关词 → feature\n"
    "4. 如果输入模糊不清，无法确定 → feature\n"
    "# 输出\n"
    "只返回一个词：game 或 feature，不要返回其他任何内容"
)

SUMMARY_PROMPT = (
    "你是一个html游戏分析专家。分析以下游戏对话历史，生成一份详细的游戏摘要。\n"
    "摘要必须包含以下信息，以JSON格式返回（只返回JSON，不要其他文字）：\n"
    "{\n"
    '  "game_name": "游戏名称（简短，如 五子棋）",\n'
    '  "game_type": "游戏类型（如策略、射击、休闲等）",\n'
    '  "features": ["所有已实现的功能列表，如人机对战、双人对战、计分系统、音效、关卡等，尽可能详细"],\n'
    '  "customization": "个性化设置描述（如难度等级、颜色主题、速度调节、棋盘大小等）",\n'
    '  "tech_stack": "使用的技术（Canvas/DOM/CSS等）",\n'
    '  "ui_layout": "界面布局描述（如左侧棋盘右侧信息面板、顶部计分栏等）",\n'
    '  "interaction": "交互方式（如点击落子、拖拽、键盘控制等）",\n'
    '  "summary": "一句话概括这个游戏（不超过50字）"\n'
    "}\n"
    "注意：features列表必须尽可能完整，列出所有已实现的功能点，这对后续重新生成游戏至关重要。"
)


def judge_intent(user_input: str) -> str:
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": ANALYSIS_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.1,
            stream=False,
        )
        result = response.choices[0].message.content.strip().lower()
        return "game" if "game" in result else "feature"
    except Exception:
        return "feature"


def compress_game_summary(history: List[dict]) -> Optional[dict]:
    if not history:
        return None
    try:
        user_messages = [m for m in history if m.get("role") == "user"]
        if not user_messages:
            return None
        history_text = "\n".join(
            f"用户: {m['content']}" for m in user_messages
        )
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": f"请分析以下游戏对话历史，生成摘要：\n\n{history_text}"},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            stream=False,
        )
        result = response.choices[0].message.content.strip()

        match = re.search(r"\{.*\}", result, re.DOTALL)
        if match:
            result = match.group()

        return json.loads(result)
    except Exception as e:
        print(f"压缩摘要失败: {e}")
        return None


def build_messages(
    chat_history: List[dict],
    recalled_summary: Optional[str] = None,
    current_prompt: Optional[str] = None,
) -> List[dict]:
    if recalled_summary and current_prompt:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是HTML5游戏生成器。严格遵循以下规则：\n"
                    "1. 只输出纯HTML代码，输出会被直接放入iframe渲染\n"
                    "2. 禁止输出任何非HTML内容：不要解释、不要注释说明、不要说任何文字\n"
                    "3. 禁止用```html或```包裹代码\n"
                    "4. HTML必须完整独立，包含<style>和<script>，可直接在iframe中运行\n"
                    "5. 代码紧凑、功能完整、界面美观\n"
                    "6. 记住用户上一轮生成的游戏内容，支持修改、优化、微调\n"
                    "违反以上规则会导致页面渲染崩溃。\n\n"
                    f"用户要求生成：{current_prompt}\n"
                    "以下是该游戏之前版本的完整摘要（包含所有已实现的功能），"
                    "你必须保留摘要中列出的所有功能，并在其基础上根据用户最新需求进行增强或修改：\n"
                    f"{recalled_summary}"
                ),
            }
        ]
    elif recalled_summary:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是HTML5游戏生成器。严格遵循以下规则：\n"
                    "1. 只输出纯HTML代码，输出会被直接放入iframe渲染\n"
                    "2. 禁止输出任何非HTML内容：不要解释、不要注释说明、不要说任何文字\n"
                    "3. 禁止用```html或```包裹代码\n"
                    "4. HTML必须完整独立，包含<style>和<script>，可直接在iframe中运行\n"
                    "5. 代码紧凑、功能完整、界面美观\n"
                    "6. 记住用户上一轮生成的游戏内容，支持修改、优化、微调\n"
                    "违反以上规则会导致页面渲染崩溃。\n\n"
                    "根据以下历史游戏摘要重新生成完整HTML5游戏，必须实现摘要中列出的所有功能：\n"
                    f"{recalled_summary}"
                ),
            }
        ]
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history)
    if current_prompt and not recalled_summary:
        messages.append({"role": "user", "content": current_prompt})
    return messages


def stream_game_response(messages: List[dict]) -> Generator[str, None, None]:
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta



