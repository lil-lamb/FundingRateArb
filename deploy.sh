#!/bin/bash
# Build and deploy script for BTC Trading Bot

# Configuration
IMAGE_NAME="btc-trading-bot"
CONTAINER_NAME="btc-bot"
PORT=8501

echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "🛑 Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🚀 Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -p $PORT:8501 \
  $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo "✅ Deployment complete!"
    echo "🌐 Access your bot at: http://localhost:$PORT"
    echo "📊 View logs: docker logs -f $CONTAINER_NAME"
    echo "🔍 Check status: docker ps | grep $CONTAINER_NAME"
else
    echo "❌ Deployment failed!"
    echo "📋 Check logs: docker logs $CONTAINER_NAME"
    exit 1
fi