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

echo 'Install open telemetry plugin for Jaeger'
cd /home/jacek/.npm-global/lib/node_modules/openclaw/extensions/diagnostics-otel/
npm install
openclaw plugins install @openclaw/diagnostics-otel
openclaw gateway restart

echo 'Otel plugin isntalled. Import openclaw.json or enable otel there and set Jaeger url.' 

echo 'Install docker compose. So we can install Langfuse later'
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version

echo 'Install Langfuse'
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up

echo "Now you need to generate keys, base64 them and configure openclaw otel with it"
echo "-n \"pk-lf-...:sk-lf-...\" | base64"


