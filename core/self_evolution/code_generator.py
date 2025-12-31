"""
代码生成器 - 根据需求自动生成新能力代码
"""
import os
from pathlib import Path
from typing import Optional
from openai import OpenAI


class CodeGenerator:
    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "qwen-max"

    def generate_tool_code(self, capability_name: str,
                           capability_description: str,
                           requirements: str = "") -> Optional[str]:
        """生成工具代码"""

        prompt = f"""你是一个Python代码生成专家。请根据以下需求生成一个完整的Python工具类。

需求：
- 能力名称：{capability_name}
- 能力描述：{capability_description}
- 额外要求：{requirements}

代码要求：
1. 创建一个类，类名为{capability_name}Tool（首字母大写，驼峰命名）
2. 必须包含一个execute()方法作为主要功能入口
3. 包含完整的错误处理和日志记录
4. 添加详细的docstring文档
5. 如果需要外部API，使用环境变量存储密钥
6. 代码要符合PEP 8规范
7. 只返回Python代码，不要有任何解释文字
8. 代码开头要有完整的import语句

请直接生成代码："""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的Python代码生成助手，只输出代码，不输出任何解释。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            code = response.choices[0].message.content.strip()

            # 清理代码块标记
            if code.startswith("```python"):
                code = code[9:]
            if code.startswith("```"):
                code = code[3:]
            if code.endswith("```"):
                code = code[:-3]

            return code.strip()

        except Exception as e:
            print(f"代码生成失败: {e}")
            return None

    def save_code(self, code: str, file_path: str) -> bool:
        """保存代码到文件"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(code)

            return True
        except Exception as e:
            print(f"保存代码失败: {e}")
            return False

    def generate_and_save(self, capability_name: str,
                          capability_description: str,
                          output_dir: str = "core/tools/generated",
                          requirements: str = "") -> Optional[str]:
        """生成并保存代码"""

        # 生成代码
        code = self.generate_tool_code(capability_name, capability_description, requirements)
        if not code:
            return None

        # 构建文件路径
        file_name = f"{capability_name.lower()}_tool.py"
        file_path = Path(output_dir) / file_name

        # 保存代码
        if self.save_code(code, str(file_path)):
            return str(file_path)

        return None
