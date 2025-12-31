"""
能力管理器 - 管理Atlas的所有能力
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class CapabilityManager:
    def __init__(self, capabilities_file: str = "core/self_evolution/capabilities.json"):
        self.capabilities_file = Path(capabilities_file)
        self.capabilities = self._load_capabilities()

    def _load_capabilities(self) -> Dict:
        """加载能力清单"""
        if self.capabilities_file.exists():
            with open(self.capabilities_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"capabilities": []}

    def _save_capabilities(self):
        """保存能力清单"""
        self.capabilities_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.capabilities_file, 'w', encoding='utf-8') as f:
            json.dump(self.capabilities, f, ensure_ascii=False, indent=2)

    def add_capability(self, name: str, description: str,
                       code_path: str, status: str = "pending") -> bool:
        """添加新能力"""
        capability = {
            "name": name,
            "description": description,
            "code_path": code_path,
            "status": status,  # pending, tested, active, failed
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # 检查是否已存在
        for cap in self.capabilities["capabilities"]:
            if cap["name"] == name:
                return False

        self.capabilities["capabilities"].append(capability)
        self._save_capabilities()
        return True

    def update_capability_status(self, name: str, status: str) -> bool:
        """更新能力状态"""
        for cap in self.capabilities["capabilities"]:
            if cap["name"] == name:
                cap["status"] = status
                cap["updated_at"] = datetime.now().isoformat()
                self._save_capabilities()
                return True
        return False

    def get_capability(self, name: str) -> Optional[Dict]:
        """获取指定能力"""
        for cap in self.capabilities["capabilities"]:
            if cap["name"] == name:
                return cap
        return None

    def list_capabilities(self, status: Optional[str] = None) -> List[Dict]:
        """列出所有能力"""
        if status:
            return [cap for cap in self.capabilities["capabilities"]
                    if cap["status"] == status]
        return self.capabilities["capabilities"]

    def remove_capability(self, name: str) -> bool:
        """移除能力"""
        original_len = len(self.capabilities["capabilities"])
        self.capabilities["capabilities"] = [
            cap for cap in self.capabilities["capabilities"]
            if cap["name"] != name
        ]
        if len(self.capabilities["capabilities"]) < original_len:
            self._save_capabilities()
            return True
        return False
