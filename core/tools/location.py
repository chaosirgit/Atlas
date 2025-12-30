import requests
from typing import Dict, Any, Optional

def get_current_location() -> Dict[str, Any]:
    """
    通过IP地址获取当前设备的地理位置(经纬度).
    """
    try:
        # 使用 ip-api.com 进行IP定位
        response = requests.get("http://ip-api.com/json", timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            lat = data.get("lat")
            lon = data.get("lon")
            city = data.get("city")
            
            if lat and lon:
                return {
                    "success": True, 
                    "latitude": lat, 
                    "longitude": lon,
                    "city": city,
                    "message": f"通过IP定位成功: {city} ({lat}, {lon})"
                }

        return {"success": False, "message": f"IP定位失败: {data.get('message')}"}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"获取IP位置失败: {e}"}
    except Exception as e:
        return {"success": False, "message": f"处理位置信息时出错: {e}"}

if __name__ == '__main__':
    # for testing
    location = get_current_location()
    print(location)
