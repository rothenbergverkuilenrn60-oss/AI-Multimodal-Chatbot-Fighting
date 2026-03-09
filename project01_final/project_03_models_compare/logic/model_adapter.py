import asyncio
import copy
from project_03_models_compare.models.engine import OllamaEngine
import os


class ModelAdapter:
    def __init__(self):
        self.ollama_models = {
            "Qwen3-VL": "qwen3-vl:8b",
            "DeepSeek-R1": "deepseek-r1:1.5b",
            "GPT-OSS": "gpt-oss:20b",
            "Qwen3-Coder": "danielsheep/Qwen3-Coder-30B-A3B-Instruct-1M-Unsloth:UD-Q6_K_XL"
        }
        
        self.model_instances = {}
        
        self.default_model = "Qwen3-VL"

    async def bot(self, *args):
        if len(args) >= 7:

            histories = args[:3]  
            selected_models = args[3:6]  
            temperature = args[6]  
        else:

            histories = args[:3] if len(args) >= 3 else args
            selected_models = [self.default_model] * len(histories)  
            temperature = args[3] if len(args) > 3 else 0.7  
        queue = asyncio.Queue()
        active_tasks = 0
        
        h_list = [copy.deepcopy(h) for h in histories]

        async def producer(idx, model_name, history):
            """模型生成器，负责调用Ollama模型并将结果放入队列"""
            nonlocal active_tasks
            try:
                # 获取或创建Ollama模型实例
                if model_name not in self.model_instances:
                    # 获取对应的Ollama模型名称
                    ollama_model_name = self.ollama_models.get(model_name, self.ollama_models[self.default_model])
                    self.model_instances[model_name] = OllamaEngine(ollama_model_name)
                
                model_instance = self.model_instances[model_name]
                
                async for updated_h in model_instance.chat(history, temperature):
                    await queue.put((idx, updated_h))
            except Exception as e:
                print(f"模型 {model_name} 异常: {e}")

                history.append({"role": "assistant", "content": f"模型调用出错: {str(e)}"})
                await queue.put((idx, history))
            finally:
                active_tasks -= 1


        for i in range(len(h_list)):

            model_name = selected_models[i] if i < len(selected_models) else self.default_model
            
            active_tasks += 1

            asyncio.create_task(producer(i, model_name, h_list[i]))

        while active_tasks > 0 or not queue.empty():
            try:
                idx, updated_h = await asyncio.wait_for(queue.get(), timeout=0.01)
                h_list[idx] = updated_h
                yield tuple(h_list)
            except asyncio.TimeoutError:
                continue

chat_adapter = ModelAdapter()