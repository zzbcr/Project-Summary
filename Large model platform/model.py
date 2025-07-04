import os
import threading
import queue
import time
import copy
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class MedicalQAModel:
    def __init__(self):
        self.local_qwen_client = ChatOllama(
            model="qwen2.5:0.5b",
            base_url="http://localhost:8888",
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0.7
        )

        self.qwen_client = ChatOpenAI(
            openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
            openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name="qwen-max",
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0.7
        )

        # 更新为医疗相关的系统提示
        self.messages_local_qwen = [
            SystemMessage(content="""你是一个专业的医疗助手，请遵循以下规则：
1. 提供准确、专业的医疗健康建议
2. 对于症状描述，分析可能原因并提供初步建议
3. 对于严重症状，明确建议用户立即就医
4. 不提供诊断，只给参考建议
5. 回答简明扼要，使用通俗语言""")
        ]

        self.messages_qwen = [
            SystemMessage(content="""你是一个专业的医疗助手，请遵循以下规则：
1. 提供准确、专业的医疗健康建议
2. 对于症状描述，分析可能原因并提供初步建议
3. 对于严重症状，明确建议用户立即就医
4. 不提供诊断，只给参考建议
5. 回答简明扼要，使用通俗语言""")
        ]
        
        self.history_records = []
        self.current_model = "local"
        self.model_mapping = {
            "local": {"name": "本地医疗模型", "messages": self.messages_local_qwen, "client": self.local_qwen_client},
            "cloud": {"name": "云端医疗模型", "messages": self.messages_qwen, "client": self.qwen_client}
        }
        
        self.output_queue = queue.Queue()

    def switch_model(self):
        self.current_model = "cloud" if self.current_model == "local" else "local"
        model_info = self.model_mapping[self.current_model]
        print(f"\n已切换到 {model_info['name']}\n")

    def handle_model_response(self, messages, model_key):
        model_info = self.model_mapping[model_key]
        try:
            start_time = time.time()
            self.output_queue.put(f"\n{model_info['name']}回答：")
            answer = ""
            for chunk in model_info["client"].stream(messages):
                content = chunk.content
                answer += content
                self.output_queue.put(content)
            end_time = time.time()
            answer += f" [{model_info['name']}回答]"
            self.output_queue.put(f"\n回答时间：{end_time - start_time:.2f}秒\n")
            self.history_records.append({'question': messages[-1].content, 'answer': answer, 'model': model_info['name']})
        except Exception as e:
            self.output_queue.put(f"\n[错误] {model_info['name']}请求失败：{e}\n")

    def send_question(self, question):
        if not question.strip():
            return

        model_info = self.model_mapping[self.current_model]
        model_messages = copy.deepcopy(model_info["messages"])
        model_messages.append(HumanMessage(content=question))
        threading.Thread(target=self.handle_model_response, args=(model_messages, self.current_model)).start()