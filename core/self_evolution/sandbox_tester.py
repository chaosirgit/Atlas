"""
沙盒测试器 - 在隔离环境中测试新生成的代码
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional
import tempfile
import shutil


class SandboxTester:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def test_syntax(self, file_path: str) -> Tuple[bool, str]:
        """测试代码语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            compile(code, file_path, 'exec')
            return True, "语法检查通过"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        except Exception as e:
            return False, f"检查失败: {e}"

    def test_import(self, file_path: str) -> Tuple[bool, str]:
        """测试代码能否正常导入"""
        try:
            # 创建临时测试脚本
            test_script = f"""
import sys
sys.path.insert(0, '{Path(file_path).parent}')

try:
    module_name = '{Path(file_path).stem}'
    __import__(module_name)
    print("IMPORT_SUCCESS")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}")
    sys.exit(1)
"""

            # 在子进程中执行
            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if "IMPORT_SUCCESS" in result.stdout:
                return True, "导入测试通过"
            else:
                return False, f"导入失败: {result.stdout + result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "导入测试超时"
        except Exception as e:
            return False, f"测试失败: {e}"

    def test_basic_execution(self, file_path: str, class_name: str) -> Tuple[bool, str]:
        """测试基本执行"""
        try:
            test_script = f"""
import sys
sys.path.insert(0, '{Path(file_path).parent}')

try:
    module_name = '{Path(file_path).stem}'
    module = __import__(module_name)

    # 尝试实例化类
    tool_class = getattr(module, '{class_name}')
    tool_instance = tool_class()

    # 检查是否有execute方法
    if hasattr(tool_instance, 'execute'):
        print("EXECUTION_TEST_SUCCESS")
    else:
        print("EXECUTION_ERROR: 缺少execute方法")
        sys.exit(1)

except Exception as e:
    print(f"EXECUTION_ERROR: {{e}}")
    sys.exit(1)
"""

            result = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if "EXECUTION_TEST_SUCCESS" in result.stdout:
                return True, "执行测试通过"
            else:
                return False, f"执行测试失败: {result.stdout + result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "执行测试超时"
        except Exception as e:
            return False, f"测试失败: {e}"

    def run_full_test(self, file_path: str, class_name: str) -> Tuple[bool, str]:
        """运行完整测试"""

        # 1. 语法测试
        success, message = self.test_syntax(file_path)
        if not success:
            return False, f"[语法测试] {message}"

        # 2. 导入测试
        success, message = self.test_import(file_path)
        if not success:
            return False, f"[导入测试] {message}"

        # 3. 执行测试
        success, message = self.test_basic_execution(file_path, class_name)
        if not success:
            return False, f"[执行测试] {message}"

        return True, "所有测试通过"
