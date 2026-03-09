import gradio as gr
import os
from dotenv import load_dotenv
from pathlib import Path

# --- 环境加载逻辑 (保持不变) ---
BASE_DIR = Path(__file__).resolve().parent
try:
    load_dotenv(BASE_DIR / 'project_03_multimodel' / '.env')
    load_dotenv(BASE_DIR / 'project_03_models_compare' / '.env', override=True)
except FileNotFoundError:
    print("Warning: .env files not found in specified directories.")

# --- 导入你的 UI 组件 (保持不变) ---
try:
    from project_03_multimodel.view.ui import fist_ui
    from project_03_models_compare.view.ui import second_ui
    from project_03_agent.view.ui import Tird_ui
except ImportError as e:
    print(f"Error importing UI modules: {e}. Please check your project structure.")

# 直接执行 setTimeout 语句，而不是定义一个匿名函数
js_redirect = """
    // 获取当前路径，并确保去除末尾可能存在的斜杠
    var currentPath = window.location.pathname.replace(/\\/$/, "");
    var origin = window.location.origin;

    // 打印当前路径到控制台（方便你调试）
    console.log("Current path for redirect check:", currentPath);

    // 检查当前路径是否是根路径 "" (Gradio 本地默认) 或 "/welcome"
    if (currentPath === "" || currentPath.endsWith("/welcome")) {
        setTimeout(function() {
            // 5000 毫秒即为 5 秒
            window.location.href = origin + "/main_page";
        }, 5000); 
    }
"""

demo = gr.Blocks()

# --- 使用 gr.Navbar 手动定义导航栏 (保持不变) ---
with demo.route(name="欢迎页", path="welcome"):
    gr.Navbar(
        main_page_name="欢迎页",
        value=[
            ("主页面", "main_page"),
            ("下一页", "next_page"),
            ("Agent", "Tird_page"),
        ]
    )
    # --- 欢迎页的内容 ---
    gr.Markdown("# 🚀 欢迎使用全场景 AI 模型集成平台")
    gr.Markdown("""
    ### 🌟 产品核心亮点：
    - **极速体验**：响应时间缩短 50%，支持流式输出。
    - **智能分析**：内置自研与开源顶尖 AI 模型矩阵。

    ### 🤖 核心模型阵列：
    - **DeepSeek · R1 (1.5B)**：基于强化学习的轻量化推理战神。
    - **百度 · 千帆/文心一言**：企业级稳定服务。
    - **字节跳动 · 豆包**：极致响应速度。
    - **通义千问3.0 · Qwen3-VL**：强大的视觉语言模型,核心能力:图像分析、视频分析、文档解析等。
    - **OpenAI · GPT-OSS**：OpenAI发布的纯文本开放权重,核心能力:强大的逻辑推理、指令遵循和函数调用。
    ---
    *系统检测到环境已就绪，将在 **5 秒** 后自动跳转至功能区...*
    """)

with demo.route(name="主页面", path="main_page"):
    fist_ui.render()

with demo.route(name="下一页", path="next_page"):
    second_ui.render()

with demo.route(name="Agent", path="Tird_page"):
    Tird_ui.render()

if __name__ == "__main__":
    print(f"ERNIE_API_KEY loaded: {bool(os.getenv('ERNIE_API_KEY'))}")

    demo.launch(
        js=js_redirect,
        css=".gradio-auto-nav { background-color: #f5f5f5; padding: 10px; }"
    )
