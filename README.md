# Public APIs MCP Server

一个零配置的 MCP 服务，包装 11 个免费公共 API，**无需 API key，开箱即用**。

A zero-config MCP server wrapping 11 free public APIs. **No API keys required, works out of the box.**

---

## 服务配置 / Server Config

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

### 环境变量 / Environment Variables

无。无需任何配置即可使用。
None. Truly zero configuration.

---

## 工具清单 / Available Tools

### 🌤️ 天气查询 — `get_weather`
基于 Open-Meteo，查询实时天气及 7 天预报。
Real-time weather and 7-day forecast via Open-Meteo (free, no key).

```json
{
  "arguments": { "city": "Beijing" }
}
```

### 🌍 国家信息 — `get_country_info`
查询国家详情：人口、货币、语言、国旗等。
Country details: population, currency, languages, flag via REST Countries.

```json
{
  "arguments": { "name": "Japan" }
}
```

### 🚀 近地小行星 — `get_asteroid_info`
查询 NASA NEO 小行星数据（按日期）。
Near-Earth asteroid data from NASA NEO by date.

```json
{
  "arguments": { "date": "2026-06-13" }
}
```

### 🔭 每日天文图片 — `get_astronomy_picture`
NASA APOD — 每日天文图片及说明。
NASA Astronomy Picture of the Day with explanation.

### 📍 IP 地理定位 — `get_ip_geolocation`
通过 ip-api.com 查询 IP 地址的地理位置（城市、国家、经纬度等）。
IP geolocation via ip-api.com (city, country, coordinates, ISP).

```json
{
  "arguments": { "ip": "8.8.8.8" }
}
```

### 📖 英文词典 — `lookup_word`
Free Dictionary API — 单词定义、音标、词性、例句。
English word definitions, phonetics, parts of speech, examples.

```json
{
  "arguments": { "word": "serendipity" }
}
```

### 🎯 随机活动 — `get_random_activity`
Bored API — 推荐随机活动，可按类型筛选。
Random activity recommendation, filterable by type.

```json
{
  "arguments": { "type": "recreational" }
}
```

### 📄 学术论文搜索 — `search_arxiv`
arXiv API — 搜索物理、数学、计算机科学等论文。
Search arXiv papers across physics, math, CS, and more.

```json
{
  "arguments": { "query": "transformer attention", "max_results": 5 }
}
```

### 📚 图书搜索 — `search_books`
Open Library — 按书名、作者、ISBN 搜索图书。
Search books by title, author, or ISBN via Open Library.

```json
{
  "arguments": { "query": "dune", "limit": 5 }
}
```

### ☀️ 日出日落 — `get_sun_times`
Sunrise-Sunset API — 查询日出日落、天文晨昏时间。
Sunrise, sunset, dawn, dusk times for any location.

```json
{
  "arguments": {
    "lat": 39.9042,
    "lng": 116.4074
  }
}
```

### 💬 测试数据 — `get_posts` / `get_users`
JSONPlaceholder — 获取模拟帖子/用户数据，适合开发和测试。
Fetch mock posts and user data for development/testing.

---

## 关于 API 限制 / API Limits

| 工具 | 来源 | 限制 |
|------|------|------|
| `get_weather` | Open-Meteo | 完全免费，每分钟 10,000 请求 |
| `get_country_info` | REST Countries | 完全免费 |
| `get_asteroid_info` | NASA NEO | 内置 `DEMO_KEY`，每小时 30 请求 |
| `get_astronomy_picture` | NASA APOD | 同上 |
| `get_ip_geolocation` | ip-api.com | 完全免费，每分钟 45 请求 |
| `lookup_word` | Free Dictionary | 完全免费 |
| `get_random_activity` | Bored API | 完全免费 |
| `search_arxiv` | arXiv API | 完全免费，合理使用 |
| `search_books` | Open Library | 完全免费，合理使用 |
| `get_sun_times` | Sunrise-Sunset | 完全免费 |
| `get_posts` / `get_users` | JSONPlaceholder | 完全免费 |

> 所有工具均使用 HTTP API，无需任何 API key 或注册。
> All tools use public HTTP APIs — no registration or API key needed.

---

## 本地开发 / Local Development

```bash
git clone https://github.com/online111111/public-apis-mcp-server.git
cd public-apis-mcp-server
uv sync
uv run python -m public_apis_mcp_server.server
```

## 许可证 / License

MIT
