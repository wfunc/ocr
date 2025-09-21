# OCR 服务

一键启动方式：

```bash
./start.sh
```

脚本会自动创建虚拟环境、安装 Python 依赖，随后启动 Gin HTTP 服务（端口 `8080`）。

## Docker 部署

本地构建镜像并运行：

```bash
docker build -t ocr-server:local .
docker run --rm -p 8080:8080 ocr-server:local
```

项目已内置 GitHub Actions（`.github/workflows/auto-release.yml`），当推送到 `main` 分支或手动触发工作流时，会自动：

- 递增 `VERSION` 文件并生成新的 `vX.Y.Z` 标签
- 为 Linux `amd64` 与 `arm64` 交叉编译二进制包并附加到 Release
- 构建并推送多架构镜像到 GitHub Container Registry（`ghcr.io/<your-username>/wfunc-ocr`）和 Docker Hub（`docker.io/<dockerhub-username>/ocr`）
- 创建对应的 GitHub Release

Release 附件包含：

- `ocr-server-<version>-linux-amd64.tar.gz`
- `ocr-server-<version>-linux-arm64.tar.gz`
- `SHA256SUMS`

首次使用前，确保仓库启用了 GitHub Packages，并遵循 GitHub 的权限设置即可，无需额外 Secrets。

接口说明：

- `GET /ocr?url=xxx`
- `POST /ocr`，请求体示例：

```json
{"url": "data:image/png;base64,...."}
```

服务会调用 `ocr.py` 并返回识别结果：

```json
{
  "result": "识别出的文本",
  "raw_output": "脚本原始输出（含调试信息）"
}
```

> 若需要自定义 Python 解释器，可在运行前设置 `PYTHON_BIN=/path/to/python ./start.sh`。
