"""
工具管理器模块
负责工具的注册、加载、调用和管理
"""
import importlib.util
import inspect
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime


class ToolManager:
    """工具管理器"""

    def __init__(self, tools_dir: Path):
        """
        初始化工具管理器

        Args:
            tools_dir: 工具目录路径
        """
        self.tools_dir = Path(tools_dir)
        self.tools_registry: Dict[str, Dict[str, Any]] = {}
        self._load_all_tools()

    def _load_all_tools(self):
        """加载所有工具"""
        if not self.tools_dir.exists():
            print(f"⚠ 工具目录不存在: {self.tools_dir}")
            return

        # 遍历所有Python文件
        for py_file in self.tools_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            self._load_tool_from_file(py_file)

        print(f"✓ 已加载 {len(self.tools_registry)} 个工具")

    def _load_tool_from_file(self, file_path: Path) -> bool:
        """
        从文件加载工具

        Args:
            file_path: 工具文件路径

        Returns:
            是否成功
        """
        try:
            # 动态导入模块
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 获取工具元数据
            if not hasattr(module, 'TOOL_METADATA'):
                print(f"⚠ 文件缺少TOOL_METADATA: {file_path.name}")
                return False

            metadata = module.TOOL_METADATA
            tool_name = metadata['name']

            # 获取工具函数
            if not hasattr(module, tool_name):
                print(f"⚠ 找不到函数 {tool_name} 在 {file_path.name}")
                return False

            tool_func = getattr(module, tool_name)

            # 注册工具
            self.tools_registry[tool_name] = {
                'function': tool_func,
                'metadata': metadata,
                'file_path': file_path,
                'module': module,
                'loaded_at': datetime.now().isoformat()
            }

            print(f"✓ 已加载工具: {tool_name}")
            return True

        except Exception as e:
            print(f"✗ 加载工具失败 {file_path.name}: {e}")
            return False

    def register_tool(
            self,
            tool_name: str,
            tool_func: Callable,
            metadata: Dict[str, Any],
            file_path: Optional[Path] = None
    ):
        """
        注册工具

        Args:
            tool_name: 工具名称
            tool_func: 工具函数
            metadata: 工具元数据
            file_path: 文件路径
        """
        self.tools_registry[tool_name] = {
            'function': tool_func,
            'metadata': metadata,
            'file_path': file_path,
            'module': None,
            'loaded_at': datetime.now().isoformat()
        }
        print(f"✓ 已注册工具: {tool_name}")

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self.tools_registry:
            raise ValueError(f"工具不存在: {tool_name}")

        tool_info = self.tools_registry[tool_name]
        tool_func = tool_info['function']

        try:
            result = tool_func(**kwargs)
            print(f"✓ 工具执行成功: {tool_name}")
            return result
        except Exception as e:
            print(f"✗ 工具执行失败 {tool_name}: {e}")
            raise

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息

        Args:
            tool_name: 工具名称

        Returns:
            工具信息字典
        """
        if tool_name not in self.tools_registry:
            return None

        tool_info = self.tools_registry[tool_name]
        return {
            'name': tool_name,
            'metadata': tool_info['metadata'],
            'file_path': str(tool_info['file_path']) if tool_info['file_path'] else None,
            'loaded_at': tool_info['loaded_at']
        }

    def list_tools(self) -> List[str]:
        """
        列出所有工具名称

        Returns:
            工具名称列表
        """
        return list(self.tools_registry.keys())

    def get_all_tools_info(self) -> Dict[str, Any]:
        """
        获取所有工具的信息

        Returns:
            所有工具信息字典
        """
        return {
            name: self.get_tool_info(name)
            for name in self.tools_registry.keys()
        }

    def reload_tool(self, tool_name: str) -> bool:
        """
        重新加载工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功
        """
        if tool_name not in self.tools_registry:
            print(f"⚠ 工具不存在: {tool_name}")
            return False

        tool_info = self.tools_registry[tool_name]
        file_path = tool_info.get('file_path')

        if not file_path or not file_path.exists():
            print(f"⚠ 工具文件不存在")
            return False

        # 删除旧的注册
        del self.tools_registry[tool_name]

        # 重新加载
        return self._load_tool_from_file(file_path)

    def export_tools_manifest(self, output_path: Path):
        """
        导出工具清单

        Args:
            output_path: 输出文件路径
        """
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'total_tools': len(self.tools_registry),
            'tools': self.get_all_tools_info()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f"✓ 工具清单已导出: {output_path}")
