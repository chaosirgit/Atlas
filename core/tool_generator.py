"""
工具生成器模块
负责根据需求描述自动生成Python工具代码
"""
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ToolGenerator:
    """工具代码生成器"""

    def __init__(self, output_dir: Path):
        """
        初始化工具生成器

        Args:
            output_dir: 生成的工具代码输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_tool(
            self,
            tool_name: str,
            description: str,
            parameters: Dict[str, Any],
            code_body: str,
            author: str = "Atlas AI"
    ) -> Path:
        """
        生成工具代码文件

        Args:
            tool_name: 工具名称（函数名）
            description: 工具描述
            parameters: 参数定义字典
            code_body: 函数体代码
            author: 作者名称

        Returns:
            生成的文件路径
        """
        # 生成文件名（转换为snake_case）
        file_name = self._to_snake_case(tool_name) + ".py"
        file_path = self.output_dir / file_name

        # 生成完整代码
        code = self._generate_code_template(
            tool_name=tool_name,
            description=description,
            parameters=parameters,
            code_body=code_body,
            author=author
        )

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        return file_path

    def _generate_code_template(
            self,
            tool_name: str,
            description: str,
            parameters: Dict[str, Any],
            code_body: str,
            author: str
    ) -> str:
        """生成代码模板"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 生成参数类型注解
        param_annotations = self._generate_param_annotations(parameters)

        # 生成参数文档
        param_docs = self._generate_param_docs(parameters)

        template = f'''"""
{description}

Author: {author}
Created: {timestamp}
"""
from typing import Any, Dict, List, Optional


def {tool_name}({param_annotations}) -> Any:
    """
    {description}

    Args:
{param_docs}

    Returns:
        执行结果
    """
{self._indent_code(code_body, 4)}


# 工具元数据
TOOL_METADATA = {{
    "name": "{tool_name}",
    "description": "{description}",
    "parameters": {parameters},
    "author": "{author}",
    "created_at": "{timestamp}"
}}
'''
        return template

    def _to_snake_case(self, name: str) -> str:
        """将驼峰命名转换为下划线命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _generate_param_annotations(self, parameters: Dict[str, Any]) -> str:
        """生成参数类型注解"""
        if not parameters:
            return ""

        params = []
        for param_name, param_info in parameters.items():
            param_type = param_info.get('type', 'Any')
            required = param_info.get('required', True)

            if required:
                params.append(f"{param_name}: {param_type}")
            else:
                default = param_info.get('default', 'None')
                params.append(f"{param_name}: Optional[{param_type}] = {default}")

        return ", ".join(params)

    def _generate_param_docs(self, parameters: Dict[str, Any]) -> str:
        """生成参数文档字符串"""
        if not parameters:
            return "        无参数"

        docs = []
        for param_name, param_info in parameters.items():
            param_desc = param_info.get('description', '参数说明')
            docs.append(f"        {param_name}: {param_desc}")

        return "\n".join(docs)

    def _indent_code(self, code: str, spaces: int) -> str:
        """为代码添加缩进"""
        indent = " " * spaces
        lines = code.split("\n")
        return "\n".join(indent + line if line.strip() else "" for line in lines)
