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

echo 'Installing openclaw'

curl -fsSL https://openclaw.ai/install.sh | bash

echo 'Install clawhub and skills'
npm i -g clawhub
clawhub install Searxng
clawhub install summarize

