#!/usr/bin/env bash

# Ensure the script is being run as root otherwise we can't reconfigure ollams context limits
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run this script as root (use: sudo ./set_ollama_vram_limit.sh)"
  exit 1
fi

echo 'Installing SearXNG'
docker pull docker.io/searxng/searxng:latest
mkdir -p ./searxng/config/ ./searxng/data/
cd ./searxng/
docker run --name searxng -d \
    -p 8888:8080 \
    -v "./config/:/etc/searxng/" \
    -v "./data/:/var/cache/searxng/" \
    docker.io/searxng/searxng:latest

echo "Run Jaeger with a restart policy to survive system reboots"
docker run -d \
  --name jaeger \
  --restart unless-stopped \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 5778:5778 \
  -p 9411:9411 \
  cr.jaegertracing.io/jaegertracing/jaeger:2.16.0

echo 'Installing ollama'

curl -fsSL https://ollama.com/install.sh | sh

echo "⚙️ Configuring global context limit (32768 tokens) for Ollama..."

# Create the systemd override directory for Ollama
mkdir -p /etc/systemd/system/ollama.service.d

# Create the override configuration file and insert the environment variables
cat <<EOF > /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_CONTEXT_LENGTH=65536"
Environment="OLLAMA_NUM_CTX=65536"
EOF

echo "🔄 Reloading systemd daemon and restarting the Ollama service..."
# Reload systemctl so it sees the new override file, then restart the service
systemctl daemon-reload
systemctl restart ollama

echo 'Installing openclaw'

curl -fsSL https://openclaw.ai/install.sh | bash

echo 'Install clawhub and skills'
npm i -g clawhub
clawhub install Searxng
clawhub install summarize

