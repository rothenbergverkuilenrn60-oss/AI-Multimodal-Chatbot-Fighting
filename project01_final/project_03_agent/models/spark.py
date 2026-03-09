import os
from openai import OpenAI

class SparkEngine:
    def __init__(self):
        api_key=os.getenv('SPARK_API_KEY')
        if not api_key:
            raise ValueError("SPARK_API_KEY not set,or .env file not found.")
        base_url=os.getenv('SPARK_BASE_URL')
        self.client=OpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=3,
        )
        if not self.client:
            raise ValueError("self.client not set,or .env file not found.")
        
    def chat(self,history,model_name:str="ep-m-20260107190352-sktbf",temperature:float=0.7,prompt_text:str=""):
        openai_message=[]

        for msgdict in history:                          
            hou_content=msgdict.get('content')              
            clean_content=""                                

            if isinstance(hou_content,list):
                for hou_content_item in hou_content:
                    if isinstance(hou_content_item,dict) and hou_content_item.get("type")=="text":  
                        clean_content+=hou_content_item.get("text","")   
            elif isinstance(hou_content,str):
                clean_content+=hou_content
            else:
                clean_content=str(hou_content) if hou_content else ""    

            if clean_content and clean_content.strip():       
                openai_message.append({                       
                    "role":msgdict['role'],
                    "content":clean_content
                })

        #--R09 将系统提示词加入到历史会话的首部
        if prompt_text and str(prompt_text).strip():
            #生成系统提示词
            system_message={
                'role':'system',
                'content':str(prompt_text).strip(),
            }
            openai_message.insert(0,system_message)

        if not openai_message:                              
            yield history
            return
        
        try:
            # 添加模型验证和日志
            print(f"DEBUG: Spark model name: {model_name}")
            print(f"DEBUG: Spark messages: {openai_message}")
            
            response=self.client.chat.completions.create(
                model=model_name,
                messages=openai_message,
                temperature=temperature,
                stream=True,
            )

            history.append({
                "role":"assistant",
                "content":""
            })

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content=chunk.choices[0].delta.content
                    history[-1]["content"]+=content         
                    yield history                      
        
        except Exception as e:
            print(f"OpenAI SDK ERROR:{e}")
            history.append({"role":"assistant","content":f"API调用出错:{str(e)}"})
            yield history