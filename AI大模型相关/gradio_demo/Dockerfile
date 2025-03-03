FROM python:3.12-slim

WORKDIR /usr/local/app

COPY ./pip.conf /etc/pip.conf

RUN pip install --no-cache-dir gradio && pip install --no-cache-dir openai && rm -rf /root/.cache

COPY ./app.py ./

EXPOSE 7860

CMD ["python3", "app.py"]