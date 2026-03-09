# 界面相关的代码：布局 + 事件绑定

# 0.导包
import os
import shutil
import uuid
os.environ["GRADIO_TEMP_DIR"] = os.path.join(os.getcwd(), "gradio_tmp")
IMG_CACHE_DIR = os.path.join(os.getcwd(), "static", "imgs")
os.makedirs(IMG_CACHE_DIR, exist_ok=True)
from random import choice
from sympy import content
import json
os.environ["GRADIO_TEMP_DIR"] = "/mnt/f/gradio_tmp"
import mimetypes
import gradio as gr
from project_03_multimodel.logic import model_adapter as chat
from data import (
    # --R04 导入prompt模块
    prompt,
)

# --基础变量
gradio_components = {}  # --1.声明一个保存界面组件的字典变量，其中：key：组件名称  value：组件对象
models = ["QianFan", "豆包", "Ernie"]  # --2.声明一个保存所有可选模型的列表变量

# --R00添加角色列表
roles = ["学者", "程序员", "医生","律师","教师","心理咨询师","艺术家",]

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE_PATH = os.path.join(APP_ROOT, "all_chat_histories.json")

def save_image_to_persist(tmp_img_path):
    """确保每次拍照生成唯一持久化路径"""
    if not tmp_img_path or not os.path.exists(tmp_img_path):
        return None
    # 生成唯一文件名（避免重复）
    img_suffix = os.path.splitext(tmp_img_path)[-1] or ".png"
    new_img_name = f"photo_{uuid.uuid4().hex}{img_suffix}"
    new_img_path = os.path.join(IMG_CACHE_DIR, new_img_name)
    # 强制覆盖旧文件（确保路径唯一）
    shutil.copy2(tmp_img_path, new_img_path)
    return new_img_path

def creat_ui_layout():
    """构建 UI 布局"""

    gr.Markdown("## AI Chatbot\n选择一个人工智障来聊天")
    with gr.Row():
        with gr.Column(scale=4):
            gradio_components["chatbot"] = gr.Chatbot(
                height=600,
            )

            with gr.Row():
                gradio_components["bot_message"] = gr.MultimodalTextbox(
                    show_label=False,
                    placeholder="输入文字或上传图片/视频...",
                    scale=5,
                    file_types=['image','video'],
                    interactive=True
                )
                gradio_components["submit_btn"] = gr.Button("发送", scale=1, variant="primary")
                gradio_components["clear_btn"] = gr.ClearButton(
                    components=[gradio_components["chatbot"], gradio_components["bot_message"]],
                    value="清空",
                    scale=1,
                    variant="warning"
                )
            with gr.Row():
                gradio_components["open_camera_btn"] = gr.Button("弹窗拍照", scale=1, variant="secondary")
        with gr.Column(scale=1):
            gradio_components["models"] = gr.Dropdown(
                choices=models, label="选取模型", interactive=True, value=models[0] if models else None
            )
            gradio_components["temperature"] = gr.Slider(
                minimum=0, maximum=1, value=0.7, step=0.1, label="Temperature", interactive=True
            )
            gradio_components["prompt_radio"] = gr.Radio(
                label='角色扮演', choices=roles, info='您可以选择AI的身份信息,让AI的回答更加专业化'
            )
            gradio_components["prompt_text"] = gr.Textbox(
                label='角色系统提示词', visible=False, lines=10
            )
            gradio_components["all_history"] = gr.State(value={})
            gr.Markdown("###历史记录")
            gradio_components["history_dropdown"] = gr.Dropdown(
                choices=[],
                label="点击恢复对话",
                interactive=True,
                allow_custom_value=False,
            )
            #独立的弹窗拍照功能
        with gr.Column(visible=False) as gradio_components["camera_modal"] :
            gr.Markdown("## 📷 独立拍照窗口（关闭自动传回图片）")
            gradio_components["big_camera"] = gr.Image(
                label="大窗口拍照", height=600, width=800, type="filepath", container=True
            )
            with gr.Row():
                gradio_components["close_modal_btn"] = gr.Button("关闭窗口", variant="stop")
        gr.HTML(
                """
                <a href="/next_page" style="text-decoration: none; color: white; background-color: #007BFF; padding: 10px 20px; border-radius: 5px; display: inline-block; margin-top: 10px;">
                    跳转至第二页
                </a>
                """
            )


def bind_event_handler():
    """绑定事件处理"""

    # 1. 辅助函数：模型切换
    def model_change(model_name):
        print(f"Model changed to: {model_name}")
        return None

    gradio_components["models"].change(
        fn=model_change,
        inputs=gradio_components["models"],
        outputs=None
    )

    # 2. 辅助函数：提交校验
    def submit_check(model_name, message_dict):
        # message_dict 是 MultimodalTextbox 的值: {'text': '...', 'files': [...]}
        if not model_name:
            raise gr.Error('请先选择一个模型！')

        # 检查是否有内容（文本或文件至少有一个）
        text = message_dict.get("text", "")
        files = message_dict.get("files", [])

        if not text.strip() and not files:
            raise gr.Error('请输入内容或上传图片！')

        # 校验通过，锁定按钮
        return gr.update(value='发送中...', interactive=False), gr.update(interactive=False)

    # 3. 核心函数：将用户输入添加到历史记录 (add_text)
    def add_text(user_message, history, temperature, all_history_dict):
        if history is None:
            history = []

        text = user_message.get("text", "").strip()
        files = user_message.get("files", [])

        # 1. 统一构建本次发送的内容列表
        content = []
        if text:
            content.append({"type": "text", "text": text})

        for f_path in files:
            mime_type, _ = mimetypes.guess_type(f_path)
            if mime_type:
                if mime_type.startswith('image'):
                    content.append({"type": "image", "path": f_path})
                elif mime_type.startswith('video'):
                    content.append({"type": "video", "path": f_path})
                else:
                    content.append({"type": "text", "text": f_path})
            else:
                content.append({"type": "text", "text": f_path})

            if content:
                history.append({"role": "user", "content": content})
            return gr.MultimodalTextbox(value=None), history, all_history_dict

        # 2. 如果有内容，更新 history 和 历史记录字典
        if content:
            # 只有在 history 为空时才生成标题，避免每回话一次就改一次标题
            if not history:
                title = text[:10] if text else "新对话"
                # 记录该标题对应的历史引用
                all_history_dict[title] = history

            history.append({"role": "user", "content": content})

        # 3. 返回时记得更新对应的 3 个组件状态
        return gr.MultimodalTextbox(value=None), history, all_history_dict

    # 4. 辅助函数：处理 Prompt 选择
    def prompt_radio_select(role_name):
        prompt_content = prompt.get_prompt(role_name)
        return gr.update(value=prompt_content, visible=True)
    #5.
    def open_camera_modal():
        # 打开弹窗时，先清空拍照组件的旧路径
        return gr.update(visible=True), gr.update(value=None)

    def close_camera_modal():
        # 关闭弹窗时，清空拍照组件的旧路径
        return gr.update(visible=False), gr.update(value=None)

    def big_camera_capture(img_path):
        if img_path and os.path.exists(img_path):
            # 1. 将临时图片持久化
            persist_img_path = save_image_to_persist(img_path)
            # 2. 更新输入框（传入持久化路径）
            input_update = gr.update(value={"text": "", "files": [persist_img_path]})
            # 3. 关闭弹窗 + 清空拍照组件的value（关键：避免下次复用旧路径）
            return input_update, gr.update(visible=False), gr.update(value=None)
        # 无有效图片时，重置状态
        return gr.update(), gr.update(visible=False), gr.update(value=None)

    # --- 事件链绑定 ---
    # 点击发送按钮
    gradio_components["submit_btn"].click(
        fn=submit_check,
        inputs=[gradio_components["models"], gradio_components["bot_message"]],
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    ).success(
        fn=add_text,
        inputs=[gradio_components["bot_message"], gradio_components["chatbot"], gradio_components["temperature"],
                gradio_components["all_history"]],
        outputs=[gradio_components["bot_message"], gradio_components["chatbot"], gradio_components["all_history"]],
        queue=False
    ).then(
        fn=chat.bot,
        inputs=[
            gradio_components["chatbot"],
            gradio_components["models"],
            gradio_components["temperature"],
            gradio_components["prompt_text"]
        ],
        outputs=[gradio_components["chatbot"]]
    ).then(
        # 然后恢复按钮状态
        fn=lambda: (gr.update(value="发送", interactive=True), gr.update(interactive=True)),
        inputs=None,
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    ).then(#保存至历史记录表里
        fn=save_to_history,
        inputs=[gradio_components["chatbot"], gradio_components["all_history"]],
        outputs=[gradio_components["all_history"], gradio_components["history_dropdown"]]
    )

    # 也可以绑定 Enter 键发送 (MultimodalTextbox 的 submit 事件)
    gradio_components["bot_message"].submit(
        fn=submit_check,
        inputs=[gradio_components["models"], gradio_components["bot_message"]],
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    ).success(
        fn=add_text,
        inputs=[gradio_components["bot_message"], gradio_components["chatbot"], gradio_components["temperature"],
                gradio_components["all_history"]],
        outputs=[gradio_components["bot_message"], gradio_components["chatbot"], gradio_components["all_history"]],
        queue=False
    ).then(
        fn=chat.bot,
        inputs=[gradio_components["chatbot"], gradio_components["models"], gradio_components["temperature"],
                gradio_components["prompt_text"]],
        outputs=[gradio_components["chatbot"]]
    ).then(
        fn=lambda: (gr.update(value="发送", interactive=True), gr.update(interactive=True)),
        inputs=None,
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    ).then(
        fn=save_to_history,
        inputs=[gradio_components["chatbot"], gradio_components["all_history"]],
        outputs=[gradio_components["all_history"], gradio_components["history_dropdown"]]
    )

    gradio_components['prompt_radio'].change(
        fn=prompt_radio_select,
        inputs=[gradio_components['prompt_radio']],
        outputs=[gradio_components['prompt_text']]
    )
    gradio_components["history_dropdown"].change(
        fn=load_history_session,
        inputs=[gradio_components["history_dropdown"], gradio_components["all_history"]],
        outputs=[gradio_components["chatbot"]]
    )
    # 打开拍照弹窗：同时清空拍照组件的旧路径
    gradio_components["open_camera_btn"].click(
        fn=open_camera_modal,
        outputs=[gradio_components["camera_modal"], gradio_components["big_camera"]]
    )
    # 关闭拍照弹窗：同时清空拍照组件的旧路径
    gradio_components["close_modal_btn"].click(
        fn=close_camera_modal,
        outputs=[gradio_components["camera_modal"], gradio_components["big_camera"]]
    )
    # 拍照完成：更新输入框 + 关闭弹窗 + 清空拍照组件
    gradio_components["big_camera"].change(
        fn=big_camera_capture,
        inputs=gradio_components["big_camera"],
        outputs=[gradio_components["bot_message"], gradio_components["camera_modal"], gradio_components["big_camera"]]
    )

def load_all_history_from_file():
    """程序启动时调用：从 JSON 文件加载所有历史记录"""
    if os.path.exists(HISTORY_FILE_PATH):
        with open(HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
            try:
                # 返回一个字典，键是标题，值是历史记录列表
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {HISTORY_FILE_PATH}, starting with empty history.")
                return {}
    # 如果文件不存在，则返回一个空字典
    return {}

def save_all_history_to_file(all_history_dict):
    """保存历史记录时调用：将所有历史记录保存到 JSON 文件"""
    with open(HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
        # 使用 ensure_ascii=False 以正确保存中文字符
        json.dump(all_history_dict, f, ensure_ascii=False, indent=4)

# --- Gradio UI 组件定义部分 ---

# 初始化 all_history State 时，从文件中加载已有的记录
initial_history_data = load_all_history_from_file()
gradio_components = {}
gradio_components["all_history"] = gr.State(value=initial_history_data)

# 根据加载的数据初始化下拉菜单选项
initial_choices = list(initial_history_data.keys())
gr.Markdown("###历史记录")
gradio_components["history_dropdown"] = gr.Dropdown(
    choices=initial_choices,
    label="点击恢复对话",
    interactive=True,
    allow_custom_value=False,
)


def save_to_history(history, all_history_dict):
    if not history:
        return all_history_dict, gr.update()
    first_msg = history[0]["content"]
    title = "新对话"
    for item in first_msg:
        if item["type"] == "text":
            title = item["text"][:10]
            break
    all_history_dict[title] = history
    new_choices_list=list(all_history_dict.keys())
    #3.CRITCAL 将整个字典保存到文件中
    save_all_history_to_file(all_history_dict)
    #4.更新Gradio UI
    return all_history_dict,gr.update(choices=new_choices_list)

def load_history_session(title, all_history_dict):
    print(f"尝试加载文件位置:{HISTORY_FILE_PATH}")
    if title in all_history_dict:
        return all_history_dict[title]
    return []

fist_ui=gr.Blocks()

with fist_ui:
    creat_ui_layout()
    bind_event_handler()
    all_history_dict= load_all_history_from_file()
    initial_choices = list(initial_history_data.keys())
