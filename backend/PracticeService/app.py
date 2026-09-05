from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import datetime
import os
import json
import hashlib
import threading
import time
from bson import ObjectId

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MONGODB_AVAILABLE = False
db = None
practice_records_col = None
wrong_questions_col = None
user_stats_col = None
leaderboard_col = None

try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client['teacher_assistant']
    practice_records_col = db['practice_records']
    wrong_questions_col = db['wrong_questions']
    user_stats_col = db['user_stats']
    leaderboard_col = db['leaderboard']
    practice_records_col.create_index([("username", 1), ("created_at", -1)])
    wrong_questions_col.create_index([("username", 1), ("category", 1)])
    user_stats_col.create_index("username", unique=True)
    leaderboard_col.create_index([("total_score", -1)])
    MONGODB_AVAILABLE = True
    print("✅ PracticeService MongoDB 连接成功")
except Exception as e:
    print(f"PracticeService MongoDB 连接失败: {e}")
    print("📝 使用内存模式运行")

memory_practice_records = []
memory_wrong_questions = []
memory_user_stats = {}
memory_leaderboard = []

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'sk-e970b82e9c064d7f822ddc9e5618b13e')
DASHSCOPE_BASE_URL = os.environ.get('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
MODEL_NAME = os.environ.get('ALI_MODEL_NAME', 'qwen-plus')

LANGCHAIN_AVAILABLE = False
llm = None

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL,
        temperature=0.7,
        max_tokens=4096,
        timeout=30
    )
    LANGCHAIN_AVAILABLE = True
    print("✅ LangChain + 通义千问 初始化成功")
except Exception as e:
    print(f"⚠️ LangChain 初始化失败: {e}")
    print("📝 AI功能将使用降级模式")


def generate_quiz_fallback(topic, question_type, difficulty, count):
    templates = {
        "code_understanding": {
            1: [
                {"question": "以下Python代码的输出是什么？\n```python\nx = [1, 2, 3]\nprint(len(x))\n```", "answer": "3", "explanation": "len()函数返回列表的长度，x有3个元素，所以输出3。"},
                {"question": "以下代码的输出是什么？\n```python\na = 5\nb = 3\nprint(a + b)\n```", "answer": "8", "explanation": "a=5, b=3, a+b=8。"},
            ],
            2: [
                {"question": "以下代码的输出是什么？\n```python\ndef foo(x):\n    return x * 2\nprint(foo(5))\n```", "answer": "10", "explanation": "函数foo将输入乘以2，foo(5)返回10。"},
            ],
            3: [
                {"question": "以下代码的输出是什么？\n```python\nresult = [x**2 for x in range(5)]\nprint(result)\n```", "answer": "[0, 1, 4, 9, 16]", "explanation": "列表推导式对0-4每个数求平方。"},
            ],
            4: [
                {"question": "以下代码的输出是什么？\n```python\nimport numpy as np\narr = np.array([[1,2],[3,4]])\nprint(arr.sum(axis=0))\n```", "answer": "[4 6]", "explanation": "axis=0按列求和：1+3=4, 2+4=6。"},
            ],
            5: [
                {"question": "分析以下代码的时间复杂度：\n```python\ndef func(n):\n    result = 0\n    for i in range(n):\n        for j in range(i, n):\n            result += i * j\n    return result\n```", "answer": "O(n²)", "explanation": "双重循环，内层循环次数为n-i，总次数为n(n+1)/2，时间复杂度为O(n²)。"},
            ],
        },
        "choice": {
            1: [
                {"question": "Python中，以下哪个是正确的变量命名？", "options": ["2name", "_name", "class", "my-name"], "answer": "B", "explanation": "Python变量名可以以下划线开头，不能以数字开头，不能是关键字，不能含连字符。"},
            ],
            2: [
                {"question": "机器学习中，过拟合是指什么？", "options": ["模型在训练集上表现差", "模型在测试集上表现差", "模型过于简单", "训练数据太少"], "answer": "B", "explanation": "过拟合指模型在训练集上表现好但在测试集（新数据）上表现差，说明模型学到了训练数据中的噪声。"},
            ],
            3: [
                {"question": "卷积神经网络(CNN)中，池化层的主要作用是什么？", "options": ["增加特征图尺寸", "减少参数量和防止过拟合", "增加非线性", "加速训练收敛"], "answer": "B", "explanation": "池化层通过降采样减少特征图的空间尺寸，从而减少参数量和计算量，同时有助于防止过拟合。"},
            ],
            4: [
                {"question": "在反向传播算法中，梯度消失问题通常出现在哪种网络结构中？", "options": ["浅层网络", "深层网络", "单层网络", "宽网络"], "answer": "B", "explanation": "梯度消失问题在深层网络中尤为严重，因为梯度在反向传播过程中经过多层后会指数级衰减。"},
            ],
            5: [
                {"question": "以下哪种优化算法最适合处理稀疏梯度问题？", "options": ["SGD", "Momentum SGD", "Adam", "RMSprop"], "answer": "C", "explanation": "Adam优化器结合了Momentum和RMSprop的优点，对稀疏梯度有更好的适应性，因为它为每个参数维护独立的学习率。"},
            ],
        },
        "short_answer": {
            1: [
                {"question": "请简述什么是变量，并举例说明。", "scoring_criteria": "能正确定义变量(3分)，举例恰当(4分)，表述清晰(3分)", "reference_answer": "变量是程序中用于存储数据的命名容器。例如：age = 25，这里age就是一个变量，存储了数值25。"},
            ],
            2: [
                {"question": "请解释什么是算法，并说明算法的五个基本特征。", "scoring_criteria": "正确定义算法(2分)，列出5个特征各1.5分，表述清晰(0.5分)", "reference_answer": "算法是解决特定问题的一系列明确步骤。五个基本特征：有穷性、确定性、可行性、输入、输出。"},
            ],
            3: [
                {"question": "请解释深度学习中批归一化(Batch Normalization)的原理和作用。", "scoring_criteria": "原理描述(4分)，作用说明(4分)，数学表达(2分)", "reference_answer": "批归一化对每个mini-batch的数据进行归一化，使其均值接近0、方差接近1，然后通过可学习的缩放和偏移参数恢复表达能力。作用：加速训练收敛、缓解梯度问题、允许更大学习率、有一定正则化效果。"},
            ],
            4: [
                {"question": "请比较L1正则化和L2正则化的区别，并分析它们对模型参数的影响。", "scoring_criteria": "L1特点(3分)，L2特点(3分)，对比分析(2分)，对参数影响(2分)", "reference_answer": "L1正则化加入参数绝对值之和，倾向于产生稀疏解，可用于特征选择；L2正则化加入参数平方和，倾向于使参数均匀变小但不会为零。L1产生稀疏权重，L2产生平滑权重。"},
            ],
            5: [
                {"question": "请详细分析Transformer架构中自注意力机制的数学原理，并说明多头注意力相比单头注意力的优势。", "scoring_criteria": "自注意力数学原理(4分)，Q/K/V解释(2分)，多头优势(3分)，缩放因子说明(1分)", "reference_answer": "自注意力通过Query、Key、Value三个矩阵计算：Attention(Q,K,V)=softmax(QK^T/√d_k)V。多头注意力将Q、K、V投影到多个子空间分别计算注意力再拼接，优势：1)捕获不同子空间的注意力模式；2)增强模型表达能力；3)计算效率高，可并行。缩放因子√d_k防止点积过大导致softmax梯度消失。"},
            ],
        }
    }
    type_templates = templates.get(question_type, templates["choice"])
    diff_templates = type_templates.get(difficulty, type_templates.get(1, []))
    if not diff_templates:
        diff_templates = list(type_templates.values())[0] if type_templates else []
    result = []
    for i in range(min(count, len(diff_templates))):
        item = diff_templates[i].copy()
        item["id"] = f"fallback_{question_type}_{difficulty}_{i}"
        item["type"] = question_type
        item["difficulty"] = difficulty
        item["topic"] = topic
        result.append(item)
    while len(result) < count:
        idx = len(result) % max(len(diff_templates), 1)
        item = diff_templates[idx].copy() if diff_templates else {"question": "请描述人工智能的基本概念。", "answer": "人工智能是计算机科学的一个分支，旨在创建能够模拟人类智能行为的系统。"}
        item["id"] = f"fallback_{question_type}_{difficulty}_{len(result)}"
        item["type"] = question_type
        item["difficulty"] = difficulty
        item["topic"] = topic
        result.append(item)
    return result


def generate_quiz_with_ai(topic, question_type, difficulty, count):
    if not LANGCHAIN_AVAILABLE:
        return generate_quiz_fallback(topic, question_type, difficulty, count)

    difficulty_map = {1: "入门级", 2: "初级", 3: "中级", 4: "高级", 5: "专家级"}
    difficulty_desc = difficulty_map.get(difficulty, "中级")

    if question_type == "code_understanding":
        system_prompt = f"""你是一位AI教育专家，正在为手写数字识别模块出题。
请生成{count}道核心代码理解题，难度为{difficulty_desc}（{difficulty}/5级）。
主题：{topic}

要求：
1. 每道题包含一段Python/AI相关代码，要求分析代码功能或输出
2. 题目应围绕手写数字识别、CNN、PyTorch、图像处理等相关知识
3. 难度{difficulty}级：{"基础语法理解" if difficulty <= 2 else "算法原理分析" if difficulty <= 3 else "架构设计与优化" if difficulty == 4 else "前沿研究与创新应用"}

请严格按照以下JSON格式返回，不要包含其他内容：
[
  {{
    "id": "q_code_{{序号}}",
    "type": "code_understanding",
    "difficulty": {difficulty},
    "topic": "{topic}",
    "question": "题目内容（含代码）",
    "answer": "标准答案",
    "explanation": "详细解析"
  }}
]"""

    elif question_type == "choice":
        system_prompt = f"""你是一位AI教育专家，正在为手写数字识别模块出题。
请生成{count}道相关知识选择题，难度为{difficulty_desc}（{difficulty}/5级）。
主题：{topic}

要求：
1. 每道题4个选项（A/B/C/D），只有一个正确答案
2. 包含详细解析
3. 题目围绕手写数字识别、CNN、深度学习、PyTorch等

请严格按照以下JSON格式返回，不要包含其他内容：
[
  {{
    "id": "q_choice_{{序号}}",
    "type": "choice",
    "difficulty": {difficulty},
    "topic": "{topic}",
    "question": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "正确选项字母（A/B/C/D）",
    "explanation": "详细解析"
  }}
]"""

    else:
        system_prompt = f"""你是一位AI教育专家，正在为手写数字识别模块出题。
请生成{count}道简答题，难度为{difficulty_desc}（{difficulty}/5级）。
主题：{topic}

要求：
1. 支持文本输入作答
2. 提供评分标准（总分10分）
3. 提供参考答案
4. 题目围绕手写数字识别、CNN、深度学习等

请严格按照以下JSON格式返回，不要包含其他内容：
[
  {{
    "id": "q_short_{{序号}}",
    "type": "short_answer",
    "difficulty": {difficulty},
    "topic": "{topic}",
    "question": "题目内容",
    "scoring_criteria": "评分标准描述",
    "reference_answer": "参考答案"
  }}
]"""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"请生成{count}道{difficulty_desc}的{question_type}类型题目，主题为{topic}。直接返回JSON数组，不要包含markdown代码块标记。")
        ]
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        questions = json.loads(content)
        if not isinstance(questions, list):
            questions = [questions]
        for q in questions:
            q["difficulty"] = difficulty
            q["topic"] = topic
            if "type" not in q:
                q["type"] = question_type
        return questions[:count]
    except Exception as e:
        print(f"AI生成题目失败: {e}")
        return generate_quiz_fallback(topic, question_type, difficulty, count)


def grade_with_ai(question, user_answer, reference_answer, scoring_criteria):
    if not LANGCHAIN_AVAILABLE:
        score = 5
        if user_answer.strip():
            keywords = reference_answer.split("，") if reference_answer else []
            matched = sum(1 for kw in keywords if kw.strip() in user_answer)
            score = min(10, max(1, int(matched / max(len(keywords), 1) * 10)))
        return {
            "score": score,
            "max_score": 10,
            "comment": f"您的回答已收到。参考答案：{reference_answer}",
            "strengths": [],
            "weaknesses": ["建议参考标准答案完善回答"],
            "suggestions": ["请结合评分标准重新组织答案"]
        }

    try:
        system_prompt = f"""你是一位AI教育评分专家。请根据以下信息对学生的回答进行评分：

题目：{question}
评分标准：{scoring_criteria}
参考答案：{reference_answer}

学生回答：{user_answer}

请严格按照以下JSON格式返回评分结果，不要包含其他内容：
{{
  "score": 分数(0-10的整数),
  "max_score": 10,
  "comment": "总体评语",
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="请评分并返回JSON格式结果。")
        ]
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        result = json.loads(content)
        result["score"] = int(result.get("score", 5))
        result["max_score"] = 10
        return result
    except Exception as e:
        print(f"AI评分失败: {e}")
        return {
            "score": 5,
            "max_score": 10,
            "comment": "评分系统暂时不可用，已给予基础分",
            "strengths": [],
            "weaknesses": [],
            "suggestions": ["请参考标准答案进行自我评估"]
        }


def generate_report_with_ai(username, practice_data):
    if not LANGCHAIN_AVAILABLE:
        total = practice_data.get("total_questions", 0)
        correct = practice_data.get("correct_count", 0)
        score = practice_data.get("total_score", 0)
        return {
            "summary": f"本次练习共{total}题，答对{correct}题，得分{score}分。",
            "weak_points": ["建议加强基础知识练习"],
            "suggestions": ["多做练习题", "关注错题解析"],
            "knowledge_gaps": ["基础概念"],
            "next_steps": ["继续练习基础难度题目"]
        }

    try:
        system_prompt = f"""你是一位AI教育分析专家。请根据学生的练习数据生成详细的学习报告：

学生：{username}
练习数据：{json.dumps(practice_data, ensure_ascii=False, default=str)}

请分析学生的：
1. 整体表现总结
2. 薄弱知识点
3. 改进建议
4. 知识盲区
5. 下一步学习建议

请严格按照以下JSON格式返回，不要包含其他内容：
{{
  "summary": "整体表现总结",
  "weak_points": ["薄弱点1", "薄弱点2"],
  "suggestions": ["建议1", "建议2"],
  "knowledge_gaps": ["知识盲区1", "知识盲区2"],
  "next_steps": ["下一步建议1", "下一步建议2"]
}}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="请生成学习报告。")
        ]
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"AI报告生成失败: {e}")
        return {
            "summary": "报告生成暂时不可用",
            "weak_points": [],
            "suggestions": ["请继续练习"],
            "knowledge_gaps": [],
            "next_steps": ["继续学习"]
        }


def update_user_stats(username, practice_result):
    score_to_add = practice_result.get("score", 0)
    correct_count = practice_result.get("correct_count", 0)
    total_count = practice_result.get("total_count", 0)
    question_type = practice_result.get("question_type", "choice")
    difficulty = practice_result.get("difficulty", 1)

    now = datetime.datetime.utcnow()

    if MONGODB_AVAILABLE:
        stats = user_stats_col.find_one({"username": username})
        if not stats:
            stats = {
                "username": username,
                "total_score": 0,
                "total_practices": 0,
                "total_questions": 0,
                "total_correct": 0,
                "weekly_score": 0,
                "weekly_practices": 0,
                "last_week_reset": now,
                "dimensions": {
                    "algorithm_understanding": 0,
                    "code_implementation": 0,
                    "problem_analysis": 0,
                    "model_application": 0,
                    "innovative_thinking": 0
                },
                "type_stats": {
                    "code_understanding": {"count": 0, "correct": 0, "total_score": 0},
                    "choice": {"count": 0, "correct": 0, "total_score": 0},
                    "short_answer": {"count": 0, "correct": 0, "total_score": 0}
                },
                "difficulty_stats": {},
                "created_at": now,
                "updated_at": now
            }
            user_stats_col.insert_one(stats)

        week_start = now - datetime.timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        last_reset = stats.get("last_week_reset", now)
        if last_reset < week_start:
            stats["weekly_score"] = 0
            stats["weekly_practices"] = 0
            stats["last_week_reset"] = week_start

        stats["total_score"] += score_to_add
        stats["total_practices"] += 1
        stats["total_questions"] += total_count
        stats["total_correct"] += correct_count
        stats["weekly_score"] += score_to_add
        stats["weekly_practices"] += 1
        stats["updated_at"] = now

        type_key = question_type
        if type_key in stats["type_stats"]:
            stats["type_stats"][type_key]["count"] += total_count
            stats["type_stats"][type_key]["correct"] += correct_count
            stats["type_stats"][type_key]["total_score"] += score_to_add

        diff_key = str(difficulty)
        if diff_key not in stats["difficulty_stats"]:
            stats["difficulty_stats"][diff_key] = {"count": 0, "correct": 0}
        stats["difficulty_stats"][diff_key]["count"] += total_count
        stats["difficulty_stats"][diff_key]["correct"] += correct_count

        type_stats = stats["type_stats"]
        dims = stats["dimensions"]
        dims["algorithm_understanding"] = round(
            (type_stats.get("code_understanding", {}).get("correct", 0) /
             max(type_stats.get("code_understanding", {}).get("count", 1), 1)) * 100, 1
        )
        dims["code_implementation"] = round(
            (type_stats.get("code_understanding", {}).get("correct", 0) /
             max(type_stats.get("code_understanding", {}).get("count", 1), 1)) * 100 * 0.8 +
            (type_stats.get("short_answer", {}).get("correct", 0) /
             max(type_stats.get("short_answer", {}).get("count", 1), 1)) * 100 * 0.2, 1
        )
        dims["problem_analysis"] = round(
            (type_stats.get("short_answer", {}).get("correct", 0) /
             max(type_stats.get("short_answer", {}).get("count", 1), 1)) * 100 * 0.6 +
            (type_stats.get("choice", {}).get("correct", 0) /
             max(type_stats.get("choice", {}).get("count", 1), 1)) * 100 * 0.4, 1
        )
        dims["model_application"] = round(
            (correct_count / max(total_count, 1)) * 100 * 0.5 +
            dims["algorithm_understanding"] * 0.5, 1
        )
        high_diff_correct = sum(
            v["correct"] for k, v in stats["difficulty_stats"].items() if int(k) >= 4
        )
        high_diff_total = sum(
            v["count"] for k, v in stats["difficulty_stats"].items() if int(k) >= 4
        )
        dims["innovative_thinking"] = round(
            (high_diff_correct / max(high_diff_total, 1)) * 100, 1
        )

        for key in dims:
            dims[key] = min(100, max(0, dims[key]))

        user_stats_col.update_one(
            {"username": username},
            {"$set": stats}
        )

        leaderboard_col.update_one(
            {"username": username},
            {"$set": {
                "total_score": stats["total_score"],
                "weekly_score": stats["weekly_score"],
                "total_practices": stats["total_practices"],
                "updated_at": now
            }},
            upsert=True
        )
    else:
        if username not in memory_user_stats:
            memory_user_stats[username] = {
                "username": username,
                "total_score": 0,
                "total_practices": 0,
                "total_questions": 0,
                "total_correct": 0,
                "weekly_score": 0,
                "weekly_practices": 0,
                "dimensions": {
                    "algorithm_understanding": 0,
                    "code_implementation": 0,
                    "problem_analysis": 0,
                    "model_application": 0,
                    "innovative_thinking": 0
                },
                "type_stats": {
                    "code_understanding": {"count": 0, "correct": 0, "total_score": 0},
                    "choice": {"count": 0, "correct": 0, "total_score": 0},
                    "short_answer": {"count": 0, "correct": 0, "total_score": 0}
                }
            }
        s = memory_user_stats[username]
        s["total_score"] += score_to_add
        s["total_practices"] += 1
        s["total_questions"] += total_count
        s["total_correct"] += correct_count
        s["weekly_score"] += score_to_add
        s["weekly_practices"] += 1

        type_key = question_type
        if type_key in s["type_stats"]:
            s["type_stats"][type_key]["count"] += total_count
            s["type_stats"][type_key]["correct"] += correct_count
            s["type_stats"][type_key]["total_score"] += score_to_add

        ts = s["type_stats"]
        s["dimensions"]["algorithm_understanding"] = round(
            (ts["code_understanding"]["correct"] / max(ts["code_understanding"]["count"], 1)) * 100, 1)
        s["dimensions"]["code_implementation"] = round(
            (ts["code_understanding"]["correct"] / max(ts["code_understanding"]["count"], 1)) * 80 +
            (ts["short_answer"]["correct"] / max(ts["short_answer"]["count"], 1)) * 20, 1)
        s["dimensions"]["problem_analysis"] = round(
            (ts["short_answer"]["correct"] / max(ts["short_answer"]["count"], 1)) * 60 +
            (ts["choice"]["correct"] / max(ts["choice"]["count"], 1)) * 40, 1)
        s["dimensions"]["model_application"] = round(
            (correct_count / max(total_count, 1)) * 50 +
            s["dimensions"]["algorithm_understanding"] * 0.5, 1)
        s["dimensions"]["innovative_thinking"] = round(
            (correct_count / max(total_count, 1)) * 100 * 0.3 + s["dimensions"]["problem_analysis"] * 0.3, 1)

        for key in s["dimensions"]:
            s["dimensions"][key] = min(100, max(0, s["dimensions"][key]))

        memory_leaderboard.clear()
        for u, st in memory_user_stats.items():
            memory_leaderboard.append({
                "username": u,
                "total_score": st["total_score"],
                "weekly_score": st["weekly_score"],
                "total_practices": st["total_practices"]
            })
        memory_leaderboard.sort(key=lambda x: x["total_score"], reverse=True)


@app.route('/api/practice/generate', methods=['POST'])
def generate_quiz():
    try:
        data = request.get_json()
        topic = data.get('topic', '手写数字识别')
        question_type = data.get('type', 'choice')
        difficulty = int(data.get('difficulty', 3))
        count = int(data.get('count', 5))

        if question_type == 'code':
            question_type = 'code_understanding'

        if question_type == 'mixed':
            type_list = ['code_understanding', 'choice', 'short_answer']
            all_questions = []
            per_type = max(1, count // len(type_list))
            remaining = count
            for i, qt in enumerate(type_list):
                if i == len(type_list) - 1:
                    n = remaining
                else:
                    n = min(per_type, remaining)
                qs = generate_quiz_with_ai(topic, qt, difficulty, n)
                all_questions.extend(qs)
                remaining -= len(qs)
                if remaining <= 0:
                    break
            questions = all_questions[:count]
        else:
            if question_type not in ['code_understanding', 'choice', 'short_answer']:
                return jsonify({"success": False, "message": "不支持的题目类型"}), 400
            questions = generate_quiz_with_ai(topic, question_type, difficulty, count)

        if difficulty < 1 or difficulty > 5:
            return jsonify({"success": False, "message": "难度级别需在1-5之间"}), 400
        if count < 1 or count > 20:
            return jsonify({"success": False, "message": "题目数量需在1-20之间"}), 400

        return jsonify({
            "success": True,
            "data": {
                "questions": questions,
                "topic": topic,
                "type": question_type,
                "difficulty": difficulty,
                "count": len(questions)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"生成题目失败: {str(e)}"}), 500


@app.route('/api/practice/submit', methods=['POST'])
def submit_answers():
    try:
        data = request.get_json()
        username = data.get('username', 'anonymous')
        questions = data.get('questions', [])
        answers = data.get('answers', {})
        question_type = data.get('type', 'choice')

        if question_type == 'code':
            question_type = 'code_understanding'

        if not questions or not answers:
            return jsonify({"success": False, "message": "缺少题目或答案"}), 400

        results = []
        total_score = 0
        max_score = 0
        correct_count = 0
        wrong_questions = []

        for q in questions:
            qid = q.get('id', '')
            user_answer = answers.get(qid, '')
            q_type = q.get('type', question_type)
            is_correct = False
            score = 0
            q_max = 10
            grading_detail = {}

            if q_type == 'choice':
                correct_answer = q.get('answer', '').upper()
                user_answer_upper = str(user_answer).upper().strip()
                is_correct = user_answer_upper == correct_answer
                score = 10 if is_correct else 0
                grading_detail = {
                    "correct_answer": correct_answer,
                    "user_answer": user_answer_upper,
                    "is_correct": is_correct,
                    "explanation": q.get('explanation', '')
                }

            elif q_type == 'code_understanding':
                correct_answer = str(q.get('answer', '')).strip()
                user_answer_str = str(user_answer).strip()
                is_correct = user_answer_str.lower() == correct_answer.lower()
                score = 10 if is_correct else 0
                grading_detail = {
                    "correct_answer": correct_answer,
                    "user_answer": user_answer_str,
                    "is_correct": is_correct,
                    "explanation": q.get('explanation', '')
                }

            elif q_type == 'short_answer':
                ai_grading = grade_with_ai(
                    q.get('question', ''),
                    str(user_answer),
                    q.get('reference_answer', ''),
                    q.get('scoring_criteria', '')
                )
                score = ai_grading.get('score', 5)
                is_correct = score >= 6
                grading_detail = {
                    "score": score,
                    "max_score": ai_grading.get('max_score', 10),
                    "comment": ai_grading.get('comment', ''),
                    "strengths": ai_grading.get('strengths', []),
                    "weaknesses": ai_grading.get('weaknesses', []),
                    "suggestions": ai_grading.get('suggestions', []),
                    "reference_answer": q.get('reference_answer', ''),
                    "scoring_criteria": q.get('scoring_criteria', '')
                }

            if is_correct:
                correct_count += 1
            else:
                wrong_questions.append({
                    "question_id": qid,
                    "question": q.get('question', ''),
                    "type": q_type,
                    "difficulty": q.get('difficulty', 1),
                    "user_answer": str(user_answer),
                    "correct_answer": q.get('answer', q.get('reference_answer', '')),
                    "explanation": q.get('explanation', q.get('scoring_criteria', '')),
                    "category": q.get('topic', '手写数字识别')
                })

            total_score += score
            max_score += q_max
            results.append({
                "question_id": qid,
                "question": q.get('question', ''),
                "type": q_type,
                "difficulty": q.get('difficulty', 1),
                "user_answer": str(user_answer),
                "is_correct": is_correct,
                "score": score,
                "max_score": q_max,
                "grading": grading_detail
            })

        practice_record = {
            "username": username,
            "type": question_type,
            "difficulty": data.get('difficulty', 3),
            "topic": data.get('topic', '手写数字识别'),
            "total_questions": len(questions),
            "correct_count": correct_count,
            "total_score": total_score,
            "max_score": max_score,
            "accuracy": round(correct_count / max(len(questions), 1) * 100, 1),
            "results": results,
            "created_at": datetime.datetime.utcnow()
        }

        if MONGODB_AVAILABLE:
            practice_records_col.insert_one(practice_record)
            for wq in wrong_questions:
                wq["username"] = username
                wq["created_at"] = datetime.datetime.utcnow()
                wq["retry_count"] = 0
                wq["mastered"] = False
                wrong_questions_col.insert_one(wq)
        else:
            practice_record["_id"] = str(len(memory_practice_records))
            memory_practice_records.append(practice_record)
            for wq in wrong_questions:
                wq["username"] = username
                wq["created_at"] = datetime.datetime.utcnow()
                wq["retry_count"] = 0
                wq["mastered"] = False
                wq["_id"] = str(len(memory_wrong_questions))
                memory_wrong_questions.append(wq)

        update_user_stats(username, {
            "score": total_score,
            "correct_count": correct_count,
            "total_count": len(questions),
            "question_type": question_type,
            "difficulty": data.get('difficulty', 3)
        })

        practice_data_for_report = {
            "total_questions": len(questions),
            "correct_count": correct_count,
            "total_score": total_score,
            "max_score": max_score,
            "accuracy": round(correct_count / max(len(questions), 1) * 100, 1),
            "type": question_type,
            "results": results
        }
        report = generate_report_with_ai(username, practice_data_for_report)

        return jsonify({
            "success": True,
            "data": {
                "practice_id": str(practice_record.get("_id", "")),
                "total_score": total_score,
                "max_score": max_score,
                "correct_count": correct_count,
                "total_questions": len(questions),
                "accuracy": round(correct_count / max(len(questions), 1) * 100, 1),
                "results": results,
                "wrong_questions_count": len(wrong_questions),
                "report": report
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"提交答案失败: {str(e)}"}), 500


@app.route('/api/practice/history', methods=['GET'])
def get_practice_history():
    try:
        username = request.args.get('username', 'anonymous')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        skip = (page - 1) * page_size

        if MONGODB_AVAILABLE:
            total = practice_records_col.count_documents({"username": username})
            records = list(practice_records_col.find(
                {"username": username},
                {"results": 0}
            ).sort("created_at", -1).skip(skip).limit(page_size))
            for r in records:
                r["_id"] = str(r["_id"])
                r["created_at"] = r["created_at"].isoformat() if isinstance(r["created_at"], datetime.datetime) else str(r["created_at"])
        else:
            user_records = [r for r in memory_practice_records if r["username"] == username]
            total = len(user_records)
            records = user_records[skip:skip + page_size]
            for r in records:
                r["created_at"] = r["created_at"].isoformat() if isinstance(r.get("created_at"), datetime.datetime) else str(r.get("created_at", ""))

        return jsonify({
            "success": True,
            "data": {
                "records": records,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"获取历史记录失败: {str(e)}"}), 500


@app.route('/api/practice/history/<record_id>', methods=['GET'])
def get_practice_detail(record_id):
    try:
        if MONGODB_AVAILABLE:
            try:
                oid = ObjectId(record_id)
            except:
                oid = record_id
            record = practice_records_col.find_one({"_id": oid})
            if record:
                record["_id"] = str(record["_id"])
                record["created_at"] = record["created_at"].isoformat() if isinstance(record["created_at"], datetime.datetime) else str(record["created_at"])
        else:
            record = None
            for r in memory_practice_records:
                if str(r.get("_id", "")) == record_id:
                    record = r
                    break

        if not record:
            return jsonify({"success": False, "message": "记录不存在"}), 404

        return jsonify({"success": True, "data": record})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取记录详情失败: {str(e)}"}), 500


@app.route('/api/practice/wrong-questions', methods=['GET'])
def get_wrong_questions():
    try:
        username = request.args.get('username', 'anonymous')
        category = request.args.get('category', '')
        mastered = request.args.get('mastered', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        query = {"username": username}
        if category:
            query["category"] = category
        if mastered == 'true':
            query["mastered"] = True
        elif mastered == 'false':
            query["mastered"] = False

        if MONGODB_AVAILABLE:
            total = wrong_questions_col.count_documents(query)
            questions = list(wrong_questions_col.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size))
            for q in questions:
                q["_id"] = str(q["_id"])
                q["created_at"] = q["created_at"].isoformat() if isinstance(q["created_at"], datetime.datetime) else str(q["created_at"])
        else:
            filtered = [q for q in memory_wrong_questions if q["username"] == username]
            if category:
                filtered = [q for q in filtered if q.get("category") == category]
            if mastered == 'true':
                filtered = [q for q in filtered if q.get("mastered")]
            elif mastered == 'false':
                filtered = [q for q in filtered if not q.get("mastered")]
            total = len(filtered)
            questions = filtered[(page - 1) * page_size:page * page_size]
            for q in questions:
                q["created_at"] = q["created_at"].isoformat() if isinstance(q.get("created_at"), datetime.datetime) else str(q.get("created_at", ""))

        categories = set()
        if MONGODB_AVAILABLE:
            cats = wrong_questions_col.distinct("category", {"username": username})
            categories = set(cats)
        else:
            for q in memory_wrong_questions:
                if q["username"] == username:
                    categories.add(q.get("category", ""))

        return jsonify({
            "success": True,
            "data": {
                "questions": questions,
                "total": total,
                "page": page,
                "page_size": page_size,
                "categories": list(categories)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"获取错题失败: {str(e)}"}), 500


@app.route('/api/practice/wrong-questions/<question_id>/retry', methods=['POST'])
def retry_wrong_question(question_id):
    try:
        data = request.get_json()
        user_answer = data.get('answer', '')
        username = data.get('username', 'anonymous')

        if MONGODB_AVAILABLE:
            try:
                oid = ObjectId(question_id)
            except:
                oid = question_id
            wq = wrong_questions_col.find_one({"_id": oid, "username": username})
            if not wq:
                return jsonify({"success": False, "message": "错题不存在"}), 404

            is_correct = str(user_answer).strip().lower() == str(wq.get("correct_answer", "")).strip().lower()
            wrong_questions_col.update_one(
                {"_id": oid},
                {"$inc": {"retry_count": 1}, "$set": {"mastered": is_correct, "last_retry_at": datetime.datetime.utcnow()}}
            )
        else:
            wq = None
            for q in memory_wrong_questions:
                if str(q.get("_id", "")) == question_id and q["username"] == username:
                    wq = q
                    break
            if not wq:
                return jsonify({"success": False, "message": "错题不存在"}), 404
            is_correct = str(user_answer).strip().lower() == str(wq.get("correct_answer", "")).strip().lower()
            wq["retry_count"] = wq.get("retry_count", 0) + 1
            wq["mastered"] = is_correct

        return jsonify({
            "success": True,
            "data": {
                "is_correct": is_correct,
                "correct_answer": wq.get("correct_answer", ""),
                "explanation": wq.get("explanation", ""),
                "mastered": is_correct
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"重做错题失败: {str(e)}"}), 500


@app.route('/api/practice/wrong-questions/export', methods=['POST'])
def export_wrong_questions():
    try:
        data = request.get_json()
        username = data.get('username', 'anonymous')
        category = data.get('category', '')

        query = {"username": username}
        if category:
            query["category"] = category

        if MONGODB_AVAILABLE:
            questions = list(wrong_questions_col.find(query, {"_id": 0}).sort("created_at", -1))
            for q in questions:
                if "created_at" in q and isinstance(q["created_at"], datetime.datetime):
                    q["created_at"] = q["created_at"].isoformat()
        else:
            questions = [q for q in memory_wrong_questions if q["username"] == username]
            if category:
                questions = [q for q in questions if q.get("category") == category]

        export_data = {
            "export_time": datetime.datetime.utcnow().isoformat(),
            "username": username,
            "total_count": len(questions),
            "questions": questions
        }

        return jsonify({
            "success": True,
            "data": export_data
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"导出错题失败: {str(e)}"}), 500


@app.route('/api/practice/stats', methods=['GET'])
def get_user_stats():
    try:
        username = request.args.get('username', 'anonymous')

        if MONGODB_AVAILABLE:
            stats = user_stats_col.find_one({"username": username})
            if stats:
                stats["_id"] = str(stats["_id"])
                if "created_at" in stats and isinstance(stats["created_at"], datetime.datetime):
                    stats["created_at"] = stats["created_at"].isoformat()
                if "updated_at" in stats and isinstance(stats["updated_at"], datetime.datetime):
                    stats["updated_at"] = stats["updated_at"].isoformat()
        else:
            stats = memory_user_stats.get(username)

        if not stats:
            stats = {
                "username": username,
                "total_score": 0,
                "total_practices": 0,
                "total_questions": 0,
                "total_correct": 0,
                "weekly_score": 0,
                "weekly_practices": 0,
                "dimensions": {
                    "algorithm_understanding": 0,
                    "code_implementation": 0,
                    "problem_analysis": 0,
                    "model_application": 0,
                    "innovative_thinking": 0
                },
                "type_stats": {
                    "code_understanding": {"count": 0, "correct": 0, "total_score": 0},
                    "choice": {"count": 0, "correct": 0, "total_score": 0},
                    "short_answer": {"count": 0, "correct": 0, "total_score": 0}
                }
            }

        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取统计数据失败: {str(e)}"}), 500


@app.route('/api/practice/radar', methods=['GET'])
def get_radar_data():
    try:
        username = request.args.get('username', 'anonymous')

        if MONGODB_AVAILABLE:
            stats = user_stats_col.find_one({"username": username})
        else:
            stats = memory_user_stats.get(username)

        if not stats:
            stats = {"dimensions": {
                "algorithm_understanding": 0,
                "code_implementation": 0,
                "problem_analysis": 0,
                "model_application": 0,
                "innovative_thinking": 0
            }}

        dims = stats.get("dimensions", {})
        radar_data = {
            "indicators": [
                {"name": "算法理解能力", "max": 100},
                {"name": "代码实现能力", "max": 100},
                {"name": "问题分析能力", "max": 100},
                {"name": "模型应用能力", "max": 100},
                {"name": "创新思维能力", "max": 100}
            ],
            "values": [
                dims.get("algorithm_understanding", 0),
                dims.get("code_implementation", 0),
                dims.get("problem_analysis", 0),
                dims.get("model_application", 0),
                dims.get("innovative_thinking", 0)
            ]
        }

        return jsonify({"success": True, "data": radar_data})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取雷达图数据失败: {str(e)}"}), 500


@app.route('/api/practice/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        username = request.args.get('username', 'anonymous')
        board_type = request.args.get('type', 'total')
        limit = int(request.args.get('limit', 100))

        if board_type == 'weekly':
            limit = min(limit, 50)

        if MONGODB_AVAILABLE:
            if board_type == 'weekly':
                entries = list(leaderboard_col.find(
                    {"weekly_score": {"$gt": 0}},
                    {"_id": 0}
                ).sort("weekly_score", -1).limit(limit))
            else:
                entries = list(leaderboard_col.find(
                    {"total_score": {"$gt": 0}},
                    {"_id": 0}
                ).sort("total_score", -1).limit(limit))
        else:
            if board_type == 'weekly':
                entries = sorted(memory_leaderboard, key=lambda x: x.get("weekly_score", 0), reverse=True)[:limit]
                entries = [e for e in entries if e.get("weekly_score", 0) > 0]
            else:
                entries = sorted(memory_leaderboard, key=lambda x: x.get("total_score", 0), reverse=True)[:limit]
                entries = [e for e in entries if e.get("total_score", 0) > 0]

        user_rank = None
        user_score = 0
        prev_score = 0
        next_score = 0

        for i, entry in enumerate(entries):
            if entry["username"] == username:
                user_rank = i + 1
                user_score = entry.get("weekly_score" if board_type == "weekly" else "total_score", 0)
                if i > 0:
                    prev_score = entries[i - 1].get("weekly_score" if board_type == "weekly" else "total_score", 0)
                if i < len(entries) - 1:
                    next_score = entries[i + 1].get("weekly_score" if board_type == "weekly" else "total_score", 0)
                break

        if user_rank is None:
            if MONGODB_AVAILABLE:
                user_entry = leaderboard_col.find_one({"username": username})
                if user_entry:
                    score_field = "weekly_score" if board_type == "weekly" else "total_score"
                    user_score = user_entry.get(score_field, 0)
                    if board_type == 'total':
                        user_rank = leaderboard_col.count_documents({"total_score": {"$gt": user_score}}) + 1
                    else:
                        user_rank = leaderboard_col.count_documents({"weekly_score": {"$gt": user_score}}) + 1

        return jsonify({
            "success": True,
            "data": {
                "type": board_type,
                "entries": entries,
                "user_rank": user_rank,
                "user_score": user_score,
                "gap_to_prev": (prev_score - user_score) if user_rank and user_rank > 1 else 0,
                "gap_to_next": (user_score - next_score) if user_rank and user_rank < len(entries) else 0
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"获取排行榜失败: {str(e)}"}), 500


@app.route('/api/practice/leaderboard/refresh', methods=['POST'])
def refresh_leaderboard():
    try:
        if MONGODB_AVAILABLE:
            now = datetime.datetime.utcnow()
            week_start = now - datetime.timedelta(days=now.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            all_stats = list(user_stats_col.find({}))
            for stats in all_stats:
                last_reset = stats.get("last_week_reset", now)
                if last_reset < week_start:
                    user_stats_col.update_one(
                        {"username": stats["username"]},
                        {"$set": {"weekly_score": 0, "weekly_practices": 0, "last_week_reset": week_start}}
                    )
                    leaderboard_col.update_one(
                        {"username": stats["username"]},
                        {"$set": {"weekly_score": 0}}
                    )

        return jsonify({"success": True, "message": "排行榜已刷新"})
    except Exception as e:
        return jsonify({"success": False, "message": f"刷新排行榜失败: {str(e)}"}), 500


AGENT_SYSTEM_PROMPT = """你是"师小助"，一个专业的人工智能助教智能体，集成在人工智能通识教育平台中。你具备全面的人工智能专业知识体系，并可以查询系统数据辅助回答。

## 专业知识领域
1. 机器学习基础：监督学习、无监督学习、强化学习、特征工程、模型评估等
2. 深度学习：CNN、RNN、LSTM、Transformer、注意力机制、BERT、GPT等
3. 计算机视觉：图像分类、目标检测(YOLO/SSD)、图像分割、GAN等
4. 自然语言处理：文本分类、命名实体识别、机器翻译、文本生成、RAG等
5. 大语言模型：Prompt Engineering、微调技术、RLHF、模型部署与优化等
6. AI应用：推荐系统、语音识别、知识图谱、多模态AI等
7. AI工具与框架：PyTorch、TensorFlow、LangChain、Hugging Face等
8. AI伦理与安全：偏见与公平性、可解释性、隐私保护等

## 系统数据查询能力
你可以通过工具查询平台数据，包括：
- 用户学习统计（五维能力值、总分、练习次数等）
- 练习记录（历史成绩、正确率等）
- 排行榜数据
- 错题信息
- 系统概览（用户总数、练习总量等）

当用户询问学习进度、成绩分析、排名等与平台数据相关的问题时，请主动使用工具查询真实数据后再回答。

## 回答要求
- 用中文回答，语言简洁专业
- 适当使用代码示例辅助说明
- 对于复杂概念，分层次由浅入深解释
- 查询数据后，结合数据给出个性化分析和建议
- 如果不确定，坦诚说明而非编造"""

AGENT_FALLBACK_REPLIES = {
    "greeting": "你好！我是师小助，你的AI学习助手。你可以问我任何关于人工智能的问题，也可以查询你在平台上的学习数据。有什么我可以帮你的吗？",
    "error": "抱歉，我暂时无法回答这个问题，请稍后再试。",
}


def _agent_tool_query_user_stats(username):
    if not MONGODB_AVAILABLE:
        stats = memory_user_stats.get(username)
        if not stats:
            return json.dumps({"found": False, "message": f"未找到用户 {username} 的统计数据"}, ensure_ascii=False)
        return json.dumps({"found": True, "data": stats}, ensure_ascii=False, default=str)
    stats = user_stats_col.find_one({"username": username})
    if not stats:
        return json.dumps({"found": False, "message": f"未找到用户 {username} 的统计数据"}, ensure_ascii=False)
    stats["_id"] = str(stats["_id"])
    for k in ["created_at", "updated_at", "last_week_reset"]:
        if k in stats and isinstance(stats[k], datetime.datetime):
            stats[k] = stats[k].isoformat()
    return json.dumps({"found": True, "data": stats}, ensure_ascii=False, default=str)


def _agent_tool_query_practice_history(username, limit=5):
    limit = min(int(limit), 20)
    if not MONGODB_AVAILABLE:
        user_records = [r for r in memory_practice_records if r["username"] == username]
        records = user_records[:limit]
        for r in records:
            r["created_at"] = r["created_at"].isoformat() if isinstance(r.get("created_at"), datetime.datetime) else str(r.get("created_at", ""))
        return json.dumps({"records": records, "total": len(user_records)}, ensure_ascii=False, default=str)
    records = list(practice_records_col.find(
        {"username": username},
        {"results": 0}
    ).sort("created_at", -1).limit(limit))
    for r in records:
        r["_id"] = str(r["_id"])
        r["created_at"] = r["created_at"].isoformat() if isinstance(r["created_at"], datetime.datetime) else str(r["created_at"])
    total = practice_records_col.count_documents({"username": username})
    return json.dumps({"records": records, "total": total}, ensure_ascii=False, default=str)


def _agent_tool_query_leaderboard(board_type="total"):
    if not MONGODB_AVAILABLE:
        entries = sorted(memory_leaderboard, key=lambda x: x.get("total_score", 0), reverse=True)[:20]
        return json.dumps({"entries": entries}, ensure_ascii=False, default=str)
    if board_type == "weekly":
        entries = list(leaderboard_col.find({"weekly_score": {"$gt": 0}}, {"_id": 0}).sort("weekly_score", -1).limit(20))
    else:
        entries = list(leaderboard_col.find({"total_score": {"$gt": 0}}, {"_id": 0}).sort("total_score", -1).limit(20))
    return json.dumps({"entries": entries}, ensure_ascii=False, default=str)


def _agent_tool_query_wrong_questions(username, limit=10):
    limit = min(int(limit), 20)
    if not MONGODB_AVAILABLE:
        filtered = [q for q in memory_wrong_questions if q["username"] == username and not q.get("mastered")]
        questions = filtered[:limit]
        for q in questions:
            q["created_at"] = q["created_at"].isoformat() if isinstance(q.get("created_at"), datetime.datetime) else str(q.get("created_at", ""))
        return json.dumps({"questions": questions, "total": len(filtered)}, ensure_ascii=False, default=str)
    questions = list(wrong_questions_col.find(
        {"username": username, "mastered": False}
    ).sort("created_at", -1).limit(limit))
    for q in questions:
        q["_id"] = str(q["_id"])
        q["created_at"] = q["created_at"].isoformat() if isinstance(q["created_at"], datetime.datetime) else str(q["created_at"])
    total = wrong_questions_col.count_documents({"username": username, "mastered": False})
    return json.dumps({"questions": questions, "total": total}, ensure_ascii=False, default=str)


def _agent_tool_query_system_overview():
    result = {}
    if MONGODB_AVAILABLE:
        try:
            result["total_users"] = db['users'].count_documents({})
            result["total_practice_records"] = practice_records_col.count_documents({})
            result["total_questions_answered"] = sum(r.get("total_questions", 0) for r in practice_records_col.find({}, {"total_questions": 1}))
            result["total_correct"] = sum(r.get("correct_count", 0) for r in practice_records_col.find({}, {"correct_count": 1}))
            result["avg_accuracy"] = round(
                sum(r.get("accuracy", 0) for r in practice_records_col.find({}, {"accuracy": 1})) /
                max(result["total_practice_records"], 1), 1
            )
            result["total_leaderboard_entries"] = leaderboard_col.count_documents({"total_score": {"$gt": 0}})
        except Exception as e:
            result["error"] = str(e)
    else:
        result["total_users"] = len(memory_user_stats)
        result["total_practice_records"] = len(memory_practice_records)
        result["total_questions_answered"] = sum(r.get("total_questions", 0) for r in memory_practice_records)
        result["total_correct"] = sum(r.get("correct_count", 0) for r in memory_practice_records)
        result["avg_accuracy"] = 0
    return json.dumps(result, ensure_ascii=False, default=str)


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_user_stats",
            "description": "查询指定用户的学习统计数据，包括五维能力值、总分、练习次数、正确率等",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "要查询的用户名"}
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_practice_history",
            "description": "查询指定用户的练习历史记录，包括每次练习的成绩、正确率、题目类型等",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "要查询的用户名"},
                    "limit": {"type": "integer", "description": "返回记录数量，默认5，最多20", "default": 5}
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_leaderboard",
            "description": "查询排行榜数据，可查总榜或周榜",
            "parameters": {
                "type": "object",
                "properties": {
                    "board_type": {"type": "string", "enum": ["total", "weekly"], "description": "排行榜类型：total为总榜，weekly为周榜", "default": "total"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_wrong_questions",
            "description": "查询指定用户未掌握的错题列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "要查询的用户名"},
                    "limit": {"type": "integer", "description": "返回记录数量，默认10，最多20", "default": 10}
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_system_overview",
            "description": "查询系统整体概览数据，包括用户总数、练习总量、平均正确率等",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

AGENT_TOOL_MAP = {
    "query_user_stats": _agent_tool_query_user_stats,
    "query_practice_history": _agent_tool_query_practice_history,
    "query_leaderboard": _agent_tool_query_leaderboard,
    "query_wrong_questions": _agent_tool_query_wrong_questions,
    "query_system_overview": _agent_tool_query_system_overview,
}


def _execute_agent_tool(tool_name, tool_args):
    fn = AGENT_TOOL_MAP.get(tool_name)
    if not fn:
        return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)
    try:
        if tool_name == "query_user_stats":
            return fn(tool_args.get("username", ""))
        elif tool_name == "query_practice_history":
            return fn(tool_args.get("username", ""), tool_args.get("limit", 5))
        elif tool_name == "query_leaderboard":
            return fn(tool_args.get("board_type", "total"))
        elif tool_name == "query_wrong_questions":
            return fn(tool_args.get("username", ""), tool_args.get("limit", 10))
        elif tool_name == "query_system_overview":
            return fn()
        return json.dumps({"error": "工具参数错误"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False)


def _build_agent_messages(history, message):
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
    messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]
    for h in history[-10:]:
        role = h.get('role', 'user')
        content = h.get('content', '')
        if role == 'user':
            messages.append(HumanMessage(content=content))
        elif role == 'assistant':
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=message))
    return messages


@app.route('/api/agent/chat/stream', methods=['POST'])
def agent_chat_stream():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        history = data.get('history', [])

        if not message:
            return jsonify({"success": False, "message": "消息不能为空"}), 400

        if not LANGCHAIN_AVAILABLE:
            if any(kw in message for kw in ['你好', '嗨', 'hi', 'hello', '您好']):
                reply = AGENT_FALLBACK_REPLIES["greeting"]
            else:
                reply = AGENT_FALLBACK_REPLIES["error"]

            def fallback_stream():
                for char in reply:
                    yield f"data: {json.dumps({'type': 'content', 'content': char}, ensure_ascii=False)}\n\n"
                    time.sleep(0.02)
                yield "data: [DONE]\n\n"
            return Response(fallback_stream(), mimetype='text/event-stream',
                          headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

        messages = _build_agent_messages(history, message)
        llm_with_tools = llm.bind_tools(AGENT_TOOLS)

        def generate():
            max_tool_rounds = 3
            for _ in range(max_tool_rounds + 1):
                has_tool_call = False
                full_content = ""
                pending_tool_calls = {}

                for chunk in llm_with_tools.stream(messages):
                    if chunk.content:
                        full_content += chunk.content
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk.content}, ensure_ascii=False)}\n\n"

                    if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
                        for tc in chunk.tool_call_chunks:
                            tc_id = tc.get('id', '')
                            tc_name = tc.get('name', '')
                            tc_args = tc.get('args', '')
                            if tc_id not in pending_tool_calls:
                                pending_tool_calls[tc_id] = {'id': tc_id, 'name': tc_name, 'args': ''}
                            if tc_name:
                                pending_tool_calls[tc_id]['name'] = tc_name
                            if tc_args:
                                pending_tool_calls[tc_id]['args'] += tc_args

                for tc_id, tc_data in pending_tool_calls.items():
                    tool_name = tc_data['name']
                    if not tool_name:
                        continue
                    has_tool_call = True
                    try:
                        tool_args = json.loads(tc_data['args']) if tc_data['args'] else {}
                    except:
                        tool_args = {}

                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'args': tool_args}, ensure_ascii=False)}\n\n"

                    tool_result = _execute_agent_tool(tool_name, tool_args)
                    messages.append(AIMessage(content=full_content, tool_calls=[{'id': tc_id, 'name': tool_name, 'args': tool_args}]))
                    messages.append(ToolMessage(content=tool_result, tool_call_id=tc_id))

                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name}, ensure_ascii=False)}\n\n"

                if not has_tool_call:
                    break

            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype='text/event-stream',
                       headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    except Exception as e:
        def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'content': f'智能体回复失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return Response(error_stream(), mimetype='text/event-stream',
                       headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        history = data.get('history', [])

        if not message:
            return jsonify({"success": False, "message": "消息不能为空"}), 400

        if not LANGCHAIN_AVAILABLE:
            if any(kw in message for kw in ['你好', '嗨', 'hi', 'hello', '您好']):
                reply = AGENT_FALLBACK_REPLIES["greeting"]
            else:
                reply = AGENT_FALLBACK_REPLIES["error"]
            return jsonify({"success": True, "data": {"reply": reply}})

        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

        messages = _build_agent_messages(history, message)
        llm_with_tools = llm.bind_tools(AGENT_TOOLS)

        max_tool_rounds = 3
        for _ in range(max_tool_rounds + 1):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_name = tc.get('name', '')
                    tool_args = tc.get('args', {})
                    tool_result = _execute_agent_tool(tool_name, tool_args)
                    messages.append(ToolMessage(content=tool_result, tool_call_id=tc.get('id', tool_name)))
            else:
                break

        reply = response.content.strip() if response.content else ""
        return jsonify({"success": True, "data": {"reply": reply}})
    except Exception as e:
        return jsonify({"success": False, "message": f"智能体回复失败: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "mongodb": "connected" if MONGODB_AVAILABLE else "memory_mode",
        "langchain": "available" if LANGCHAIN_AVAILABLE else "fallback_mode",
        "model": MODEL_NAME,
        "message": "练习反馈服务运行中"
    })


if __name__ == '__main__':
    print("=" * 50)
    print("📝 练习反馈服务启动")
    print("=" * 50)
    print(f"   MongoDB: {'✅ 已连接' if MONGODB_AVAILABLE else '⚠️ 内存模式'}")
    print(f"   LangChain: {'✅ 已连接' if LANGCHAIN_AVAILABLE else '⚠️ 降级模式'}")
    print(f"   模型: {MODEL_NAME}")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5011)
