import os,sys
import random
from project_03_agent.models.qianfan import QianfanLlmEngine
from project_03_agent.models.spark import SparkEngine
from project_03_agent.models.ernie import ErnieEngine

_engine_cache = {}  

def get_engine(model_name):
    if model_name in _engine_cache:
        return _engine_cache[model_name]
    
    engine = None
    if model_name == "QianFan":
        engine = QianfanLlmEngine()
    elif model_name == 'Spark':
        engine = SparkEngine()
    elif model_name == 'Ernie':
        engine = ErnieEngine()
    
    if engine:
        _engine_cache[model_name] = engine
    return engine

def bot(history, temperature, prompt_text):
    has_media = False
    
    if history and len(history) > 0:
        last_message = history[-1]
        if last_message["role"] == "user":
            content = last_message["content"]
            
            if isinstance(content, list):
                for item in content:
                    if item.get("type") in ["image", "video", "file"]:
                        has_media = True
                        break
    
    if has_media:
        model_name = "Ernie"
        print("智能体决策：检测到图片/视频，使用Ernie模型")
    else:
        model_name = random.choice(["Spark", "QianFan"])
        print(f"智能体决策：纯文本输入，随机选择{model_name}模型")
    
    engine = get_engine(model_name)
    
    if not engine:
        history.append({
            "role": "assistant", 
            "content": f"系统错误: 未找到模型引擎 {model_name}"
        })
        yield history
        return

    try:
        yield from engine.chat(    
            history=history,
            temperature=temperature,
            prompt_text=prompt_text
        )
    except Exception as e:
        print(f"Chat Error: {e}")
        history.append({
            "role": "assistant",
            "content": f"生成时发生异常: {str(e)}"
        })
        yield history