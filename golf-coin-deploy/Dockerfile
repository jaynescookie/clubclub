FROM python:3.11-slim
WORKDIR /app
COPY server.py app.html ./
ENV PORT=8080 DATA_DIR=/data
VOLUME ["/data"]
EXPOSE 8080
CMD ["python3", "server.py"]
