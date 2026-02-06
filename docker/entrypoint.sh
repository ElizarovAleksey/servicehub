#!/bin/sh
set -e

echo "[ServiceHub] Starting..."

# если volume пустой — инициализируем
if [ ! -f /app/app.py ]; then
  echo "[ServiceHub] Initializing /app from image..."
  cp -R /opt/app/* /app/
else
  echo "[ServiceHub] Using existing /app volume"
fi

cd /app
exec python app.py