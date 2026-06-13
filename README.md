# Public APIs MCP Server

A Model Context Protocol (MCP) server wrapping multiple free public APIs — no API keys required. Built with FastMCP.

## Features

- 🌤️ **Weather** (Open-Meteo) — real-time weather and 7-day forecast by city or coordinates
- 🌍 **Country Info** (REST Countries) — population, currency, language, flag, timezone
- 📝 **Test Data** (JSONPlaceholder) — mock posts and users for development
- 🚀 **NASA Space Data** (NEO, APOD) — near-earth asteroid info and daily astronomy picture

All APIs are completely free. NASA uses a public `DEMO_KEY` with daily quota limits.

## Quick Start

```json
{
  "mcpServers": {
    "public-apis": {
      "command": "uvx",
      "args": ["public-apis-mcp-server"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_weather` | Current weather + forecast by city or lat/lon |
| `get_country_info` | Detailed country information |
| `get_posts` | Mock posts from JSONPlaceholder |
| `get_users` | Mock users from JSONPlaceholder |
| `get_asteroid_info` | NASA near-earth object data |
| `get_astronomy_picture` | NASA Astronomy Picture of the Day |

## Environment Variables

None required. Works out of the box.

## License

MIT
