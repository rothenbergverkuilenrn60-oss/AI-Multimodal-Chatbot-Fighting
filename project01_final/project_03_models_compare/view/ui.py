# 0.导包
import gradio as gr
from project_03_models_compare.logic.model_adapter import chat_adapter

# --基础变量
gradio_components = {}


def create_bot_caller(slider_component, adapter_instance):
    async def bot_caller(*histories):
        current_temp = slider_component.value
        async for result in adapter_instance.bot(*histories, temperature=current_temp):
            yield result

    return bot_caller


# ui view -layout
def creat_ui_layout():
    gr.Markdown(
        """
        ## AI Chatbot
        三个大模型并发聊天
        """
    )
    with gr.Row():
        with gr.Column(scale=4):
            with gr.Row():
                for i in range(3):
                    chatbot_key = f"chatbot_{i + 1}"

                    with gr.Group():
                        with gr.Row():
                            gradio_components[f"label_{i + 1}"] = gr.Markdown(
                                f"<small>聊天窗口{i + 1}</small>",
                                visible=True
                            )

                        gradio_components[chatbot_key] = gr.Chatbot(
                            height=400,
                            show_label=False,
                            scale=1
                        )

                        with gr.Row():
                            gr.Label("", visible=False, scale=1)
                            collapse_key = f"collapse_btn_{i + 1}"
                            gradio_components[collapse_key] = gr.Button(
                                value="−",
                                variant="secondary",
                                size="sm",
                                scale=0,
                                min_width=30,
                                visible=True
                            )

            gr.Markdown("### 单独与每个模型聊天")
            with gr.Row():
                for i in range(3):
                    with gr.Column():
                        input_key = f"bot_message_{i + 1}"
                        gradio_components[input_key] = gr.Textbox(
                            scale=4,
                            show_label=False,
                            placeholder=f"与聊天窗口{i + 1}单独聊天...",
                            interactive=True,
                        )
                        with gr.Row():
                            send_key = f"send_btn_{i + 1}"
                            gradio_components[send_key] = gr.Button(
                                scale=1,
                                variant="primary",
                                value='发送',
                            )
                            clear_key = f"clear_btn_{i + 1}"
                            gradio_components[clear_key] = gr.ClearButton(
                                scale=1,
                                components=[gradio_components[f"chatbot_{i + 1}"]]
                            )

            gr.Markdown("### 同时与三个模型聊天")
            with gr.Row():
                gradio_components["bot_message"] = gr.Textbox(
                    scale=4,
                    show_label=False,
                    placeholder="输入问题同时发送给三个模型：",
                    interactive=True,
                )
                gradio_components["submit_btn"] = gr.Button(
                    scale=1,
                    variant="primary",
                    value='发送给所有',
                )
                gradio_components["clear_btn"] = gr.ClearButton(
                    scale=1,
                    components=[gradio_components["chatbot_1"], gradio_components["chatbot_2"],
                                gradio_components["chatbot_3"]]
                )
        with gr.Column(scale=1):
            # 模型选择下拉菜单 - 只显示Ollama模型
            gradio_components['model_select_1'] = gr.Dropdown(
                choices=["Qwen3-VL", "Qwen3-Coder", "DeepSeek-R1", "GPT-OSS"],
                value="Qwen3-VL",
                label="聊天窗口1模型",
                interactive=True,
            )
            gradio_components['model_select_2'] = gr.Dropdown(
                choices=["Qwen3-VL", "Qwen3-Coder", "DeepSeek-R1", "GPT-OSS"],
                value="DeepSeek-R1",
                label="聊天窗口2模型",
                interactive=True,
            )
            gradio_components['model_select_3'] = gr.Dropdown(
                choices=["Qwen3-VL", "Qwen3-Coder", "DeepSeek-R1", "GPT-OSS"],
                value="GPT-OSS",
                label="聊天窗口3模型",
                interactive=True,
            )

            # 温度滑块
            gradio_components['temperature'] = gr.Slider(
                minimum=0.1,
                maximum=2.0,
                value=0.7,
                step=0.1,
                label="Temperature",
                interactive=True,
            )

            gr.Markdown("### 模型对抗模式")
            gradio_components['adversarial_mode'] = gr.Checkbox(
                label="开启模型对抗",
                value=False,
                interactive=True
            )
            gradio_components['adversarial_topic'] = gr.Textbox(
                label="对抗主题",
                placeholder="输入对抗的主题，如：'人工智能是否会伤害人类'",
                interactive=True
            )
            gradio_components['adversarial_rounds'] = gr.Slider(
                minimum=1,
                maximum=10,
                value=3,
                step=1,
                label="对抗轮数",
                interactive=True
            )
            gradio_components['start_adversarial'] = gr.Button(
                value="开始对抗",
                variant="primary",
                interactive=True
            )

            gradio_components['adversarial_result'] = gr.Label(
                value="对抗结果将显示在这里",
                label="对抗状态",
            )
            gr.HTML(
                """
                <a href="/main_page" style="text-decoration: none; color: white; background-color: #4CAF50; padding: 10px 20px; border-radius: 5px;">
                    返回首页
                </a>
                """
            )


def toggle_chatbot_visibility(button_value, is_visible):
    if is_visible:
        return "×", gr.update(visible=False), False
    else:
        return "−", gr.update(visible=True), True


def bind_event_handler():
    chatbots = [
        gradio_components["chatbot_1"],
        gradio_components["chatbot_2"],
        gradio_components["chatbot_3"]
    ]
    model_selects = [
        gradio_components["model_select_1"],
        gradio_components["model_select_2"],
        gradio_components["model_select_3"]
    ]
    for i in range(3):
        visible_key = f"visible_state_{i + 1}"
        gradio_components[visible_key] = gr.State(value=True)

    for i in range(3):
        chatbot = gradio_components[f"chatbot_{i + 1}"]
        collapse_btn = gradio_components[f"collapse_btn_{i + 1}"]
        visible_state = gradio_components[f"visible_state_{i + 1}"]

        collapse_btn.click(
            fn=toggle_chatbot_visibility,
            inputs=[collapse_btn, visible_state],
            outputs=[collapse_btn, chatbot, visible_state]
        )

    safe_bot_caller = create_bot_caller(
        gradio_components["temperature"],
        chat_adapter
    )

    actions = [
        gradio_components['bot_message'].submit,
        gradio_components['submit_btn'].click
    ]

    for action in actions:
        action(
            fn=submit_check,
            inputs=[gradio_components["bot_message"]],
            outputs=[
                gradio_components["submit_btn"],
                gradio_components["clear_btn"]
            ]
        ).success(
            fn=add_text,
            inputs=[
                gradio_components["bot_message"],
                *chatbots
            ],
            outputs=[
                gradio_components["bot_message"],
                *chatbots
            ],
            queue=True
        ).then(
            # fn=safe_bot_caller,
            fn=chat_adapter.bot,
            inputs=[
                *chatbots,
                *model_selects,
                gradio_components["temperature"]
            ],
            outputs=[
                *chatbots,
            ],
            queue=True
        ).success(
            fn=lambda: [
                gr.update(value="发送给所有", interactive=True),
                gr.update(interactive=True)
            ],
            inputs=None,
            outputs=[
                gradio_components["submit_btn"],
                gradio_components["clear_btn"]
            ]
        )

    for i in range(3):
        chatbot = gradio_components[f"chatbot_{i + 1}"]
        input_text = gradio_components[f"bot_message_{i + 1}"]
        send_btn = gradio_components[f"send_btn_{i + 1}"]
        model_select = gradio_components[f"model_select_{i + 1}"]

        send_btn.click(
            fn=lambda msg: gr.update(value='发送中...', interactive=False),
            inputs=[input_text],
            outputs=[send_btn]
        ).success(
            fn=add_text_single,
            inputs=[input_text, chatbot],
            outputs=[input_text, chatbot],
            queue=True
        ).then(
            fn=chat_single,
            inputs=[chatbot, model_select, gradio_components["temperature"]],
            outputs=[chatbot],
            queue=True
        ).success(
            fn=lambda: gr.update(value='发送', interactive=True),
            inputs=None,
            outputs=[send_btn]
        )

        input_text.submit(
            fn=lambda msg: gr.update(value='发送中...', interactive=False),
            inputs=[input_text],
            outputs=[send_btn]
        ).success(
            fn=add_text_single,
            inputs=[input_text, chatbot],
            outputs=[input_text, chatbot],
            queue=True
        ).then(
            fn=chat_single,
            inputs=[chatbot, model_select, gradio_components["temperature"]],
            outputs=[chatbot],
            queue=True
        ).success(
            fn=lambda: gr.update(value='发送', interactive=True),
            inputs=None,
            outputs=[send_btn]
        )

    gradio_components['start_adversarial'].click(
        fn=start_adversarial,
        inputs=[
            gradio_components['adversarial_topic'],
            gradio_components['adversarial_rounds'],
            gradio_components['temperature'],
            gradio_components['chatbot_1'],
            gradio_components['chatbot_2'],
            gradio_components['chatbot_3']
        ],
        outputs=[
            gradio_components['chatbot_1'],
            gradio_components['chatbot_2'],
            gradio_components['chatbot_3'],
            gradio_components['adversarial_result']
        ],
        queue=True
    )


def submit_check(message):
    if len(message) == 0:
        raise gr.Error('没有输入内容，请先输入内容。')
    return gr.update(
        value="发送",
        interactive=False,
    ), gr.update(
        interactive=False,
    )


async def add_text(message, h1, h2, h3):
    new_message = {'role': 'user', 'content': message}

    if h1 == None:
        h1 = []
    if h2 == None:
        h2 = []
    if h3 == None:
        h3 = []
    h1.append(new_message)
    h2.append(new_message)
    h3.append(new_message)
    return "", h1, h2, h3


async def add_text_single(message, history):
    if history is None:
        history = []
    new_message = {'role': 'user', 'content': message}
    history.append(new_message)
    return "", history


async def chat_single(history, model_select, temperature):
    # 确定要使用的模型
    model_name = model_select

    from project_03_models_compare.models.engine import OllamaEngine

    model_map = {
        "Qwen3-VL": "qwen3-vl:8b",
        "Qwen3-Coder": "danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth:UD-Q6_K_XL",
        "DeepSeek-R1": "deepseek-r1:1.5b",
        "GPT-OSS": "gpt-oss:20b"
    }

    ollama_model_name = model_map.get(model_name, "qwen3-vl:8b")
    model_instance = OllamaEngine(ollama_model_name)

    if not model_instance:
        history.append({"role": "assistant", "content": "模型选择失败"})
        yield history
        return

    async for updated_history in model_instance.chat(history, temperature=temperature):
        yield updated_history


# 模型对抗功能
async def start_adversarial(topic, rounds, temperature, history1, history2, history3):
    import os
    import random
    from project_03_models_compare.models.engine import OllamaEngine

    # 从.env获取模型或使用默认值
    model1_name = os.getenv("QWEN3VL", "qwen3-vl:8b")
    model2_name = os.getenv("GPTOSS", "gpt-oss:20b")
    model3_name = os.getenv("DEEPSEEK", "deepseek-r1:1.5b")

    model1 = OllamaEngine(model1_name)
    model2 = OllamaEngine(model2_name)
    model3 = OllamaEngine(model3_name)

    adv_history1 = history1.copy() if history1 else []
    adv_history2 = history2.copy() if history2 else []
    adv_history3 = history3.copy() if history3 else []

    # 开始对抗
    current_round = 0

    round_opinions = []

    while current_round < rounds:
        if current_round == 0:
            content_text = f"请围绕'{topic}'这个主题发表你的观点，作为开场发言，不超过200字。"
        else:
            prev_model3_opinion = adv_history3[-1]["content"] if adv_history3 else "前序观点"
            content_text = f"针对上一轮模型3的观点：'{prev_model3_opinion}'，请进行反驳并继续深化你的主题观点，不超过200字。"

        model1_prompt = [{"role": "user", "content": content_text}]

        temp_h1 = adv_history1[-5:].copy()
        temp_h1.extend(model1_prompt)

        async for updated_h1 in model1.chat(temp_h1, temperature=temperature, max_chars=200):
            adv_history1 = updated_h1
            yield adv_history1, adv_history2, adv_history3, f"对抗进行中... 第{current_round + 1}轮，模型1发言"

        round_opinions = []
        if adv_history1 and adv_history1[-1]["role"] == "assistant":
            round_opinions.append(adv_history1[-1]["content"])

        yield adv_history1, adv_history2, adv_history3, f"对抗进行中... 第{current_round + 1}轮，模型2发言"

        if round_opinions:
            model1_opinion = round_opinions[0]
            model2_prompt = [
                {"role": "user", "content": f"请反驳以下观点（不超过200字）：{model1_opinion}"}
            ]
        else:
            model2_prompt = [
                {"role": "user", "content": f"请围绕'{topic}'这个主题发表你的观点，不超过200字。"}
            ]

        temp_h2 = adv_history2[-5:].copy()
        temp_h2.extend(model2_prompt)

        async for updated_h2 in model2.chat(temp_h2, temperature=temperature, max_chars=200):
            adv_history2 = updated_h2
            yield adv_history1, adv_history2, adv_history3, f"对抗进行中... 第{current_round + 1}轮，模型2发言"

        if adv_history2 and adv_history2[-1]["role"] == "assistant":
            round_opinions.append(adv_history2[-1]["content"])

        yield adv_history1, adv_history2, adv_history3, f"对抗进行中... 第{current_round + 1}轮，模型3发言"

        if len(round_opinions) >= 2:
            model3_prompt = [
                {"role": "user", "content": f"请反驳以下观点（不超过200字）：{round_opinions[0]} {round_opinions[1]}"}
            ]
        elif len(round_opinions) == 1:
            model3_prompt = [
                {"role": "user", "content": f"请反驳以下观点（不超过200字）：{round_opinions[0]}"}
            ]
        else:
            model3_prompt = [
                {"role": "user", "content": f"请围绕'{topic}'这个主题发表你的观点，不超过200字。"}
            ]

        temp_h3 = adv_history3[-5:].copy()
        temp_h3.extend(model3_prompt)

        async for updated_h3 in model3.chat(temp_h3, temperature=temperature, max_chars=200):
            adv_history3 = updated_h3
            yield adv_history1, adv_history2, adv_history3, f"对抗进行中... 第{current_round + 1}轮，模型3发言"

        current_round += 1

    yield adv_history1, adv_history2, adv_history3, f"对抗结束！共进行了{rounds}轮辩论。"

#1.定义一个Gradio Blocks实例,这就是这个页面的根容器
second_ui=gr.Blocks()
#2.在这个实例的上下文管理中调用你的布局和绑定函数
with second_ui:
    creat_ui_layout()
    bind_event_handler()
