# Bug Agent Demo

一个用于练习工具调用（tool calling）的极简代码修复 Agent。Agent 会检查 `target` 目录中的 Python 项目，按需读取或修改文件，并运行 pytest，直到测试全部通过或达到最大执行步数。

## 项目结构

```text
.
├── agent.py                 # Agent 主循环与工具定义
├── tools.py                 # 文件读写和测试执行工具
└── target/
    ├── calculator.py        # 待检查/修复的示例代码
    └── test_calculator.py   # pytest 测试
```

## 环境要求

- Python 3.10+
- DeepSeek API Key

## 安装

建议先创建并启用虚拟环境，然后安装依赖：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
pip install openai pytest
```

macOS / Linux：

```bash
source .venv/bin/activate
pip install openai pytest
```

## 运行

先配置 API Key。

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY = "your-api-key"
python agent.py
```

macOS / Linux：

```bash
export DEEPSEEK_API_KEY="your-api-key"
python agent.py
```

运行后，Agent 会在终端中输出每一步的工具调用和结果。当前默认模型为 `deepseek-flash`，最多执行 10 步。

也可以直接运行示例测试：

```bash
pytest -q target
```

## 注意事项

- 请勿将 API Key 写入代码或提交到版本库。
- Agent 会覆盖写入 `target` 目录中的文件，建议只在练习项目或受版本控制的代码上运行。
- `tools.py` 是为了演示而设计的最小实现，不应直接用于执行不受信任的输入。
