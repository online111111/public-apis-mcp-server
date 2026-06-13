"""Public APIs MCP Server — 基于 public-apis 项目挑选的免费公共 API"""

from .server import mcp


def main():
    """启动 MCP server（stdio 模式）"""
    mcp.run()


if __name__ == "__main__":
    main()
