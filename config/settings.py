"""
Atlas 系统配置文件
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 工具相关配置
TOOLS_DIR = PROJECT_ROOT / "tools"
GENERATED_TOOLS_DIR = TOOLS_DIR / "generated"

# LLM 配置
LLM_MODEL = "qwen-max"
LLM_API_KEY = os.getenv("QWEN_API_KEY", "")
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Git 配置
GIT_AUTO_COMMIT = True
GIT_COMMIT_LANGUAGE = "zh-CN"

# 日志配置
LOG_LEVEL = "INFO"
LOG_DIR = PROJECT_ROOT / "logs"

# 确保必要的目录存在
GENERATED_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
