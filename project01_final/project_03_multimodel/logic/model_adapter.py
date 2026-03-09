'''
    模型适配
        沟通前（界面）后（具体模型）的转发器
        依据前端界面发过来的参数，调用后端某个具体的模型的chat方法
'''
import os,sys

# current_file_path=os.path.abspath(__file__)
# current_dir=os.path.dirname(current_file_path)
# project_root=os.path.diename(current_dir)
# sys.path.insert(0,project_root)

from project_03_multimodel.models.qianfan import QianfanLlmEngine
from project_03_multimodel.models.spark import SparkEngine
from project_03_multimodel.models.ernie import ErnieEngine

_engine_cache = {}

def get_engine(model_name):
    if model_name in _engine_cache:
        return _engine_cache[model_name]

    engine = None
    if model_name == "QianFan":
        engine = QianfanLlmEngine()
    elif model_name == '豆包':
        engine = SparkEngine()
    elif model_name == 'Ernie':
        engine = ErnieEngine()

    if engine:
        _engine_cache[model_name] = engine
    return engine

def bot(history, model_name, temperature, prompt_text):
    """
    模型适配器入口
    """
    engine = get_engine(model_name)

    if not engine:
        history.append({
            "role": "assistant",
            "content": f"系统错误: 未找到模型引擎 {model_name}"
        })
        yield history
        return

    try:
        # 统一调用 chat 接口
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