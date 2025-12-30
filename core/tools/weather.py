import os
import requests
from typing import Dict, Any, Optional

AMAP_API_KEY = os.getenv("AMAP_API_KEY")
BASE_URL = "https://restapi.amap.com/v3"

def _make_amap_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    向高德地图API发起请求的通用函数.
    """
    if not AMAP_API_KEY or "your_amap_api_key" in AMAP_API_KEY:
        return {"success": False, "message": "高德API Key未配置或无效"}

    params["key"] = AMAP_API_KEY
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "1":
            return {"success": True, "data": data}
        else:
            # 高德API返回的错误信息在 info 字段
            error_info = data.get("info", "未知错误")
            return {"success": False, "message": f"高德API错误: {error_info}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"网络请求失败: {e}"}
    except Exception as e:
        return {"success": False, "message": f"处理API数据时出错: {e}"}


def get_city_adcode(city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
    """
    根据城市名或经纬度获取高德城市代码(adcode).
    优先使用经纬度查询.
    """
    if lat and lon:
        endpoint = "/geocode/regeo"
        params = {"location": f"{lon},{lat}"}
        result = _make_amap_request(endpoint, params)
        if result.get("success"):
            # 从返回数据中提取 adcode
            adcode = result["data"].get("regeocode", {}).get("addressComponent", {}).get("adcode")
            if adcode:
                return {"success": True, "adcode": adcode}
            else:
                return {"success": False, "message": "从经纬度未能解析出adcode"}
        return result # 返回包含错误信息的原始字典
    
    elif city:
        endpoint = "/geocode/geo"
        params = {"address": city}
        result = _make_amap_request(endpoint, params)
        if result.get("success"):
            geocodes = result["data"].get("geocodes")
            if geocodes:
                adcode = geocodes[0].get("adcode")
                return {"success": True, "adcode": adcode}
            else:
                return {"success": False, "message": f"未能找到城市 '{city}' 的adcode"}
        return result
        
    else:
        return {"success": False, "message": "必须提供城市名或经纬度"}


def get_weather_by_adcode(adcode: str) -> Dict[str, Any]:
    """
    根据高德城市代码(adcode)获取实时天气.
    """
    endpoint = "/weather/weatherInfo"
    params = {"city": adcode, "extensions": "base"} # base: 返回实况天气
    result = _make_amap_request(endpoint, params)

    if result.get("success"):
        lives = result["data"].get("lives")
        if lives:
            weather_info = lives[0]
            # 精简并格式化天气信息
            formatted_weather = {
                "城市": weather_info.get("city"),
                "天气": weather_info.get("weather"),
                "温度": f"{weather_info.get('temperature')}°C",
                "风向": f"{weather_info.get('winddirection')}风",
                "风力": f"{weather_info.get('windpower')}级",
                "湿度": f"{weather_info.get('humidity')}%",
                "更新时间": weather_info.get("reporttime")
            }
            return {"success": True, "weather": formatted_weather, "message": f"获取 {weather_info.get('city')} 天气成功"}
        else:
            return {"success": False, "message": "未能获取到天气实况"}
    return result

if __name__ == '__main__':
    # for testing
    # 1. by name
    adcode_result = get_city_adcode(city="北京")
    if adcode_result["success"]:
        weather_result = get_weather_by_adcode(adcode_result["adcode"])
        print(weather_result)

    # 2. by coords
    adcode_result_coords = get_city_adcode(lat=39.9042, lon=116.4074) # beijing
    if adcode_result_coords["success"]:
        weather_result_coords = get_weather_by_adcode(adcode_result_coords["adcode"])
        print(weather_result_coords)
