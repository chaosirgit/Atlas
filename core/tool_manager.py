import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from .tools.code_executor import CodeExecutor
from .tools import web_reader
from .tools import location
from .tools import weather


class AtlasTools:
    """Atlas的工具集"""

    def __init__(self, workspace: str = "./atlas_workspace"):
        """初始化工具，设置工作空间"""
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)
        self.code_executor = CodeExecutor()  # 新增


    def _get_safe_path(self, path: str) -> Path:
        """确保路径在工作空间内，防止越界操作"""
        target = (self.workspace / path).resolve()
        if not str(target).startswith(str(self.workspace.resolve())):
            raise ValueError(f"路径越界: {path}")
        return target
    
    def read_web_content(self, url: str) -> Dict[str, Any]:
        """读取网页的主要文本内容"""
        return web_reader.read_web_content(url)

    def list_web_resources(self, url: str) -> Dict[str, Any]:
        """列出网页引用的所有资源"""
        return web_reader.list_web_resources(url)

    def get_current_location(self) -> Dict[str, Any]:
        """获取当前设备的地理位置(经纬度)"""
        return location.get_current_location()

    def get_weather(self, city: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定城市或当前位置的天气.
        如果未提供城市,则自动获取当前位置并查询.
        """
        adcode_result = None
        if city:
            # 1. 根据城市名获取adcode
            adcode_result = weather.get_city_adcode(city=city)
        else:
            # 2. 未提供城市,获取当前位置
            loc_result = self.get_current_location()
            if not loc_result.get("success"):
                return loc_result # 返回定位失败的信息
            
            # 3. 根据经纬度获取adcode
            lat = loc_result.get("latitude")
            lon = loc_result.get("longitude")
            adcode_result = weather.get_city_adcode(lat=lat, lon=lon)

        # 4. 根据adcode获取天气
        if adcode_result and adcode_result.get("success"):
            adcode = adcode_result.get("adcode")
            return weather.get_weather_by_adcode(adcode)
        
        # 返回获取adcode失败的信息
        return adcode_result if adcode_result else {"success": False, "message": "无法确定查询天气的城市"}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            target = self._get_safe_path(path)
            target.mkdir(parents=True, exist_ok=True)
            return {"success": True, "message": f"目录创建成功: {path}"}
        except Exception as e:
            return {"success": False, "message": f"创建失败: {str(e)}"}

    def delete_directory(self, path: str) -> Dict[str, Any]:
        """删除目录"""
        try:
            target = self._get_safe_path(path)
            if target.exists() and target.is_dir():
                shutil.rmtree(target)
                return {"success": True, "message": f"目录删除成功: {path}"}
            return {"success": False, "message": "目录不存在"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}

    def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """创建文件"""
        try:
            target = self._get_safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
            return {"success": True, "message": f"文件创建成功: {path}"}
        except Exception as e:
            return {"success": False, "message": f"创建失败: {str(e)}"}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            target = self._get_safe_path(path)
            if target.exists() and target.is_file():
                target.unlink()
                return {"success": True, "message": f"文件删除成功: {path}"}
            return {"success": False, "message": "文件不存在"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}

    def move_directory(self, src: str, dst: str) -> Dict[str, Any]:
        """移动目录"""
        try:
            src_path = self._get_safe_path(src)
            dst_path = self._get_safe_path(dst)
            shutil.move(str(src_path), str(dst_path))
            return {"success": True, "message": f"目录移动成功: {src} -> {dst}"}
        except Exception as e:
            return {"success": False, "message": f"移动失败: {str(e)}"}

    def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        """移动文件"""
        try:
            src_path = self._get_safe_path(src)
            dst_path = self._get_safe_path(dst)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            return {"success": True, "message": f"文件移动成功: {src} -> {dst}"}
        except Exception as e:
            return {"success": False, "message": f"移动失败: {str(e)}"}

    def write_file(self, path: str, content: str, mode: str = "w") -> Dict[str, Any]:
        """写入文件 (mode: 'w'覆盖, 'a'追加)"""
        try:
            target = self._get_safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, mode, encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "message": f"文件写入成功: {path}"}
        except Exception as e:
            return {"success": False, "message": f"写入失败: {str(e)}"}

    def read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            target = self._get_safe_path(path)
            if not target.exists():
                return {"success": False, "message": "文件不存在"}
            content = target.read_text(encoding='utf-8')
            return {"success": True, "content": content, "message": f"文件读取成功: {path}"}
        except Exception as e:
            return {"success": False, "message": f"读取失败: {str(e)}"}

    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """列出目录内容"""
        try:
            target = self._get_safe_path(path)
            if not target.exists():
                return {"success": False, "message": "目录不存在"}

            items = []
            for item in target.iterdir():
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })

            return {"success": True, "items": items, "message": f"目录列表: {path}"}
        except Exception as e:
            return {"success": False, "message": f"列表失败: {str(e)}"}

    def execute_python(self, code: str) -> Dict[str, Any]:
        """执行Python代码"""
        return self.code_executor.execute(code)