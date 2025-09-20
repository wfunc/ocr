# syntax=docker/dockerfile:1

ARG GO_VERSION=1.22
ARG PYTHON_VERSION=3.12-slim

FROM golang:${GO_VERSION}-bookworm AS builder
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .

ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
RUN CGO_ENABLED=0 GOOS=${TARGETOS:-linux} GOARCH=${TARGETARCH:-amd64} go build -o /out/ocr-server ./main.go

FROM python:${PYTHON_VERSION}
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHON_BIN=/usr/local/bin/python

WORKDIR /app

COPY requirements.txt ocr.py ./

# 安装运行 OCR 所需的系统依赖并安装 Python 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        libffi-dev \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        librsvg2-2 \
        libgdk-pixbuf-2.0-0 \
        libglib2.0-0 \
        libgl1 \
    && python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && apt-get purge -y build-essential pkg-config libffi-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/ocr-server ./ocr-server

EXPOSE 8080

CMD ["/app/ocr-server"]
