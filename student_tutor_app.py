import json
import os
import sys
# 将src目录加入路径，以便导入agents
sys.path.append(os.path.dirname(__file__))
from src.agents.coordinator import Coordinator
import gradio as gr

# ================= 配置区域 =================
API_KEY = os.environ.get("ZHIPU_API_KEY", "")
coordinator = Coordinator(API_KEY)

# ================= 题库 =================
QUESTION_BANK = {
    "q1": {
        "title": "找最大值",
        "description": "编写函数 find_max(numbers)，接收整数列表，返回最大值。不能使用内置 max() 函数。",
        "rubrics": "1. 逻辑正确(60分): 正确处理各种情况\n2. 代码规范(20分): 变量名清晰，有注释\n3. 边界处理(20分): 处理空列表和单元素列表"
    }
}

# ================= 批改功能（使用协调器） =================
def grade_student_code(student_code, selected_question="q1"):
    question = QUESTION_BANK[selected_question]
    result = coordinator.grade_workflow(student_code, question['description'], question['rubrics'])
    
    # 获取诊断摘要
    diag_summary = result.get('diagnosis', {}).get('summary', '无诊断')
    weak_kps = result.get('diagnosis', {}).get('weak_knowledge_points', [])
    graph_diag = result.get('diagnosis', {}).get('graph_diagnosis', [])
    
    # 在原有报告底部追加诊断信息
    formatted = result['final_report']
    formatted += f"\n\n---\n### 🔍 知识图谱诊断\n{diag_summary}\n"
    if weak_kps:
        formatted += f"\n**薄弱知识点**: {', '.join(weak_kps)}"
    if graph_diag:
        for diag in graph_diag[:1]:  # 只显示第一个错误
            formatted += f"\n\n**错误: {diag['error']['name']}**"
            for node in diag.get('chain', []):
                indent = "  " * node['level']
                formatted += f"\n{indent}- [{node['type']}] {node['node'].get('name', '')}"
    
    return formatted, json.dumps(result['evaluation'], ensure_ascii=False)

# ================= 追问功能（使用协调器） =================
def ask_followup(question, chat_history, grading_report_json):
    if not question.strip():
        return "", chat_history
    # 提取最近一次批改的代码（聊天历史中可能没有，这里可以从report_state获取）
    # 简化：用grading_report_json中的code字段，或从chat_history找
    # 这里我们假设在批改时已经存储了代码到state，现在暂时用空字符串，实际可扩展
    student_code = ""  # 可以在state中额外保存代码
    # 更好的做法：将代码也存入一个gr.State，这里为了方便，从评语中无法获取代码，因此追问可能缺代码上下文。
    # 但导师智能体主要依赖知识库和批改报告，代码可以传入空串
    answer = coordinator.tutoring_workflow(question, chat_history, student_code, grading_report_json)
    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": answer})
    return "", chat_history

# ================= Gradio 界面 =================
def create_ui():
    with gr.Blocks(title="码途智伴 - Python学习助手", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🤖 码途智伴 — Python 编程学伴 (多智能体版)")
        report_state = gr.State("{}")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📝 提交作业")
                question_dropdown = gr.Dropdown(
                    choices=[("找最大值", "q1")], value="q1", label="选择题目")
                code_input = gr.Code(
                    language="python", label="你的代码", lines=15,
                    value="# 在这里粘贴你的Python代码\n")
                submit_btn = gr.Button("🚀 提交批改", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 批改报告")
                report_output = gr.Markdown("等待提交代码...")
        
        gr.Markdown("---")
        gr.Markdown("### 💬 追问辅导")
        chatbot = gr.Chatbot(label="辅导对话", height=400,
                             placeholder="例如：为什么我的代码会索引越界？")
        msg_input = gr.Textbox(label="你的问题", placeholder="输入你的疑问...", lines=2)
        ask_btn = gr.Button("💬 追问", variant="secondary")
        clear_btn = gr.Button("🗑️ 清空对话")
        
        submit_btn.click(fn=grade_student_code, inputs=[code_input, question_dropdown],
                         outputs=[report_output, report_state])
        
        def ask_wrapper(question, history, report_json):
            return ask_followup(question, history, report_json)
        
        ask_btn.click(fn=ask_wrapper, inputs=[msg_input, chatbot, report_state],
                     outputs=[msg_input, chatbot])
        msg_input.submit(fn=ask_wrapper, inputs=[msg_input, chatbot, report_state],
                        outputs=[msg_input, chatbot])
        clear_btn.click(fn=lambda: ([],), outputs=[chatbot])
    
    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)