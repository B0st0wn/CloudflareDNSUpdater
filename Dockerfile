FROM python:3.12-slim

# Install minimal deps for runtime
RUN apt-get update \
	 && apt-get install -y --no-install-recommends \
		 bash tzdata ca-certificates wget build-essential gcc libssl-dev libffi-dev libyaml-dev \
	 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir -r requirements.txt

# remove build deps to reduce final image size
RUN apt-get remove -y build-essential gcc libssl-dev libffi-dev libyaml-dev \
	&& apt-get autoremove -y \
	&& rm -rf /var/lib/apt/lists/*

COPY ./app ./app

VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD wget -q -O - http://localhost:8080/health || exit 1

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080","--proxy-headers"]
