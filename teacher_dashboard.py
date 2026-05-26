import streamlit as st
import json
import os
import zipfile
import tempfile
import time
from pathlib import Path
from datetime import datetime
import sys
sys.path.append(os.path.dirname(__file__))
from src.agents.coordinator import Coordinator
from src.plagiarism.detector import PlagiarismDetector
import docker
import pandas as pd
import numpy as np
import plotly.express as px
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures

# ================= 页面配置 =================
st.set_page_config(page_title="码途智伴 - 教师管理平台", page_icon="📚", layout="wide")

# ================= 配置区域 =================
API_KEY = os.environ.get("ZHIPU_API_KEY", "")

@st.cache_resource
def get_coordinator():
    return Coordinator(API_KEY)

@st.cache_resource  
def get_plagiarism_detector():
    return PlagiarismDetector()

# 替换原来的
# coordinator = Coordinator(API_KEY)
# plagiarism_detector = PlagiarismDetector()

coordinator = get_coordinator()
plagiarism_detector = get_plagiarism_detector()

# ================= Docker 沙箱 =================
@st.cache_resource
def get_docker_client():
    try:
        return docker.from_env()
    except:
        return None

docker_client = get_docker_client()

def safe_execute_code(code, language="python", test_input="", timeout=5):
    if docker_client is None:
        return False, "Docker 未启动"
    
    from src.languages import LANGUAGE_PARSERS
    parser = LANGUAGE_PARSERS.get(language, LANGUAGE_PARSERS["python"])
    image = parser.get_sandbox_image()
    
    # 确保镜像已拉取（首次较慢）
    try:
        docker_client.images.get(image)
    except:
        docker_client.images.pull(image)
    
    # 确定文件名和命令
    if language == "java":
        filename = "Main.java"
    else:
        filename = "solution.py"
    command = parser.get_execution_command(filename)
    
    try:
        with tempfile.NamedTemporaryFile(suffix=f'.{language}', mode='w', delete=False) as f:
            f.write(code)
            tmp_path = f.name
            tmp_dir = os.path.dirname(tmp_path)
            tmp_filename = os.path.basename(tmp_path)
        
        # 对于 Java，文件需要重命名为 Main.java
        if language == "java":
            os.rename(tmp_path, os.path.join(tmp_dir, "Main.java"))
        
        result = docker_client.containers.run(
            image,
            command=command,
            volumes={tmp_dir: {'bind': '/code', 'mode': 'ro'}},
            working_dir='/code',
            mem_limit='256m',
            network_disabled=True,
            timeout=timeout,
            remove=True
        )
        os.unlink(tmp_path) if os.path.exists(tmp_path) else None
        return True, result.decode('utf-8', errors='ignore')
    except Exception as e:
        return False, f"执行失败: {str(e)}"

# ================= 会话状态 =================
if 'questions' not in st.session_state:
    st.session_state.questions = {}
if 'reports' not in st.session_state:
    st.session_state.reports = []

# ================= 批改函数 =================
def grade_single(question_desc, rubrics, student_code, student_name="", language="python"):
    result = coordinator.grade_workflow(student_code, question_desc, rubrics, language=language)
    report = result['evaluation']
    report['student_name'] = student_name
    report['code'] = student_code
    report['diagnosis'] = result.get('diagnosis', {})
    report['language'] = language  # ★ 保存语言信息
    return report

def batch_grade(question_desc, rubrics, zip_file, progress_bar=None, max_workers=5):
    reports = []
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            # 逐个解压，修复中文文件名
            for file_info in zf.infolist():
                # 尝试修复中文编码
                try:
                    filename = file_info.filename.encode('cp437').decode('gbk')
                except:
                    filename = file_info.filename.encode('cp437').decode('utf-8', errors='replace')
                
                # 跳过文件夹
                if file_info.is_dir():
                    continue
                
                # 只处理 .py 和 .java 文件
                if not (filename.endswith('.py') or filename.endswith('.java')):
                    continue
                
                # 提取到临时目录
                extracted_path = os.path.join(tmpdir, os.path.basename(filename))
                with zf.open(file_info) as source, open(extracted_path, 'wb') as target:
                    target.write(source.read())
        
        # 收集所有提取的文件
        py_files = list(Path(tmpdir).rglob("*.py")) + list(Path(tmpdir).rglob("*.java"))
        total = len(py_files)
        
        if total == 0:
            st.error("未找到任何 .py 或 .java 文件，请检查压缩包内容")
            return []
        
        tasks = []
        for py_file in py_files:
            student_name = py_file.stem
            code = py_file.read_text(encoding='utf-8', errors='ignore')
            lang = 'java' if py_file.suffix == '.java' or 'class Main' in code or 'public static' in code else 'python'
            tasks.append((student_name, code, lang))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_student = {
                executor.submit(grade_single, question_desc, rubrics, code, name, lang): name
                for name, code, lang in tasks
            }
            completed = 0
            for future in as_completed(future_to_student):
                try:
                    report = future.result()
                    reports.append(report)
                except Exception as e:
                    st.error(f"批改失败: {future_to_student[future]} - {e}")
                completed += 1
                if progress_bar:
                    progress_bar.progress(completed / total)
    
    return reports

# ================= 页面标题 =================
st.title("📚 码途智伴 — 教师管理平台 (竞赛版)")
tabs = st.tabs(["📝 题库管理", "📤 批量批改", "📊 成绩查看", "📈 数据驾驶舱", "🕵️ 抄袭检测", "🧠 知识图谱", "🧪 沙箱测试"])

# -------- 标签1: 题库管理 (不变) --------
with tabs[0]:
    st.header("📝 题库管理")
    with st.form("add_question"):
        col1, col2 = st.columns([1, 3])
        with col1:
            q_id = st.text_input("题目ID", placeholder="j1")
            q_lang = st.selectbox("语言", ["python", "java"])  # ← 新增
        with col2:
            q_title = st.text_input("题目名称", placeholder="找最大值 (Java)")
        q_desc = st.text_area("题目描述", height=100)
        q_rubrics = st.text_area("评分标准", height=80)
        q_template = st.text_area("代码模板（可选）", height=80, 
                                   placeholder="public class Main {\n    // 学生初始代码\n}")
        submitted = st.form_submit_button("✅ 添加/更新题目")
        if submitted and q_id:
            st.session_state.questions[q_id] = {
                "title": q_title,
                "description": q_desc,
                "rubrics": q_rubrics,
                "language": q_lang,
                "template": q_template
            }
            st.success(f"题目 {q_id} 已保存！")

# -------- 标签2: 批量批改 --------
with tabs[1]:
    st.header("📤 批量批改作业")
    if not st.session_state.questions:
        st.session_state.questions["q1"] = {
            "title": "找最大值",
            "description": "编写函数 find_max(numbers)...",
            "rubrics": "1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)"
        }
    q_options = {f"{qid}: {q['title']}": qid for qid, q in st.session_state.questions.items()}
    selected_q = st.selectbox("选择题目", list(q_options.keys()))
    selected_qid = q_options[selected_q]
    q_info = st.session_state.questions[selected_qid]
    
    upload_mode = st.radio("提交方式", ["📄 粘贴单个代码", "📦 上传作业包(.zip)"])
    if upload_mode == "📄 粘贴单个代码":
        student_code = st.text_area("学生代码", height=200)
        student_name = st.text_input("学生姓名", "测试学生")
        if st.button("🚀 批改此作业", type="primary"):
            with st.spinner("批改中..."):
                report = grade_single(q_info['description'], q_info['rubrics'], student_code, student_name)
                st.session_state.reports.append(report)
            st.success("完成！")
            st.json(report)
    else:
        uploaded_zip = st.file_uploader("上传zip", type="zip")
        if uploaded_zip and st.button("🚀 批量批改", type="primary"):
            progress_bar = st.progress(0)
            with st.spinner("批量批改中..."):
                reports = batch_grade(q_info['description'], q_info['rubrics'], uploaded_zip, progress_bar)
                st.session_state.reports.extend(reports)
            progress_bar.empty()
            st.success(f"✅ 处理 {len(reports)} 份")
            scores = [r['overall_score'] for r in reports if 'error' not in r]
            if scores:
                col1, col2, col3 = st.columns(3)
                col1.metric("平均分", f"{sum(scores)/len(scores):.1f}")
                col2.metric("最高分", max(scores))
                col3.metric("最低分", min(scores))

# -------- 标签3: 成绩查看 --------
with tabs[2]:
    st.header("📊 成绩查看")
    if st.session_state.reports:
        score_data = [{"序号": i+1, "学生": r.get('student_name','未知'), "总分": r.get('overall_score',0)} for i,r in enumerate(st.session_state.reports)]
        st.dataframe(score_data, use_container_width=True)
        scores = [r['overall_score'] for r in st.session_state.reports if 'error' not in r]
        if scores:
            fig = px.histogram(scores, nbins=10, title="成绩分布")
            st.plotly_chart(fig, use_container_width=True)
        selected_student = st.selectbox("选择学生", [r['student_name'] for r in st.session_state.reports])
        idx = [r['student_name'] for r in st.session_state.reports].index(selected_student)
        report = st.session_state.reports[idx]
        col1, col2 = st.columns(2)
    
        # ★ 根据题目语言选择代码高亮
        code_lang = report.get('language', 'python')
        col1.code(report.get('code',''), language=code_lang)
    
        col2.metric("总分", f"{report.get('overall_score',0)}/100")
        col2.write(report.get('summary',''))
        for d in report.get('deductions', []):
            st.warning(f"第{d['line']}行 {d['type']} (-{d['points_deducted']}): {d['suggestion']}")
        if st.button("导出JSON"):
            st.download_button("下载", json.dumps(st.session_state.reports, ensure_ascii=False, indent=2),
                               file_name="reports.json", mime="application/json")
    else:
        st.info("暂无批改记录")

# -------- 标签4: 数据驾驶舱 (NEW) --------
with tabs[3]:
    st.header("📈 教学数据驾驶舱")
    if not st.session_state.reports:
        st.info("请先完成批改，数据将在此展示")
    else:
        # 提取所有数据
        all_reports = [r for r in st.session_state.reports if 'error' not in r]
        if not all_reports:
            st.warning("无有效批改数据")
        else:
            scores = [r['overall_score'] for r in all_reports]
            students = [r['student_name'] for r in all_reports]
            
            # 指标卡片
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("平均分", f"{np.mean(scores):.1f}")
            col2.metric("中位数", f"{np.median(scores):.1f}")
            col3.metric("及格率", f"{sum(1 for s in scores if s>=60)/len(scores)*100:.1f}%")
            col4.metric("学困生(60以下)", f"{sum(1 for s in scores if s<60)}人")
            
            st.divider()
            
            # 成绩分布与错误分析
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("成绩分布")
                fig = px.histogram(scores, nbins=10, labels={'value': '分数', 'count': '人数'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col_right:
                st.subheader("错误类型频率")
                error_counter = Counter()
                for r in all_reports:
                    for d in r.get('deductions', []):
                        error_counter[d['type']] += 1
                if error_counter:
                    err_df = pd.DataFrame(error_counter.most_common(10), columns=['错误类型', '次数'])
                    fig = px.bar(err_df, x='错误类型', y='次数', color='次数')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("无错误数据")
            
            st.divider()
            
            # 薄弱知识点分布
            st.subheader("薄弱知识点分布")
            kp_counter = Counter()
            for r in all_reports:
                diag = r.get('diagnosis', {})
                for kp in diag.get('weak_knowledge_points', []):
                    kp_counter[kp] += 1
            if kp_counter:
                kp_df = pd.DataFrame(kp_counter.most_common(10), columns=['知识点', '出现次数'])
                fig = px.pie(kp_df, values='出现次数', names='知识点')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无知识点分析数据，请确保诊断智能体正常工作")
            
            st.divider()
            
            # 个人能力雷达图
            st.subheader("个人能力雷达图")
            selected = st.selectbox("选择学生查看能力雷达", students, key="radar_student")
            idx = students.index(selected)
            report = all_reports[idx]
            deductions = report.get('deductions', [])
            # 模拟维度得分（可根据扣分类型统计）
            dimensions = {
                '逻辑正确': 100,
                '边界处理': 100,
                '代码规范': 100,
                '算法效率': 100
            }
            for d in deductions:
                if '逻辑' in d['type'] or '初始化' in d['type'] or '返回值' in d['type']:
                    dimensions['逻辑正确'] -= d['points_deducted']
                elif '越界' in d['type'] or '空列表' in d['type'] or '边界' in d['type']:
                    dimensions['边界处理'] -= d['points_deducted']
                elif '规范' in d['type'] or '缩进' in d['type']:
                    dimensions['代码规范'] -= d['points_deducted']
                else:
                    dimensions['算法效率'] -= d['points_deducted']
            # 限制最低0
            for k in dimensions:
                dimensions[k] = max(0, dimensions[k])
            
            # 雷达图
            categories = list(dimensions.keys())
            values = list(dimensions.values())
            fig = px.line_polar(r=values, theta=categories, line_close=True, range_r=[0,100])
            st.plotly_chart(fig, use_container_width=True)

# -------- 标签5: 抄袭检测 (NEW) --------
with tabs[4]:
    st.header("🕵️ 学术诚信 - 代码相似度检测")
    if not st.session_state.reports:
        st.info("请先批改作业，然后检测抄袭")
    else:
        # 准备代码字典
        student_codes = {r['student_name']: r.get('code', '') for r in st.session_state.reports}
        if len(student_codes) < 2:
            st.warning("至少需要两份作业才能进行比对")
        else:
            if st.button("🔍 开始检测", type="primary"):
                with st.spinner("分析代码相似度..."):
                    result = plagiarism_detector.detect(student_codes)
                
                # 相似度矩阵热力图
                st.subheader("相似度矩阵")
                matrix = result['matrix']
                names = result['names']
                # 确保矩阵是方阵
                if len(matrix) == len(names):
                    fig = px.imshow(matrix, 
                                   labels=dict(x="学生", y="学生", color="相似度"),
                                   x=names, y=names, color_continuous_scale='Reds',
                                   zmin=0, zmax=1)
                    st.plotly_chart(fig, use_container_width=True)
                
                # 可疑组合
                st.subheader("可疑抄袭组合（相似度>70%）")
                suspicious = result.get('suspicious_pairs', [])
                if suspicious:
                    for pair in suspicious:
                        st.warning(f"⚠️ **{pair[0]}** 与 **{pair[1]}** 相似度: **{pair[2]:.2%}**")
                        # 显示两份代码对比
                        with st.expander("查看代码对比"):
                            col1, col2 = st.columns(2)
                            # 自动检测语言
                            code1 = student_codes[pair[0]]
                            code2 = student_codes[pair[1]]
                            lang1 = 'java' if 'class Main' in code1 or 'public static' in code1 else 'python'
                            lang2 = 'java' if 'class Main' in code2 or 'public static' in code2 else 'python'
                            col1.code(code1, language=lang1)
                            col2.code(code2, language=lang2)
                else:
                    st.success("未发现明显抄袭行为")

# -------- 标签6: 知识图谱 (NEW) --------
with tabs[5]:
    st.header("🧠 编程知识图谱")
    st.markdown("展示错误→知识点→前置知识的诊断链路")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Python 知识点")
        st.markdown("""
        """)
    with col2:
        st.subheader("Java 知识点")
        st.markdown("""
        """)
    
    st.divider()
    st.subheader("诊断链路示例")
    
    if st.session_state.reports:
        student_names = [r.get('student_name', f'学生{i}') for i, r in enumerate(st.session_state.reports)]
        selected = st.selectbox("选择学生查看诊断链路", student_names, key="kg_student")
        idx = student_names.index(selected)
        report = st.session_state.reports[idx]
        
        diag = report.get('diagnosis', {})
        if diag:
            weak_kps = diag.get('weak_knowledge_points', [])
            if weak_kps:
                st.markdown("**薄弱知识点:**")
                for kp in weak_kps:
                    st.warning(f"📌 {kp}")
            
            graph_diag = diag.get('graph_diagnosis', [])
            if graph_diag:
                st.markdown("**诊断链路:**")
                for gd in graph_diag:
                    err = gd.get('error', {})
                    st.error(f"❌ 错误: {err.get('name', '未知')} → {err.get('fix_hint', '')}")
                    chain = gd.get('chain', [])
                    for node in chain:
                        indent = "&nbsp;&nbsp;" * node.get('level', 0)
                        st.markdown(f"{indent}↳ {node.get('node', {}).get('name', '')} [{node.get('type', '')}]", unsafe_allow_html=True)
    else:
        st.info("暂无批改记录，提交作业后可查看诊断链路")



# -------- 标签7: 沙箱测试 (修复bug) --------
with tabs[6]:
    st.header("🧪 代码沙箱测试")
    if docker_client is None:
        st.error("Docker未启动")
    else:
        st.success("Docker已就绪")
    
    sandbox_lang = st.selectbox("语言", ["python", "java"])
    
    if sandbox_lang == "java":
        default_code = """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from 沙箱!");
    }
}"""
    else:
        default_code = "print('Hello from 沙箱!')\nprint(1+1)"
    
    test_code = st.text_area("测试代码", value=default_code, height=150)
    timeout = st.slider("超时(秒)", 1, 30, 5)
    
    if st.button("🧪 执行"):
        with st.spinner("沙箱执行中..."):
            success, output = safe_execute_code(test_code, language=sandbox_lang, timeout=timeout)
        if success:
            st.success("成功")
            st.code(output)
        else:
            st.error(output)
