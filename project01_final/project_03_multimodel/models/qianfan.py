'''
    1. 获取apikey和baseurl
    2. 基于apikey和baseurl创建一个和llm的连接
        连接的实例对象 --client
    3. 基于client
        发送请求、
        流式输出：获取响应、回传响应
'''
#Users-->View---->Service----->Dao----->DBHelper---->DBConnection-----> MySql

import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

# 以下三行代码应该放在app.py中
# from dotenv import load_dotenv,find_dotenv
# # 1.1 获取apikey和baseurl,完成.env查找和加载（系统环境变量中）
# sys.path.append(os.path.join(os.path.dirname(__file__)))
# load_dotenv(find_dotenv(".env"))

'''
    1-预处理（清洗、格式化）发过来的信息，规范成openai_message
    2-发送并接收
    3-输出
'''
class QianfanLlmEngine:
    def __init__(self):
        api_key=os.getenv("QIANFAN_API_KEY")
        if not api_key:
            raise ValueError("QIANFAN_API_KEY not set,or .env file not found.") #作用：如果没有设置环境变量，就抛出异常
        base_url=os.getenv("QIANFAN_BASE_URL")

        self.client=OpenAI(  #openai sdk的封装,封装复杂的网络通信细节
            api_key=api_key,
            base_url=base_url,
            max_retries=3,  #自动重试次数。网络抖动时，Client 会自动帮你多试几次
        )
        if not self.client:
            raise ValueError("self.client not set,or .env file not found.")
        
    #--R08 增加角色提示词参数
    def chat(self,history,model_name:str="ernie-4.0-8k",temperature:float=0.7,prompt_text:str=""): #加:和=的作用：指定参数的类型和默认值
        # 1-预处理、清洗
        openai_messages=[]
        for msg in history:  
            raw_content=msg.get("content")
            clean_content=""

            if isinstance(raw_content,list):                
                # 如果 content 是列表（多模态格式），提取其中的 text 类型内容
                for item in raw_content:
                    if isinstance(item,dict) and item.get("type")=="text":
                        clean_content+=item.get("text",'')
            elif isinstance(raw_content,str):
                clean_content=raw_content  # 纯文本格式直接赋值
            else:
                clean_content = str(raw_content) if raw_content else ""  # 容错处理 非标类型有哪些:比如None,数字,布尔值或者意外传入的对象
            
            # 如果 clean_content 是 None(已杜绝) 或空字符串 ""
            if clean_content and clean_content.strip():
                openai_messages.append({
                    "role":msg["role"],
                    "content":clean_content,
                })

        #--R09 将系统提示词加入到历史会话的首部
        if prompt_text and str(prompt_text).strip():
            #生成系统提示词
            system_message={
                'role':'system',
                'content':str(prompt_text).strip(),
            }
            openai_messages.insert(0,system_message)

        print(f"DEBUG:Sending to OpenAi SDK：{openai_messages}")

        if not openai_messages:
            yield history  #边界防御。如果洗完发现没内容，直接返回原样，避免发起无效网络请求浪费 Token
            return  # 如果没有 return，代码会继续向下执行

        # 2- 基于之前创建的连接实例对象，发送消息、获取响应
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=openai_messages,
                temperature=temperature,
                stream=True,
            )

            # 3-流式解析,流式响应
            # 准备字典列表的message formatte数据格式（openai的数据格式）来逐步接收流式            
            history.append({    
                "role":"assistant",
                "content":""
            })  # 先在历史记录末尾占位

            for chunk in response:
                #流式数据包(Chunk中),第一包可能只包含角色信息,直接写后果:delta.content为None或不存在,最后一包可能只包含结束符(finish_reason),直接写:程序崩溃.因为最后一个包里没有content字段,它们都没有content
                if chunk.choices and chunk.choices[0].delta.content:  #多层级属性安全取值.OpenAI格式层级深,必须逐级判断是否存在delta.content.否则会触发AttributeError
                    content = chunk.choices[0].delta.content
                    history[-1]["content"] += content
                    yield history
        except Exception as e:
            print(f"OpenAI SDK ERROR:{e}")            
            history.append({"role":"assistant","content":f"API调用出错:{str(e)}"})
            yield history


# ==========================================
# 测试代码入口
# ==========================================
if __name__ == "__main__":
    # 【关键修改】在这里（测试专用区域）进行环境补救
    print(">>> (测试模式) 正在加载环境变量...")    
    # 手动加载同级或上级的 .env
    # 注意：如果 .env 在根目录，models/qianfan.py 运行时的相对路径可能找不到
    # 建议使用 find_dotenv() 自动查找，或者手动指定绝对路径
    load_dotenv(find_dotenv())


    # -----------------------------------
    print(">>> 开始测试 QianfanLlmEngine...")

    # 1. 尝试初始化引擎
    try:
        engine = QianfanLlmEngine()
        print("引擎初始化成功！")
    except Exception as e:
        print(f"引擎初始化失败: {e}")
        exit()

    # 2. 模拟 Gradio 传入的历史记录数据 (Messages 格式)
    # 模拟用户发送 "你好..."
    test_history = [
        {"role": "user", "content": "请用一句话介绍一下百度千帆。"}
    ]

    print(f"--- 正在发送消息: {test_history[0]['content']} ---")

    # 3. 调用 chat 函数并处理流式输出
    # 因为 chat 函数使用了 yield，所以它返回的是一个生成器，必须用循环迭代
    try:
        # 这里的 chat() 会返回不断更新的 history 列表
        generator = engine.chat(history=test_history, temperature=0.5)
        
        for current_history in generator:
            # 获取最新的一条消息（即 AI 正在生成的回复）
            ai_reply = current_history[-1]
            
            # 为了在控制台看清楚流式效果，使用 sys.stdout 刷新打印，或者直接打印当前完整内容
            # 这里为了简单，直接打印 AI 当前生成的所有内容，模拟打字机效果会刷屏，
            # 所以只打印最后一次生成的完整内容，中间过程用 print('.', end='') 模拟进度。
            print(f"\r正在生成: {ai_reply['content']}", end="", flush=True)
        
        print("\n\n测试完成！完整对话记录如下：")
        print(test_history)

    except Exception as e:
        print(f"\n调用 chat 过程中出错: {e}")



    '''
    __init__的内容
        判断“生命周期” —— 这个值在整个对象存在的期间，是否基本保持不变
        判断“依赖关系” —— 如果没有这个东西，这个类还能初始化吗
        判断“资源开销” —— 创建这个变量是否费时、费内存？是否涉及网络连接
        判断“灵活性需求” —— 如果我想在同一次运行中，用不同的模式调用它，方便吗，为了灵活性，放函数参数
        参考“AIOps 运维视角”的标准化原则 —— 环境敏感：凡是从环境变量读取的内容（敏感信息、后端 URL），一律在 __init__ 中完成加载和校验。
                                        无状态执行：函数（如 chat）应该尽量只处理输入的数据流，而不应该去管“如何连接服务器”这种底层破事
    '''
    '''
        client的作用
            建立连接： 与百度千帆（或 OpenAI）的服务器进行 TCP/HTTP 握手。
            协议转换： 把你写的 Python 字典（Messages）转换成服务器能理解的 JSON 格式。
            身份验证： 自动在请求头（Header）里加上你的 API_KEY。
            错误处理： 处理网络超时、断线重连或服务器 500 错误
    '''
    '''
        无效请求费： API 供应商（如百度、OpenAI）对每个 Request 都有基础开销。
        异常开销： 服务器收到空消息会返回 400 Bad Request 错误。虽然没产生生成 Token，但你的代码进入了 except 块，
                消耗了系统的 CPU 和网络 IO 资源。在 AIOps 高频调用场景下，成千上万个空请求会造成网络拥塞
    '''
    '''
        self.client.chat.completions.create:作用:发起网络请求.它把数据发给远程服务器(或本地容器化的模型服务),并获取结果。
        tokenizer.apply_chat_template:      作用:格式化文本.它不联网,只是把字典列表转成带特定Prompt标记(如<|im_start|>)的长字符串。
        区别:前者是“寄信”,后者是“把信装进信封”.在您的F盘模型开发中,如果是调用API用前者:如果是用Transformers加载F盘本地权重推理,则必须先用后者
    '''
    '''
        不占位会怎样：
            代码执行到history[-1]["content"]+=content时,会因为找不到对应的助手回复框而报错(下标越界或修改了用户的上一条消息)
            用户体验： 没有占位符，用户在前端看不到“AI 正在输入”的状态
    '''
    '''
        chunk: 服务器返回的一个极小的二进制数据块。
        choices[0]: API 支持一次生成多个结果，默认取第一个。
        delta: 增量对象，代表这次“新蹦出来”的数据。
        content: 本次生成的具体字符（例如“北”、“京”）
    '''
    '''
    1. 多模态列表	List  {"role": "user", "content": [{"type": "text", "text": "你好"}, {"type": "image_url", "url": "..."}]}  if isinstance(raw_content, list)	重点情况。代码会遍历列表，只捞取 type=="text" 的部分，丢弃图片信息。
    2. 简单字符串	Str	    "你是谁？"	                         elif isinstance(raw_content, str)	常规情况。直接赋值给 clean_content。
    3. 非标数字/布尔 Int/Bool	12345 或 True	                else: clean_content = str(...)	    异常情况。有些前端传参错误，强行转成字符串 "12345" 防止程序报错。
    4. 缺失/空值	None	None	                           else: clean_content = ""	            容错情况。如果 msg 里没有 content 键，代码确保它变成空串，不至于崩掉。
    5. 复杂嵌套列表 list  ['第一段', '第二段']                  if isinstance(raw_content, list)    边界情况。如果是纯字符串列表，内部 item.get 会失败（因为 item 不是 dict），从而返回空，这也解释了为什么代码里要判 isinstance(item, dict)
    '''
    '''
    为什么不建议这么做？（穿透式死角拆解）
    （1） 极其隐蔽的“竞态条件”风险（Race Condition）
        虽然 Python 有全局解释器锁（GIL），但在某些高级异步框架（如 asyncio）或多线程环境中，chunk 对象是由底层 SDK 异步填充的。
        风险点： 极小概率下，if 判断时 chunk.choices[0].delta.content 还有值，但到了执行 += 那一行时，由于底层连接重置或内存回收，该值可能被置为空或改变。
        对比： 赋值给 content 变量相当于做了一次“内存快照”。一旦赋值成功，content 就是一个独立的局部引用，不受原对象变化的影响。
    （2） 属性访问的性能开销（Performance Overhead）
        原生写法： 访问 1 次 chunk -> 访问 1 次 choices -> 访问 1 次索引 0 -> 访问 1 次 delta -> 访问 1 次 content。拿到值后，后面直接用。
        改写后写法： 你在 if 里访问了一遍这 5 层结构，在 += 时又重新访问了一遍这 5 层结构。
        深度分析： 在大模型流式响应中，一个回复可能有成百上千个 Chunk。每一包都多进行 5 次属性寻址，在高并发、高性能要求的 AI 应用中，这属于不必要的 CPU 消耗。
    （3） 笔误与维护的“死角”（Maintenance Risk）
        仔细看你提供的改写代码：
        history[-1]["content"] += hunk.choices[0].delta.content
        发现了吗？ 你把 chunk 写成了 hunk。
        拆解： 当路径非常长（如 chunk.choices[0].delta.content）时，程序员极易在第二次书写时产生笔误。如果使用局部变量 content，你只需要在赋值时写对一次，后面使用简单的变量名，犯错率降低 90% 以上。
    （4） 调试与日志记录的缺失
        在实际开发中，我们经常需要这样：
        python
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                # print(f"DEBUG: 收到字符 -> {content}") # 方便在这里打断点或输出
                history[-1]["content"] += content
        请谨慎使用此类代码。
        如果你直接累加，当你发现回复内容乱码或缺失时，你很难在这一行精确地观察到“那一瞬间”到底收到了什么，除非你再次写一遍长长的链式调用
    '''