# 如何利用 OpenCode 免费模型驱动 OMP (Oh My Pi) 智能体

本工程包含一个本地免密代理服务 (`opencode_keyless_proxy.py`)，可以让你的 OMP (Oh My Pi / Pi Coding Agent) 智能体免密调用 OpenCode 网关（`opencode.ai`）提供的所有免费大模型（如 `deepseek-v4-flash-free`、`hy3-free`、`nemotron-3-ultra-free` 等）。代理会拦截 `/v1/models` 请求，仅返回真正免费的模型（ID 以 `-free` 结尾或 `big-pickle`），剔除 OMP 内置目录里那些需要密钥的付费模型。

## 🚀 快速开始步骤

### 第一步：启动本地代理服务

进入本工程目录，运行以下命令拉起本地免密转发代理（在后台或新的终端窗口中运行，监听 `127.0.0.1:4000`）：

```bash
uv run python opencode_keyless_proxy.py
```
*提示：该代理会自动剥离 OMP 默认带有的 Auth 占位请求头，防止上游网关报错，同时支持流式传输 (SSE) 并配置了 120 秒的宽松读取超时，以应对慢推理模型的首字延迟。*

### 第二步：配置 OMP 的 `models.yml`

打开你的 OMP 用户模型配置文件 `~/.omp/agent/models.yml`（如果不存在则新建），在 `providers` 下追加 `opencode-free` 供应商（使用独立的自定义供应商名以避免 OMP 内置的 72 个付费模型目录干扰），并通过 `discovery` 从本地代理动态获取免费模型列表：

```yaml
providers:
  opencode-free:
    baseUrl: http://127.0.0.1:4000
    api: openai-completions
    apiKey: any-string # 使用任意虚拟 Key 避开 OMP 本地验证限制
    discovery:
      type: openai-models-list

### 第三步：在 OMP 中使用模型

配置完成并保持本地代理运行后，重新启动 OMP 会话。你可以使用以下方式使用这些模型：

1. **查看可用模型**：
   ```bash
   omp models
   ```
   你将在列表中看到 `opencode-free` 下自动发现的所有免费模型（例如 `deepseek-v4-flash-free`、`hy3-free`、`big-pickle` 等）。

2. **单次命令调用测试**：
   ```bash
  omp --model opencode-free/deepseek-v4-flash-free -p "用两个字打招呼"
   ```

3. **设置 OMP 默认驱动模型**：
   若想将 OMP 会话的默认模型切换为 OpenCode 的免费模型，运行：
   ```bash
  omp config set modelRoles.default opencode-free/deepseek-v4-flash-free
  ```
  或者直接修改 OMP 的配置 `~/.omp/agent/config.yml`：
  ```yaml
  modelRoles:
    default: opencode-free/deepseek-v4-flash-free
    smol: opencode-free/deepseek-v4-flash-free
    slow: opencode-free/hy3-free
   ```
