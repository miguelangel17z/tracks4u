FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gen_synthetic.py recommend.py check_output.py ./

CMD ["sh", "-c", "if [ \"${GENERATE_SYNTHETIC:-1}\" = \"1\" ]; then python gen_synthetic.py; fi && python recommend.py && python check_output.py"]
