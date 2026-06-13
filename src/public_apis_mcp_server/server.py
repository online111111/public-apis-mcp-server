#!/usr/bin/env python3
"""
Public APIs MCP Server — 基于 public-apis 项目挑选的免费公共 API
用 FastMCP 将多个公共 API 封装成 MCP 工具，供 LLM agent 直接调用。

包含:
1. Open-Meteo (天气) — 完全免费，无需 API key
2. REST Countries (国家信息) — 完全免费，无需 API key
3. JSONPlaceholder (测试数据) — 完全免费，无需 API key
4. NASA (太空数据) — 免费，需 API key（可选）
"""

import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="public-apis-server",
    version="1.0.0",
)

# ─── 配置 ───────────────────────────────────────────────────────────
OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
REST_COUNTRIES_BASE = "https://restcountries.com/v3.1"
JSON_PLACEHOLDER_BASE = "https://jsonplaceholder.typicode.com"
NASA_BASE = "https://api.nasa.gov"
NASA_KEY = "DEMO_KEY"  # 公开演示 key，也可用你自己的

# ─── 工具 1: Open-Meteo 天气 ────────────────────────────────────────
@mcp.tool()
async def get_weather(
    city: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone: str = "auto",
    forecast_days: int = 3,
) -> str:
    """获取指定城市或经纬度坐标的天气信息（当前 + 预报）。
    
    Args:
        city: 城市名称（如 "Beijing"、"Tokyo"、"London"）
        latitude: 纬度（当不提供 city 时使用）
        longitude: 经度（当不提供 city 时使用）
        timezone: 时区，默认 "auto"
        forecast_days: 预报天数，1-16，默认 3
    """
    # 如果提供了城市名，先地理编码
    if city:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=zh"
        async with httpx.AsyncClient() as client:
            try:
                geo_resp = await client.get(geo_url, timeout=10)
                geo_resp.raise_for_status()
                geo_data = geo_resp.json()
            except Exception as e:
                return f"地理编码失败: {e}"
            
            if not geo_data.get("results"):
                return f"未找到城市 '{city}'，请提供准确的英文名称或经纬度坐标。"
            loc = geo_data["results"][0]
            latitude = loc["latitude"]
            longitude = loc["longitude"]
            city = loc.get("name", city)
            country = loc.get("country", "")
            timezone = loc.get("timezone", "auto")

    url = (
        f"{OPEN_METEO_BASE}/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"current=temperature_2m,relative_humidity_2m,precipitation,"
        f"weather_code,wind_speed_10m,wind_direction_10m&"
        f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        f"weather_code&timezone={timezone}&forecast_days={forecast_days}"
    )

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"天气 API 请求失败: {e}"

    if data.get("error"):
        return f"天气 API 错误: {data.get('error')}"

    current = data.get("current", {})
    daily = data.get("daily", {})

    # 天气代码映射
    weather_map = {
        0: "晴", 1: "多云", 2: "多云", 3: "阴",
        45: "雾", 48: "雾",
        51: "小雨", 53: "小雨", 55: "中雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        80: "阵雨", 81: "阵雨", 82: "暴雨",
        95: "雷雨", 96: "雷雨伴冰雹", 99: "强雷雨",
    }

    def weather_desc(code):
        return weather_map.get(code, f"未知天气({code})")

    label = f"{city} ({country})" if country else city
    lines = [f"🌤️  {label} 天气报告"]
    lines.append(f"   温度: {current.get('temperature_2m', 'N/A')}°C")
    lines.append(f"   湿度: {current.get('relative_humidity_2m', 'N/A')}%")
    lines.append(f"   天气: {weather_desc(current.get('weather_code', 0))}")
    lines.append(f"   降水: {current.get('precipitation', 'N/A')}mm")
    lines.append(f"   风速: {current.get('wind_speed_10m', 'N/A')} km/h")
    lines.append(f"   风向: {current.get('wind_direction_10m', 'N/A')}°")

    if daily.get("time"):
        lines.append("")
        lines.append("📅 未来预报:")
        for i, date in enumerate(daily["time"]):
            lines.append(
                f"   {date}: 最高 {daily['temperature_2m_max'][i]}°C / "
                f"最低 {daily['temperature_2m_min'][i]}°C / "
                f"{weather_desc(daily['weather_code'][i])} / "
                f"降水 {daily['precipitation_sum'][i]}mm"
            )

    return "\n".join(lines)


# ─── 工具 2: REST Countries 国家信息 ────────────────────────────────
@mcp.tool()
async def get_country_info(name: str) -> str:
    """获取指定国家的详细信息（人口、面积、货币、语言、国旗等）。
    
    Args:
        name: 国家名称（中文或英文，如 "China"、"日本"、"Germany"、"CHN"）
    """
    async with httpx.AsyncClient() as client:
        # 先尝试精确匹配 name
        resp = await client.get(f"{REST_COUNTRIES_BASE}/name/{name}?fullText=true", timeout=10)
        
        if resp.status_code != 200:
            # 尝试用 alpha 代码（2 位或 3 位）
            resp = await client.get(f"{REST_COUNTRIES_BASE}/alpha/{name}", timeout=10)
        
        if resp.status_code != 200:
            # 尝试模糊搜索
            resp = await client.get(f"{REST_COUNTRIES_BASE}/name/{name}", timeout=10)
            if resp.status_code == 200:
                data_list = resp.json()
                # 如果是列表，尝试找到最匹配的
                if isinstance(data_list, list):
                    # 优先找完全匹配
                    for item in data_list:
                        if item.get("name", {}).get("common", "").lower() == name.lower():
                            data = item
                            break
                    else:
                        data = data_list[0]
                else:
                    data = data_list
            else:
                return f"未找到国家 '{name}'，请检查名称拼写。"
        else:
            data = resp.json()
            if isinstance(data, list):
                data = data[0]

    lines = [f"🌍 {data.get('name', {}).get('common', name)}"]
    lines.append(f"   官方名称: {data.get('name', {}).get('official', 'N/A')}")
    lines.append(f"   首都: {', '.join(data.get('capital', ['N/A']))}")
    pop = data.get('population', 'N/A')
    if isinstance(pop, int):
        lines.append(f"   人口: {pop:,}")
    else:
        lines.append(f"   人口: {pop}")
    area = data.get('area', 'N/A')
    if isinstance(area, (int, float)):
        lines.append(f"   面积: {area:,.0f} km²")
    else:
        lines.append(f"   面积: {area} km²")

    # 货币
    currencies = data.get("currencies", {})
    if currencies:
        cur_lines = [f"{v.get('name', '')} ({v.get('symbol', '')})" for v in currencies.values()]
        lines.append(f"   货币: {', '.join(cur_lines)}")

    # 语言
    languages = data.get("languages", {})
    if languages:
        lines.append(f"   语言: {', '.join(languages.values())}")

    # 时区
    tz = data.get("timezones", [])
    if tz:
        lines.append(f"   时区: {', '.join(tz)}")

    # 国旗 emoji
    flag = data.get("flag", "")
    if flag:
        lines.append(f"   国旗: {flag}")

    # 独立日期
    indep = data.get("independent", False)
    lines.append(f"   独立: {'是' if indep else '否（属地）'}")

    return "\n".join(lines)


# ─── 工具 3: JSONPlaceholder 测试数据 ──────────────────────────────
@mcp.tool()
async def get_posts(limit: int = 5, user_id: int = 0) -> str:
    """获取 JSONPlaceholder 测试平台的帖子列表。
    这是一个免费的在线 REST API 测试服务，返回模拟数据。
    
    Args:
        limit: 返回帖子数量，默认 5
        user_id: 可选，按用户 ID 筛选
    """
    url = f"{JSON_PLACEHOLDER_BASE}/posts?_limit={limit}"
    if user_id:
        url += f"&userId={user_id}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        posts = resp.json()

    lines = [f"📝 JSONPlaceholder 帖子 (共 {len(posts)} 条)"]
    for i, post in enumerate(posts, 1):
        lines.append(f"   [{i}] {post.get('title', 'N/A')}")
        body = post.get("body", "")
        preview = body[:100] + "..." if len(body) > 100 else body
        lines.append(f"       {preview}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_users() -> str:
    """获取 JSONPlaceholder 测试平台的用户列表。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{JSON_PLACEHOLDER_BASE}/users", timeout=10)
        users = resp.json()

    lines = [f"👥 JSONPlaceholder 用户 (共 {len(users)} 位)"]
    for i, user in enumerate(users, 1):
        name = user.get("name", "")
        username = user.get("username", "")
        email = user.get("email", "")
        company = user.get("company", {}).get("name", "")
        city = user.get("address", {}).get("city", "")
        lines.append(f"   [{i}] {name} (@{username})")
        lines.append(f"       邮箱: {email} | 公司: {company} | 城市: {city}")
        lines.append("")

    return "\n".join(lines)


# ─── 工具 4: NASA 太空数据 ─────────────────────────────────────────
@mcp.tool()
async def get_asteroid_info(date: str = "") -> str:
    """获取指定日期的近地小行星信息（NEO）。
    
    Args:
        date: 日期，格式 YYYY-MM-DD，默认今天
    """
    import datetime
    if not date:
        date = datetime.date.today().isoformat()

    url = (
        f"{NASA_BASE}/neo/rest/v1/feed?"
        f"start_date={date}&end_date={date}&api_key={NASA_KEY}"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        data = resp.json()

    if "error" in data:
        return f"NASA API 错误: {data['error']}"

    neos = data.get("near_earth_objects", {}).get(date, [])
    if not neos:
        return f"{date} 没有记录在近地小行星数据中。"

    lines = [f"🚀 NASA 近地小行星报告 ({date})"]
    lines.append(f"   共发现 {len(neos)} 颗小行星")
    lines.append("")

    for neo in neos[:10]:  # 最多展示 10 颗
        name = neo.get("name", "N/A")
        diameter_min = neo.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_min", "N/A")
        diameter_max = neo.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max", "N/A")
        hazardous = neo.get("is_potentially_hazardous_asteroid", False)
        velocity = neo.get("close_approach_data", [{}])[0].get("relative_velocity", {}).get("kilometers_per_second", "N/A")

        hazard_tag = " ⚠️ 潜在危险" if hazardous else ""
        lines.append(f"   • {name}{hazard_tag}")
        lines.append(f"     直径: {diameter_min:.3f} ~ {diameter_max:.3f} km")
        lines.append(f"     相对速度: {velocity} km/s")
        lines.append("")

    if len(neos) > 10:
        lines.append(f"   ... 还有 {len(neos) - 10} 颗（已截断）")

    return "\n".join(lines)


@mcp.tool()
async def get_astronomy_picture(date: str = "") -> str:
    """获取 NASA 每日天文图片（APOD）的信息。
    
    Args:
        date: 日期，格式 YYYY-MM-DD，默认今天
    """
    import datetime
    if not date:
        date = datetime.date.today().isoformat()

    url = f"{NASA_BASE}/planetary/apod?api_key={NASA_KEY}&date={date}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        data = resp.json()

    if "error" in data:
        return f"NASA API 错误: {data['error']}"

    lines = [f"🔭 NASA 每日天文图片 ({data.get('date', date)})"]
    lines.append(f"   标题: {data.get('title', 'N/A')}")
    lines.append(f"   类型: {data.get('media_type', 'N/A')}")
    lines.append(f"   版权: {data.get('copyright', 'N/A')}")
    lines.append("")
    desc = data.get("explanation", "")
    # 分段展示描述（避免太长）
    if len(desc) > 500:
        lines.append(f"   描述: {desc[:500]}...")
        lines.append(f"   (完整描述共 {len(desc)} 字)")
    else:
        lines.append(f"   描述: {desc}")

    url_link = data.get("url", "")
    if url_link:
        lines.append(f"   图片链接: {url_link}")

    return "\n".join(lines)


# ─── 资源 ───────────────────────────────────────────────────────────
@mcp.resource("public-apis://list", description="public-apis 项目所有免费 API 的分类列表")
async def list_apis() -> str:
    """列出所有可用的公共 API 工具及其用途。"""
    return """# Public APIs MCP Server — 可用工具列表

## 🌤️ 天气
- `get_weather(city, latitude, longitude)` — 获取城市或坐标的天气和预报（Open-Meteo）

## 🌍 国家信息
- `get_country_info(name)` — 获取国家详细信息（人口、面积、货币、语言等）（REST Countries）

## 📝 测试数据
- `get_posts(limit, user_id)` — 获取模拟帖子数据（JSONPlaceholder）
- `get_users()` — 获取模拟用户数据（JSONPlaceholder）

## 🚀 太空数据
- `get_asteroid_info(date)` — 获取近地小行星信息（NASA）
- `get_astronomy_picture(date)` — 获取每日天文图片（NASA APOD）

---
数据来源: https://github.com/public-apis/public-apis
所有 API 均免费，无需 API key（NASA 使用公开演示 key）。
"""


if __name__ == "__main__":
    mcp.run()
