"""
Git操作器 - 自动进行版本控制
"""
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime


class GitOperator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def _run_command(self, command: list) -> Tuple[bool, str]:
        """执行git命令"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except Exception as e:
            return False, str(e)

    def add_file(self, file_path: str) -> Tuple[bool, str]:
        """添加文件到暂存区"""
        return self._run_command(['git', 'add', file_path])

    def commit(self, message: str) -> Tuple[bool, str]:
        """提交更改"""
        return self._run_command(['git', 'commit', '-m', message])

    def commit_new_capability(self, capability_name: str,
                              file_paths: list) -> Tuple[bool, str]:
        """提交新能力"""

        # 添加所有相关文件
        for file_path in file_paths:
            success, message = self.add_file(file_path)
            if not success:
                return False, f"添加文件失败: {message}"

        # 提交
        commit_message = f"[自动生成] 新增能力: {capability_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return self.commit(commit_message)

    def create_tag(self, tag_name: str, message: str = "") -> Tuple[bool, str]:
        """创建标签"""
        if message:
            return self._run_command(['git', 'tag', '-a', tag_name, '-m', message])
        else:
            return self._run_command(['git', 'tag', tag_name])
