import os
import gradio as gr
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("LLM_API_KEY"),
    # 示例：调用火山方舟大模型API
    # base_url="https://ark.cn-beijing.volces.com/api/v3",
    base_url=os.environ.get("LLM_API_URL"),
)


def chat_with_ai(message, history, system_prompt, max_turns):
    history = history or []

    # 系统prompt
    messages = [{"role": "system", "content": system_prompt}]

    # 只保留最近max_turns轮对话
    history = history[-2 * max_turns :]
    # print(history)
    # 添加历史对话，使得ChatBot能够根据历史对话进行回复
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 添加本轮用户消息
    messages.append({"role": "user", "content": message})
    # print(messages)

    # 调用API获取回复
    response = client.chat.completions.create(
        model=os.environ.get("LLM_MODEL_ID"), messages=messages, stream=True
    )

    partial_message = ""
    # 流式获取回复
    for chunk in response:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content is not None:
            partial_message += chunk.choices[0].delta.content
            yield partial_message


# 定义Gradio界面
chatbot = gr.ChatInterface(
    fn=chat_with_ai,
    type="messages",
    title="AI 聊天助手",
    description="这是一个基于AI大模型的聊天机器人",
    theme="Soft",
    # 历史对话存储在用户本地浏览器中
    save_history=True,
    editable=True,
    additional_inputs=[
        gr.Textbox(
            label="系统预置提示词", value="你是人工智能助手小帅", show_label=True
        ),
        gr.Slider(
            minimum=1,
            maximum=20,
            value=5,
            label="可记忆的最大对话轮数",
            show_label=True,
            step=1,
        ),
    ],
    additional_inputs_accordion="Chatbot高级设置",
)


# 启动Gradio应用
if __name__ == "__main__":
    chatbot.launch(server_name="0.0.0.0", server_port=7860)
