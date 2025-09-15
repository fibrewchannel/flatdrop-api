#!/bin/sh

uvicorn app.main:app --reload --port 5050 &
