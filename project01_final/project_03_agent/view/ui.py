# 0.导包
import os
import mimetypes
import gradio as gr
from project_03_agent.logic import model_adapter as chat
from project_03_agent.data import (
    #--R04 导入prompt模块
    prompt,
)

# --基础变量
gradio_components = {}  

#--R00添加角色列表
roles = ["学者", "程序员", "医生","律师","教师","心理咨询师","艺术家"]

def creat_ui_layout():
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
                    file_types=['image', 'video'],
                    interactive=True
                )
                gradio_components["submit_btn"] = gr.Button("发送", scale=1, variant="primary")
                gradio_components["clear_btn"] = gr.ClearButton(
                    components=[gradio_components["chatbot"], gradio_components["bot_message"]],
                    value="清空",
                    scale=1,
                    variant="warning"
                )

        with gr.Column(scale=1):
            gradio_components["temperature"] = gr.Slider(
                minimum=0, maximum=1, value=0.7, step=0.1, label="Temperature", interactive=True
            )
            gradio_components["prompt_radio"] = gr.Radio(
                label='AI 角色', choices=roles, info='请选择您的AI角色'
            )
            gradio_components["prompt_text"] = gr.Textbox(
                label='角色系统提示词', visible=False, lines=10
            )

def bind_event_handler():
    def submit_check(message_dict):
        text = message_dict.get("text", "")
        files = message_dict.get("files", [])
        
        if not text.strip() and not files:
            raise gr.Error('请输入内容或上传图片/视频！')
            
        return gr.update(value='发送中...', interactive=False), gr.update(interactive=False)
    
    def add_text(user_message, history, temperature):
        if history is None:
            history = []
            
        text = user_message.get("text", "").strip()
        files = user_message.get("files", [])
        
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
                    content.append({"type": "file", "path": f_path})
            else:
                content.append({"type": "file", "path": f_path})
            
        if content:
            history.append({"role": "user", "content": content})
            
        return gr.MultimodalTextbox(value=None), history

    def prompt_radio_select(role_name):
        prompt_content = prompt.get_prompt(role_name)
        return gr.update(value=prompt_content, visible=True)

    gradio_components["submit_btn"].click(
        fn=submit_check,
        inputs=[gradio_components["bot_message"]],
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    ).success(
        fn=add_text,
        inputs=[gradio_components["bot_message"], gradio_components["chatbot"], gradio_components["temperature"]],
        outputs=[gradio_components["bot_message"], gradio_components["chatbot"]],
        queue=False
    ).then(
        fn=chat.bot,
        inputs=[
            gradio_components["chatbot"],
            gradio_components["temperature"],
            gradio_components["prompt_text"]
        ],
        outputs=[gradio_components["chatbot"]]
    ).then(
        fn=lambda: (gr.update(value="发送", interactive=True), gr.update(interactive=True)),
        inputs=None,
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    )
    
    gradio_components["bot_message"].submit(
        fn=submit_check,
        inputs=[gradio_components["bot_message"]],
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    ).success(
        fn=add_text,
        inputs=[gradio_components["bot_message"], gradio_components["chatbot"], gradio_components["temperature"]],
        outputs=[gradio_components["bot_message"], gradio_components["chatbot"]],
        queue=False
    ).then(
        fn=chat.bot,
        inputs=[gradio_components["chatbot"], gradio_components["temperature"], gradio_components["prompt_text"]],
        outputs=[gradio_components["chatbot"]]
    ).then(
        fn=lambda: (gr.update(value="发送", interactive=True), gr.update(interactive=True)),
        inputs=None,
        outputs=[gradio_components["submit_btn"], gradio_components["clear_btn"]]
    )

    gradio_components['prompt_radio'].change(
        fn=prompt_radio_select,
        inputs=[gradio_components['prompt_radio']],
        outputs=[gradio_components['prompt_text']]
    )

Tird_ui=gr.Blocks()

with Tird_ui:
    creat_ui_layout()
    bind_event_handler()