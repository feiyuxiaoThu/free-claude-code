# OpenCode Free + OMP 配置检查清单 (Windows PowerShell)

> 在 Windows 电脑的 PowerShell 中逐项检查，确认所有项均通过后配置即正常。

---

## 1. 代理服务检查

```powershell
# 检查代理是否正在运行（应输出 JSON 模型列表）
Invoke-RestMethod -Uri http://127.0.0.1:4000/v1/models
```

**预期输出**：包含 `data` 数组，每个模型有 `id`、`object`、`created`、`owned_by` 字段。  
**预期模型列表**（至少包含以下部分或全部）：

| 模型 ID |
|---|
| `big-pickle` |
| `deepseek-v4-flash-free` |
| `mimo-v2.5-free` |
| `nemotron-3-ultra-free` |
| `north-mini-code-free` |
| `ling-3.0-flash-free` |
| `laguna-s-2.1-free` |

**如果失败**：
- 未运行 → 启动代理：`uv run python opencode_keyless_proxy.py`
- 端口冲突 → 检查 `:4000` 是否被占用

---

## 2. 配置文件检查

### 2.1 `$HOME\.omp\agent\models.yml`

确认文件存在且内容如下：

```yaml
providers:
  nvidia-nim:
    baseUrl: http://localhost:8082/v1
    api: openai-completions
    apiKey: any-string
    headers:
      anthropic-version: "2023-06-01"
    models:
      - id: deepseek-v4-flash
        name: DeepSeek V4 Flash
        contextWindow: 1000000
        maxTokens: 65536
      - id: kimi
        name: Kimi K2.6
        contextWindow: 262000
        maxTokens: 65536
      - id: minimax
        name: MiniMax M2.7
        contextWindow: 200000
        maxTokens: 16384
      - id: glm
        name: GLM 5.1
        contextWindow: 200000
        maxTokens: 8192
      - id: deepseek-v4-pro
        name: DeepSeek V4 Pro
        contextWindow: 1000000
        maxTokens: 65536
  opencode-free:
    baseUrl: http://127.0.0.1:4000
    api: openai-completions
    apiKey: any-string
    discovery:
      type: openai-models-list
```

**关键检查点**：
- [ ] `opencode-free` provider 存在
- [ ] `baseUrl` 为 `http://127.0.0.1:4000`
- [ ] `api` 为 `openai-completions`
- [ ] `apiKey` 为任意字符串（占位用）
- [ ] `discovery.type` 为 `openai-models-list`

### 2.2 `$HOME\.omp\agent\config.yml`

确认文件包含以下关键内容：

```yaml
setupVersion: 1
modelRoles:
  default: opencode-free/mimo-v2.5-free
  commit: opencode-free/deepseek-v4-flash-free:off
  smol: opencode-free/north-mini-code-free:off
  tiny: opencode-free/ling-3.0-flash-free:high
enabledModels:
  - opencode-free/deepseek-v4-flash-free
  - opencode-free/big-pickle
  - opencode-free/mimo-v2.5-free
  - opencode-free/nemotron-3-ultra-free
  - opencode-free/north-mini-code-free
  - opencode-free/ling-3.0-flash-free
  - opencode-free/laguna-s-2.1-free
```

**关键检查点**：
- [ ] `modelRoles.default` 设为 `opencode-free/*` 系列的模型
- [ ] `enabledModels` 包含 `opencode-free/` 开头的模型
- [ ] 其他 provider (如 `google-antigravity/*`, `nvidia-nim/*`) 按需存在

---

## 3. OMP 可用模型检查

```powershell
# 查看 OMP 识别的全部可用模型
omp models
```

**预期输出**：列表中包含 `opencode-free/deepseek-v4-flash-free`、`opencode-free/mimo-v2.5-free` 等。

---

## 4. 端到端通话测试

```powershell
# 用免费模型跑一次推理
omp --model opencode-free/deepseek-v4-flash-free -p "用两个字打招呼"
```

**预期输出**：模型返回内容（如 `"你好"`），无报错。

**排查**：
- 连接被拒绝 → 代理未启动，回 **第 1 步**
- 模型未找到 → `models.yml` 配置有误，回 **第 2.1 步**
- 认证错误 → 检查 `apiKey` 是否设为任意字符串；检查代理是否正常转发

---

## 快速诊断命令清单

```powershell
# 1. 代理存活检查（应输出 200）
(Invoke-WebRequest -Uri http://127.0.0.1:4000/v1/models -UseBasicParsing).StatusCode

# 2. 查看 models.yml 中 opencode-free 配置段
Get-Content $HOME\.omp\agent\models.yml | Select-String -Pattern "opencode-free" -Context 0,5

# 3. 查看 config.yml 中 opencode-free 引用
Get-Content $HOME\.omp\agent\config.yml | Select-String -Pattern "opencode-free"

# 4. OMP 可见性检查
omp models | Select-String -Pattern "opencode-free"

# 5. 端到端测试（取前 5 行输出）
omp --model opencode-free/mimo-v2.5-free -p "Hi" 2>&1 | Select-Object -First 5
```
