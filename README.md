# Public APIs MCP Server

一个基于 FastMCP 的 Model Context Protocol (MCP) 服务，包装了 **10 个完全免费**的公共 API，无需任何 API key，开箱即用。

## 功能

| 工具 | API 来源 | 用途 |
|------|----------|------|
| `get_weather` | Open-Meteo | 🌤️ 实时天气及 7 天预报 |
| `get_country_info` | REST Countries | 🌍 国家详情（人口、货币、语言等） |
| `get_posts` / `get_users` | JSONPlaceholder | 📝 模拟测试数据 |
| `get_asteroid_info` | NASA NEO | 🚀 近地小行星数据 |
| `get_astronomy_picture` | NASA APOD | 🔭 每日天文图片 |
| `get_ip_geolocation` | ip-api.com | 📍 IP 地理位置查询 |
| `lookup_word` | Free Dictionary API | 📖 英文单词定义/音标/例句 |
| `get_random_activity` | Bored API | 🎯 随机活动推荐 |
| `search_arxiv` | arXiv API | 📄 学术论文搜索（物理/数学/CS 等） |
| `search_books` | Open Library | 📚 图书搜索 |
| `get_sun_times` | Sunrise-Sunset API | ☀️ 日出日落/天文晨昏时间 |

全部零配置，无需 API key（NASA 使用公开 `DEMO_KEY`）。

## 快速开始（CLAUDIO）

```json
{
  "mcpServers": {
    "public-apis": {
      "command": "uvx",
      "args": ["public-apis-mcp-server@latest"]
    }
  }
}
```

## 环境变量

无。开箱即用。

## 开发

```bash
git clone https://github.com/online111111/public-apis-mcp-server.git
cd public-apis-mcp-server
uv sync
uv run python -m public_apis_mcp_server.server
```

## 许可证

MIT
