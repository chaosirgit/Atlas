"""
AI引擎模块
负责理解需求、设计工具方案、生成代码
"""
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests


class AIEngine:
    """AI引擎"""

    def __init__(
            self,
            model: str,
            api_key: str,
            base_url: str,
            temperature: float = 0.7
    ):
        """
        初始化AI引擎

        Args:
            model: 模型名称
            api_key: API密钥
            base_url: API基础URL
            temperature: 温度参数
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.temperature = temperature
        self.conversation_history: List[Dict[str, str]] = []

    def _call_llm(
            self,
            messages: List[Dict[str, str]],
            temperature: Optional[float] = None
    ) -> str:
        """
        调用LLM API

        Args:
            messages: 消息列表
            temperature: 温度参数

        Returns:
            LLM响应内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']
            return content

        except Exception as e:
            raise RuntimeError(f"LLM调用失败: {e}")

    def analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """
        分析需求，提取关键信息

        Args:
            requirement: 用户需求描述

        Returns:
            需求分析结果
        """
        system_prompt = """你是一个专业的需求分析专家。
请分析用户的需求，提取以下信息并以JSON格式返回：
{
    "tool_name": "工具名称（英文，驼峰命名）",
    "description": "工具功能描述（中文）",
    "parameters": {
        "参数名": {
            "type": "参数类型（str/int/float/bool/list/dict等）",
            "description": "参数说明",
            "required": true/false,
            "default": "默认值（如果非必需）"
        }
    },
    "return_type": "返回值类型",
    "complexity": "复杂度评估（简单/中等/复杂）",
    "dependencies": ["需要的第三方库"]
}

只返回JSON，不要其他内容。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"需求：{requirement}"}
        ]

        response = self._call_llm(messages, temperature=0.3)

        # 提取JSON
        try:
            # 尝试直接解析
            analysis = json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取代码块中的JSON
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                raise ValueError(f"无法解析需求分析结果: {response}")

        print(f"✓ 需求分析完成: {analysis['tool_name']}")
        return analysis

    def generate_code(self, analysis: Dict[str, Any]) -> str:
        """
        根据需求分析生成代码

        Args:
            analysis: 需求分析结果

        Returns:
            生成的代码（函数体）
        """
        system_prompt = """你是一个专业的Python开发专家。
根据需求分析生成高质量的Python函数实现代码。

要求：
1. 只生成函数体内的代码，不要包含函数定义
2. 代码要健壮，包含必要的错误处理
3. 添加适当的注释
4. 遵循PEP 8规范
5. 如果需要导入库，在代码开头注释说明
6. 代码要实用、可运行

只返回代码，不要其他解释。"""

        requirement_text = f"""
工具名称: {analysis['tool_name']}
功能描述: {analysis['description']}
参数定义: {json.dumps(analysis['parameters'], ensure_ascii=False, indent=2)}
返回类型: {analysis['return_type']}
依赖库: {', '.join(analysis.get('dependencies', []))}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": requirement_text}
        ]

        code = self._call_llm(messages, temperature=0.5)

        # 清理代码块标记
        import re
        code = re.sub(r'^```python\s*', '', code)
        code = re.sub(r'^```\s*', '', code)
        code = re.sub(r'\s*```$', '', code)
        code = code.strip()

        print(f"✓ 代码生成完成，共 {len(code.split(chr(10)))} 行")
        return code

    def review_code(self, code: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        审查生成的代码

        Args:
            code: 生成的代码
            analysis: 需求分析结果

        Returns:
            审查结果
        """
        system_prompt = """你是一个代码审查专家。
请审查以下代码，检查：
1. 代码正确性
2. 潜在的bug
3. 性能问题
4. 安全问题
5. 代码规范

返回JSON格式：
{
    "passed": true/false,
    "score": 0-100,
    "issues": ["问题列表"],
    "suggestions": ["改进建议"],
    "summary": "总体评价"
}

只返回JSON，不要其他内容。"""

        review_content = f"""
需求分析：
{json.dumps(analysis, ensure_ascii=False, indent=2)}

生成的代码：
```python
{code}
```
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": review_content}
        ]

        response = self._call_llm(messages, temperature=0.3)

        # 提取JSON
        try:
            review_result = json.loads(response)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                review_result = json.loads(json_match.group(1))
            else:
                raise ValueError(f"无法解析审查结果: {response}")

        print(f"✓ 代码审查完成，评分: {review_result['score']}/100")
        return review_result

    def improve_code(self, code: str, review_result: Dict[str, Any]) -> str:
        """
        根据审查结果改进代码

        Args:
            code: 原始代码
            review_result: 审查结果

        Returns:
            改进后的代码
        """
        if review_result['passed'] and review_result['score'] >= 80:
            print("✓ 代码质量良好，无需改进")
            return code

        system_prompt = """你是一个代码优化专家。
    根据审查意见改进代码，解决发现的问题。
    只返回改进后的完整代码，不要其他解释。"""
        improve_content = f"""
        原始代码：
        ```python
        {code}
        ```
        审查意见：
        问题: {', '.join(review_result['issues'])}
        建议: {', '.join(review_result['suggestions'])}

        请改进代码。"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": improve_content}
        ]

        improved_code = self._call_llm(messages, temperature=0.5)

        # 清理代码块标记
        import re
        improved_code = re.sub(r'^```python\s*', '', improved_code)
        improved_code = re.sub(r'^```\s*', '', improved_code)
        improved_code = re.sub(r'\s*```$', '', improved_code)
        improved_code = improved_code.strip()

        print(f"✓ 代码已改进")
        return improved_code

    def chat(self, message: str) -> str:
        """
        对话接口

        Args:
            message: 用户消息

        Returns:
            AI回复
        """
        self.conversation_history.append({"role": "user", "content": message})

        response = self._call_llm(self.conversation_history)

        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("✓ 对话历史已清空")
