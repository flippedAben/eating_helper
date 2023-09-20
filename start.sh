#!/bin/bash

cd backend
poetry install
poetry run uvicorn eating_helper.web_server.main:app --reload &

cd ../frontend
npm run dev &
cd ..