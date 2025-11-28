#!/usr/bin/env bash
set -e

cd /home/jenkins/Desktop/karma_agent

if [ ! -f ".venv/bin/activate" ]; then
  echo "Virtualenv not found. Creating..."
  python3 -m venv .venv
fi

source .venv/bin/activate

uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8010
