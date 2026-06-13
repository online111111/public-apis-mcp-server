#!/usr/bin/env python3
"""
Public APIs MCP Server — 基于 public-apis 项目挑选的免费公共 API
用 FastMCP 将多个公共 API 封装成 MCP 工具，供 LLM agent 直接调用。

全部 zero-config，无需任何 API key（有些有免费额度限制）。

工具清单:
1. Open-Meteo (天气) — 完全免费，无需 API key
2. REST Countries (国家信息) — 完全免费，无需 API key
3. JSONPlaceholder (测试数据) — 完全免费，无需 API key
4. NASA (太空数据) — 免费，需 API key（可选，内置 DEMO_KEY）
5. ip-api.com (IP 地理定位) — 完全免费，无需 API key
6. Free Dictionary (词典) — 完全免费，无需 API key
7. Bored API (活动推荐) — 完全免费，无需 API key
8. arXiv (学术论文搜索) — 完全免费，无需 API key
9. Open Library (图书搜索) — 完全免费，无需 API key
10. Sunrise Sunset (日出日落时间) — 完全免费，无需 API key
"""

import datetime
import json
import re
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="public-apis-server",
    version="1.1.0",
)

# ─── 常量 ───────────────────────────────────────────────────────────
OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
REST_COUNTRIES_BASE = "https://restcountries.com/v3.1"
JSON_PLACEHOLDER_BASE = "https://jsonplaceholder.typicode.com"
NASA_BASE = "https://api.nasa.gov"
NASA_KEY = "DEMO_KEY"  # 公开演示 key，也可用你自己的

# ─── 工具函数 ───────────────────────────────────────────────────────

def _weather_desc(code: int) -> str:
    """将 WMO 天气代码转为中文描述"""
    weather_map = {
        0: "晴", 1: "多云", 2: "多云", 3: "阴",
        45: "雾", 48: "雾",
        51: "小雨", 53: "小雨", 55: "中雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        80: "阵雨", 81: "阵雨", 82: "暴雨",
        95: "雷雨", 96: "雷雨伴冰雹", 99: "强雷雨",
    }
    return weather_map.get(code, f"未知天气({code})")


def _fmt(text: str, indent: int = 4) -> str:
    return f"{' ' * indent}{text}"


# ═══════════════════════════════════════════════════════════════════
# 工具 1: Open-Meteo 天气
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_weather(
    city: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
    timezone: str = "auto",
    forecast_days: int = 3,
) -> str:
    """获取指定城市或经纬度坐标的天气信息（当前 + 预报）。
    数据来源: Open-Meteo，完全免费。
    
    Args:
        city: 城市名称（如 "Beijing"、"Tokyo"、"London"，中英文均可）
        latitude: 纬度（不提供 city 时使用）
        longitude: 经度（不提供 city 时使用）
        timezone: 时区，默认 "auto"
        forecast_days: 预报天数，1-16，默认 3
    """
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

    label = f"{city} ({country})" if country else city
    lines = [f"🌤️  {label} 天气报告"]
    lines.append(_fmt(f"温度: {current.get('temperature_2m', 'N/A')}°C"))
    lines.append(_fmt(f"湿度: {current.get('relative_humidity_2m', 'N/A')}%"))
    lines.append(_fmt(f"天气: {_weather_desc(current.get('weather_code', 0))}"))
    lines.append(_fmt(f"降水: {current.get('precipitation', 'N/A')}mm"))
    lines.append(_fmt(f"风速: {current.get('wind_speed_10m', 'N/A')} km/h"))

    if daily.get("time"):
        lines.append("")
        lines.append("📅 未来预报:")
        for i, date in enumerate(daily["time"]):
            lines.append(_fmt(
                f"{date}: 最高 {daily['temperature_2m_max'][i]}°C / "
                f"最低 {daily['temperature_2m_min'][i]}°C / "
                f"{_weather_desc(daily['weather_code'][i])} / "
                f"降水 {daily['precipitation_sum'][i]}mm"
            ))

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 2: REST Countries 国家信息
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_country_info(name: str) -> str:
    """获取指定国家的详细信息（人口、面积、货币、语言、国旗等）。
    数据来源: REST Countries，完全免费。
    
    Args:
        name: 国家名称（中文或英文，如 "China"、"日本"、"Germany"、"CHN"）
    """
    async with httpx.AsyncClient() as client:
        # 先尝试精确匹配
        resp = await client.get(f"{REST_COUNTRIES_BASE}/name/{name}?fullText=true", timeout=10)
        if resp.status_code != 200:
            resp = await client.get(f"{REST_COUNTRIES_BASE}/alpha/{name}", timeout=10)
        if resp.status_code != 200:
            resp = await client.get(f"{REST_COUNTRIES_BASE}/name/{name}", timeout=10)
            if resp.status_code == 200:
                data_list = resp.json()
                if isinstance(data_list, list):
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
    lines.append(_fmt(f"官方名称: {data.get('name', {}).get('official', 'N/A')}"))
    lines.append(_fmt(f"首都: {', '.join(data.get('capital', ['N/A']))}"))

    pop = data.get("population", "N/A")
    lines.append(_fmt(f"人口: {pop:,}" if isinstance(pop, int) else f"人口: {pop}"))

    area = data.get("area", "N/A")
    lines.append(_fmt(f"面积: {area:,.0f} km²" if isinstance(area, (int, float)) else f"面积: {area} km²"))

    currencies = data.get("currencies", {})
    if currencies:
        cur_lines = [f"{v.get('name', '')} ({v.get('symbol', '')})" for v in currencies.values()]
        lines.append(_fmt(f"货币: {', '.join(cur_lines)}"))

    languages = data.get("languages", {})
    if languages:
        lines.append(_fmt(f"语言: {', '.join(languages.values())}"))

    tz = data.get("timezones", [])
    if tz:
        lines.append(_fmt(f"时区: {', '.join(tz)}"))

    flag = data.get("flag", "")
    if flag:
        lines.append(_fmt(f"国旗: {flag}"))

    lines.append(_fmt(f"独立: {'是' if data.get('independent', False) else '否（属地）'}"))
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 3: JSONPlaceholder 测试数据
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_posts(limit: int = 5, user_id: int = 0) -> str:
    """获取 JSONPlaceholder 测试平台的帖子列表（模拟数据）。
    
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
        lines.append(f"  [{i}] {post.get('title', 'N/A')}")
        body = post.get("body", "")
        preview = body[:100] + "..." if len(body) > 100 else body
        lines.append(f"       {preview}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_users() -> str:
    """获取 JSONPlaceholder 测试平台的用户列表（模拟数据）。"""
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
        lines.append(f"  [{i}] {name} (@{username})")
        lines.append(f"       邮箱: {email} | 公司: {company} | 城市: {city}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 4: NASA 太空数据
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_asteroid_info(date: str = "") -> str:
    """获取指定日期的近地小行星信息（NEO）。
    数据来源: NASA，使用公开 DEMO_KEY（每小时 30 次限制）。
    
    Args:
        date: 日期，格式 YYYY-MM-DD，默认今天
    """
    if not date:
        date = datetime.date.today().isoformat()

    url = f"{NASA_BASE}/neo/rest/v1/feed?start_date={date}&end_date={date}&api_key={NASA_KEY}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        data = resp.json()

    if "error" in data:
        return f"NASA API 错误: {data['error']}"

    neos = data.get("near_earth_objects", {}).get(date, [])
    if not neos:
        return f"{date} 没有记录在近地小行星数据中。"

    lines = [f"🚀 NASA 近地小行星报告 ({date})"]
    lines.append(_fmt(f"共发现 {len(neos)} 颗小行星"))
    lines.append("")

    for neo in neos[:10]:
        name = neo.get("name", "N/A")
        diam_min = neo.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_min", "N/A")
        diam_max = neo.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max", "N/A")
        hazardous = neo.get("is_potentially_hazardous_asteroid", False)
        velocity = neo.get("close_approach_data", [{}])[0].get("relative_velocity", {}).get("kilometers_per_second", "N/A")

        tag = " ⚠️ 潜在危险" if hazardous else ""
        lines.append(f"  • {name}{tag}")
        lines.append(_fmt(f"直径: {diam_min:.3f} ~ {diam_max:.3f} km"))
        lines.append(_fmt(f"相对速度: {velocity} km/s"))
        lines.append("")

    if len(neos) > 10:
        lines.append(_fmt(f"... 还有 {len(neos) - 10} 颗（已截断）"))

    return "\n".join(lines)


@mcp.tool()
async def get_astronomy_picture(date: str = "") -> str:
    """获取 NASA 每日天文图片（APOD）的信息。
    数据来源: NASA，使用公开 DEMO_KEY（每小时 30 次限制）。
    
    Args:
        date: 日期，格式 YYYY-MM-DD，默认今天
    """
    if not date:
        date = datetime.date.today().isoformat()

    url = f"{NASA_BASE}/planetary/apod?api_key={NASA_KEY}&date={date}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        data = resp.json()

    if "error" in data:
        return f"NASA API 错误: {data['error']}"

    lines = [f"🔭 NASA 每日天文图片 ({data.get('date', date)})"]
    lines.append(_fmt(f"标题: {data.get('title', 'N/A')}"))
    lines.append(_fmt(f"类型: {data.get('media_type', 'N/A')}"))
    lines.append(_fmt(f"版权: {data.get('copyright', 'N/A')}"))
    lines.append("")
    desc = data.get("explanation", "")
    if len(desc) > 500:
        lines.append(_fmt(f"描述: {desc[:500]}..."))
        lines.append(_fmt(f"(完整描述共 {len(desc)} 字)"))
    else:
        lines.append(_fmt(f"描述: {desc}"))

    url_link = data.get("url", "")
    if url_link:
        lines.append(_fmt(f"图片链接: {url_link}"))

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 5: IP 地理定位 (ip-api.com)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_ip_geolocation(ip: str = "") -> str:
    """查询 IP 地址的地理位置信息（国家、城市、ISP 等）。
    数据来源: ip-api.com，完全免费，无需 API key。
    
    Args:
        ip: IP 地址，不传则查询本机公网 IP
    """
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,lat,lon,timezone,query" if ip else "http://ip-api.com/json/?fields=status,message,country,regionName,city,isp,org,as,lat,lon,timezone,query"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            data = resp.json()
        except Exception as e:
            return f"IP 查询失败: {e}"

    if data.get("status") == "fail":
        return f"IP 查询失败: {data.get('message', '未知错误')}"

    lines = [f"📍 IP 地理位置"]
    lines.append(_fmt(f"IP 地址: {data.get('query', 'N/A')}"))
    lines.append(_fmt(f"国家: {data.get('country', 'N/A')}"))
    lines.append(_fmt(f"地区: {data.get('regionName', 'N/A')}"))
    lines.append(_fmt(f"城市: {data.get('city', 'N/A')}"))
    lines.append(_fmt(f"ISP: {data.get('isp', 'N/A')}"))
    lines.append(_fmt(f"组织: {data.get('org', 'N/A')}"))
    lines.append(_fmt(f"ASN: {data.get('as', 'N/A')}"))
    lines.append(_fmt(f"坐标: {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}"))
    lines.append(_fmt(f"时区: {data.get('timezone', 'N/A')}"))
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 6: Free Dictionary (词典)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def lookup_word(word: str) -> str:
    """查询英文单词的定义、音标、词性、例句等。
    数据来源: Free Dictionary API (dictionaryapi.dev)，完全免费。
    
    Args:
        word: 要查询的英文单词
    """
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            if resp.status_code == 404:
                return f"未找到单词 '{word}'，请检查拼写。"
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"词典查询失败: {e}"

    if not data or not isinstance(data, list):
        return f"未找到单词 '{word}'。"

    entry = data[0]
    word_text = entry.get("word", word)
    phonetic = entry.get("phonetic", "") or entry.get("phonetics", [{}])[0].get("text", "")
    lines = [f"📖 {word_text}{f' ({phonetic})' if phonetic else ''}"]

    for meaning in entry.get("meanings", []):
        part_of_speech = meaning.get("partOfSpeech", "")
        for i, definition in enumerate(meaning.get("definitions", [])[:3], 1):
            def_text = definition.get("definition", "")
            lines.append(f"  {part_of_speech}.{i} {def_text}")
            example = definition.get("example")
            if example:
                lines.append(f"      例: \"{example}\"")
            synonyms = definition.get("synonyms", [])[:3]
            if synonyms:
                lines.append(f"      近义词: {', '.join(synonyms)}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 7: Bored API (活动推荐)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_random_activity(
    type: str = "",
    participants: int = 0,
    min_price: float = 0.0,
    max_price: float = 1.0,
) -> str:
    """获取随机活动推荐，适合打发时间或寻找灵感。
    数据来源: Bored API (boredapi.com)，完全免费。
    
    Args:
        type: 活动类型，可选: education/recreational/social/diy/cooking/music/busywork/relaxation/charity
        participants: 参与人数（0 表示不限）
        min_price: 最低花费 (0.0 - 1.0)
        max_price: 最高花费 (0.0 - 1.0)
    """
    params = {}
    valid_types = {"education", "recreational", "social", "diy", "cooking", "music", "busywork", "relaxation", "charity"}
    if type and type.lower() in valid_types:
        params["type"] = type.lower()
    if participants > 0:
        params["participants"] = participants
    if min_price > 0.0:
        params["minprice"] = min_price
    if max_price < 1.0:
        params["maxprice"] = max_price

    url = "https://www.boredapi.com/api/activity"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url += "?" + qs

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"活动推荐获取失败: {e}"

    if data.get("error"):
        return f"没有找到符合条件的活动，试试放宽筛选条件。"

    lines = ["🎯 推荐活动"]
    lines.append(_fmt(f"活动: {data.get('activity', 'N/A')}"))
    lines.append(_fmt(f"类型: {data.get('type', 'N/A')}"))
    lines.append(_fmt(f"人数: {data.get('participants', 1)} 人"))
    pr = data.get("price", 0.0)
    lines.append(_fmt(f"花费: {'免费' if pr == 0 else f'${pr:.1f} 级别' if pr <= 0.3 else f'${pr:.1f} 级别' if pr <= 0.5 else '$0.5+'}" ))
    acc = data.get("accessibility", 0.0)
    lines.append(_fmt(f"难度: {'简单' if acc <= 0.2 else '中等' if acc <= 0.5 else '困难'}"))
    link = data.get("link", "")
    if link:
        lines.append(_fmt(f"链接: {link}"))
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 8: arXiv 学术论文搜索
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_arxiv(
    query: str,
    max_results: int = 5,
    sort_by: str = "relevance",
    category: str = "",
) -> str:
    """搜索 arXiv 学术论文（物理学、数学、计算机科学、经济学等）。
    数据来源: arXiv API，完全免费。
    
    Args:
        query: 搜索关键词
        max_results: 返回结果数，默认 5，最大 20
        sort_by: 排序方式，可选 relevance / lastUpdatedDate / submittedDate
        category: 分类筛选，如 cs.AI (人工智能)、math (数学)、physics (物理)
    """
    max_results = min(max_results, 20)
    search_query = query
    if category:
        search_query = f"({query})+AND+cat:{category}"

    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query=all:{search_query}&"
        f"max_results={max_results}&"
        f"sortBy={sort_by}&sortOrder=descending"
    )

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=30)
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            return f"arXiv 搜索失败: {e}"

    # 简易 XML 解析（无需额外依赖）
    lines = [f"📄 arXiv 搜索结果: \"{query}\""]

    entries = re.findall(r"<entry>(.*?)</entry>", text, re.DOTALL)
    if not entries:
        lines.append("  没有找到相关论文。")

    for i, entry in enumerate(entries[:max_results], 1):
        title = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        title = title.group(1).strip().replace("\n", " ") if title else "N/A"

        authors = re.findall(r"<name>(.*?)</name>", entry)
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += f" et al."

        summary = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        summary = summary.group(1).strip().replace("\n", " ")[:200] + "..." if summary else ""

        published = re.search(r"<published>(.*?)</published>", entry)
        published = published.group(1)[:10] if published else ""

        link = re.search(r'<id>(.*?)</id>', entry)
        link = link.group(1) if link else ""

        lines.append(f"\n  [{i}] {title}")
        lines.append(_fmt(f"作者: {author_str}"))
        if summary:
            lines.append(_fmt(f"摘要: {summary}"))
        lines.append(_fmt(f"日期: {published} | 链接: {link}"))

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 9: Open Library (图书搜索)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def search_books(
    query: str,
    limit: int = 5,
) -> str:
    """搜索图书信息（标题、作者、出版年份、封面等）。
    数据来源: Open Library，完全免费。
    
    Args:
        query: 搜索关键词（书名、作者等）
        limit: 返回结果数，默认 5，最大 20
    """
    limit = min(limit, 20)
    url = f"https://openlibrary.org/search.json?q={query}&limit={limit}"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"图书搜索失败: {e}"

    docs = data.get("docs", [])
    total = data.get("numFound", 0)
    lines = [f"📚 图书搜索结果: \"{query}\" (共 {total:,} 条)"]

    if not docs:
        lines.append("  没有找到相关图书。")
        return "\n".join(lines)

    for i, doc in enumerate(docs[:limit], 1):
        title = doc.get("title", "N/A")
        authors = doc.get("author_name", [])
        author_str = ", ".join(authors[:3]) if authors else "未知作者"
        year = doc.get("first_publish_year", "")
        isbn = doc.get("isbn", [])
        isbn_str = isbn[0] if isbn else ""
        pages = doc.get("number_of_pages_median", "")
        cover_id = doc.get("cover_i", "")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""

        lines.append(f"\n  [{i}] {title}")
        lines.append(_fmt(f"作者: {author_str}  |  出版年份: {year}"))
        if pages:
            lines.append(_fmt(f"页数: {pages}"))
        if isbn_str:
            lines.append(_fmt(f"ISBN: {isbn_str}"))
        if cover_url:
            lines.append(_fmt(f"封面: {cover_url}"))

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 工具 10: Sunrise Sunset (日出日落时间)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def get_sun_times(
    latitude: float,
    longitude: float,
    date: str = "",
) -> str:
    """获取指定地点和日期的日出、日落、晨光、暮光等天文时间。
    数据来源: Sunrise-Sunset API，完全免费。
    
    Args:
        latitude: 纬度
        longitude: 经度
        date: 日期，格式 YYYY-MM-DD，默认今天
    """
    if not date:
        date = datetime.date.today().isoformat()

    url = f"https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&date={date}&formatted=0"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return f"日出日落查询失败: {e}"

    if data.get("status") != "OK":
        return f"查询失败: {data.get('status', '未知错误')}"

    results = data.get("results", {})

    def _fmt_utc(iso_str: str) -> str:
        """将 ISO 时间格式化为 HH:MM UTC"""
        if not iso_str:
            return "N/A"
        try:
            dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.strftime("%H:%M UTC")
        except Exception:
            return iso_str

    lines = [f"☀️ 天文时间 ({latitude}, {longitude})"]
    lines.append(_fmt(f"日期: {date}"))
    lines.append("")
    lines.append(_fmt(f"日出: {_fmt_utc(results.get('sunrise', ''))}"))
    lines.append(_fmt(f"日落: {_fmt_utc(results.get('sunset', ''))}"))
    lines.append(_fmt(f"天文晨光始: {_fmt_utc(results.get('astronomical_twilight_begin', ''))}"))
    lines.append(_fmt(f"天文暮光终: {_fmt_utc(results.get('astronomical_twilight_end', ''))}"))
    lines.append(_fmt(f"航海晨光始: {_fmt_utc(results.get('nautical_twilight_begin', ''))}"))
    lines.append(_fmt(f"航海暮光终: {_fmt_utc(results.get('nautical_twilight_end', ''))}"))
    lines.append(_fmt(f"民用晨光始: {_fmt_utc(results.get('civil_twilight_begin', ''))}"))
    lines.append(_fmt(f"民用暮光终: {_fmt_utc(results.get('civil_twilight_end', ''))}"))
    day_length = results.get("day_length", 0)
    if day_length:
        hours = int(day_length // 3600)
        minutes = int((day_length % 3600) // 60)
        lines.append(_fmt(f"日照时长: {hours}小时{minutes}分钟"))
    solar_noon = _fmt_utc(results.get("solar_noon", ""))
    if solar_noon:
        lines.append(_fmt(f"正午: {solar_noon}"))

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 资源: 服务总览
# ═══════════════════════════════════════════════════════════════════

@mcp.resource("public-apis://list", description="所有可用工具列表")
async def list_apis() -> str:
    """列出所有可用的公共 API 工具及其用途。"""
    return """# Public APIs MCP Server v1.1.0 — 全部工具列表

## 🌤️ 天气
- `get_weather(city, latitude, longitude...)` — 实时天气及预报（Open-Meteo）

## 🌍 国家信息
- `get_country_info(name)` — 国家详情（REST Countries）

## 📝 测试数据
- `get_posts(limit, user_id)` — 模拟帖子（JSONPlaceholder）
- `get_users()` — 模拟用户（JSONPlaceholder）

## 🚀 太空数据
- `get_asteroid_info(date)` — 近地小行星（NASA）
- `get_astronomy_picture(date)` — 每日天文图片（NASA APOD）

## 📍 IP 地理定位
- `get_ip_geolocation(ip)` — 查询 IP 地址位置（ip-api.com）

## 📖 词典
- `lookup_word(word)` — 英文单词定义、音标、例句（Free Dictionary API）

## 🎯 活动推荐
- `get_random_activity(type, participants, price...)` — 随机活动推荐（Bored API）

## 📄 学术论文
- `search_arxiv(query, max_results, category)` — 搜索 arXiv 论文

## 📚 图书搜索
- `search_books(query, limit)` — 搜索图书信息（Open Library）

## ☀️ 天文时间
- `get_sun_times(latitude, longitude, date)` — 日出日落/晨光暮光

---
所有 API 均免费，零配置，无需 API key。
数据来源: https://github.com/public-apis/public-apis
"""


if __name__ == "__main__":
    mcp.run()
