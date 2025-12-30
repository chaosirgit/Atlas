import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any
import ast
import timeout_decorator


class CodeExecutor:
    """安全的Python代码执行器"""

    def __init__(self):
        # 允许的模块白名单
        self.allowed_modules = {
            'math', 'random', 'datetime', 'json', 'collections',
            'itertools', 'functools', 're', 'statistics',
            'numpy', 'pandas', 'matplotlib', 'seaborn'
        }

        # 禁止的操作
        self.forbidden_names = {
            'eval', 'exec', 'compile', '__import__',
            'open', 'input', 'file', 'os', 'sys',
            'subprocess', 'socket', 'urllib'
        }

    def _check_code_safety(self, code: str) -> tuple[bool, str]:
        """检查代码安全性"""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # 检查是否使用了禁止的名称
                if isinstance(node, ast.Name):
                    if node.id in self.forbidden_names:
                        return False, f"禁止使用: {node.id}"

                # 检查导入
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] not in self.allowed_modules:
                            return False, f"禁止导入模块: {alias.name}"

                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] not in self.allowed_modules:
                        return False, f"禁止导入模块: {node.module}"

            return True, "代码安全"

        except SyntaxError as e:
            return False, f"语法错误: {e}"

    @timeout_decorator.timeout(10, use_signals=False)
    def _run_code(self, code: str) -> tuple[str, str]:
        """执行代码并捕获输出"""
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # 预导入允许的模块
                import math
                import random
                import datetime
                import json
                import collections
                import itertools
                import functools
                import re
                import statistics

                # 创建受限的执行环境
                exec_globals = {
                    '__builtins__': {
                        'print': print,
                        'len': len,
                        'range': range,
                        'str': str,
                        'int': int,
                        'float': float,
                        'bool': bool,
                        'list': list,
                        'dict': dict,
                        'tuple': tuple,
                        'set': set,
                        'abs': abs,
                        'sum': sum,
                        'min': min,
                        'max': max,
                        'sorted': sorted,
                        'enumerate': enumerate,
                        'zip': zip,
                        'map': map,
                        'filter': filter,
                        'round': round,
                        'pow': pow,
                    },
                    # 预导入的模块
                    'math': math,
                    'random': random,
                    'datetime': datetime,
                    'json': json,
                    'collections': collections,
                    'itertools': itertools,
                    'functools': functools,
                    're': re,
                    'statistics': statistics,
                }

                exec(code, exec_globals)

            return stdout_capture.getvalue(), stderr_capture.getvalue()

        except Exception as e:
            return "", traceback.format_exc()

    def execute(self, code: str) -> Dict[str, Any]:
        """执行Python代码"""
        # 安全检查
        is_safe, message = self._check_code_safety(code)
        if not is_safe:
            return {
                'success': False,
                'message': f'代码安全检查失败: {message}',
                'output': '',
                'error': message
            }

        try:
            # 执行代码
            stdout, stderr = self._run_code(code)

            if stderr:
                return {
                    'success': False,
                    'message': '代码执行出错',
                    'output': stdout,
                    'error': stderr
                }
            else:
                return {
                    'success': True,
                    'message': '代码执行成功',
                    'output': stdout,
                    'error': ''
                }

        except timeout_decorator.TimeoutError:
            return {
                'success': False,
                'message': '代码执行超时（超过10秒）',
                'output': '',
                'error': '执行超时'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'执行失败: {str(e)}',
                'output': '',
                'error': traceback.format_exc()
            }
