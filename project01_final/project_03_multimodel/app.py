import gradio as gr
from view import ui

# .env的查找和加载，应该在app.py中运行一次即可
from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())


# 完成界面组装
with gr.Blocks(title="AI Chatbot") as chat_interface:
    ui.creat_ui_layout()
    ui.bind_event_handler()


if __name__ == "__main__":
    # 启用排队机制
    chat_interface.queue()
    chat_interface.launch()