FROM python:3.12-slim
WORKDIR /app
RUN pip install --quiet uv
COPY . user_agent/
WORKDIR /app/user_agent
RUN if [ -d wheels ]; then uv pip install --system --no-deps wheels/*.whl; fi
RUN if [ -f requirements.txt ]; then uv pip install --system --find-links=./wheels --prerelease=allow -r requirements.txt; fi
EXPOSE 8088 8090
CMD ["python", "main.py"]
