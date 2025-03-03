# 使用Gradio构建的一个Web版AI聊天机器人Demo

## 运行方式
前提：运行本Demo时调用的大模型API需适配OpenAI格式，如火山方舟大模型API
```shell
# 构建Docker镜像
docker build -t gradio-chatbot-demo .

# 运行容器，注意替换大模型API相关环境变量
docker run --name gradio-chatbot-demo -p 7860:7860 -d -e LLM_API_KEY=<xxx> -e LLM_MODEL_ID=<xxx> -e LLM_API_URL=<xxx> gradio-chatbot-demo:latest
```

使用浏览器访问：http://127.0.0.1:7860
## 效果图
![](attachments/Pasted%20image%2020250303234637.png)