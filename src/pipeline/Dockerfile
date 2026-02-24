# Keep your existing FROM line (likely python3-template-launcher-base)
FROM gcr.io/dataflow-templates-base/python3-template-launcher-base

# 1. Set the variable for where Dataflow expects files
ARG WORKDIR=/template
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

# 2. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 👇 THIS IS THE CRITICAL FIX: Copy the pipeline code to /template/pipeline.py
# (Make sure your local python file is actually named 'pipeline.py'. 
# If it's named 'main.py' or 'flash_crash.py', rename it or update this line)
COPY pipeline.py ${WORKDIR}/pipeline.py

# 4. Set the Environment Variable so Dataflow knows exactly where to look
ENV FLEX_TEMPLATE_PYTHON_PY_FILE="${WORKDIR}/pipeline.py"

# (Optional) If you have a setup.py, copy it too
# COPY setup.py ${WORKDIR}/setup.py