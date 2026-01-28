# FROM public.ecr.aws/lambda/python:3.12

# # Copy and install deps
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy code
# COPY app.py graph.py ./
# COPY tools ./tools
# COPY rag ./rag

# # Set Lambda handler
# CMD ["app.lambda_handler"]
FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py graph.py ./
COPY rag ./rag
COPY tools ./tools

CMD ["app.lambda_handler"]
