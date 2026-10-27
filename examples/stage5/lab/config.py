"""配置与用户可理解的错误；离线导入不需要第三方包。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "data" / "docs"
RUNTIME = ROOT / ".runtime"


def live_client():
    try:
        from dotenv import load_dotenv
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("请先运行 python -m pip install -r requirements.txt") from exc
    load_dotenv(ROOT / ".env", override=False)
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("缺少 OPENAI_API_KEY：复制 .env.example 为 .env 并填写密钥，或去掉 --live。")
    # 固定官方端点，避免环境中遗留的第三方 BASE_URL 意外接收密钥。
    return OpenAI(api_key=key, base_url="https://api.openai.com/v1", timeout=30, max_retries=0)


def model_name():
    return os.environ.get("OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")


def cli(main):
    """只打印错误类别与修复建议，不回显密钥或完整请求。"""
    try:
        main()
    except KeyboardInterrupt:
        print("已中断。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        name = type(exc).__name__
        hints = {
            "AuthenticationError": "认证失败：检查 .env 中的 API key 是否有效。",
            "PermissionDeniedError": "权限不足：检查项目权限与模型访问权限。",
            "NotFoundError": "模型或接口不存在：检查 OPENAI_MODEL 与账号可用模型。",
            "RateLimitError": "额度或速率受限：检查余额/限额，稍后重试，不要无限重试。",
            "APITimeoutError": "请求超过 30 秒：检查网络后手动重试。",
            "APIConnectionError": "连接失败：检查网络、代理和证书设置。",
            "BadRequestError": "请求被拒绝：检查模型是否支持 Responses 与工具调用。",
            "APIStatusError": "服务端请求失败：稍后重试，并查看服务商状态。",
            "OperationalError": "数据库无法访问：检查 .runtime 目录权限，关闭占用数据库的程序。",
        }
        message = hints.get(name)
        if message is None:
            message = str(exc) if isinstance(exc, (ValueError, RuntimeError, FileNotFoundError, PermissionError)) else "运行失败，请检查输入和文件权限。"
        print(f"错误 [{name}]：{message}", file=sys.stderr)
        raise SystemExit(1)
