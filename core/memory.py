import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import dashscope
from dashscope import TextEmbedding

# 先检查numpy是否安装
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️ numpy未安装，长期记忆功能将被禁用")


class Memory:
    """改进的记忆系统 - 短期记忆 + 长期记忆"""

    def __init__(self, workspace: str = "atlas_workspace"):
        self.workspace = Path(workspace)
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # 短期记忆文件
        self.short_term_file = self.memory_dir / "short_term_memory.json"

        # 短期记忆（最近20条对话）
        self.short_term_memory: List[Dict[str, Any]] = self._load_short_term()  # 改这里
        self.max_short_term = 20

        # 长期记忆文件
        self.long_term_file = self.memory_dir / "long_term_memory.json"
        self.embeddings_file = self.memory_dir / "embeddings.npy"

        # 加载记忆
        self.long_term_memory: List[Dict[str, Any]] = self._load_long_term()
        self.embeddings: Optional[np.ndarray] = self._load_embeddings() if HAS_NUMPY else None

        print(f"✅ 记忆系统初始化完成")
        print(f"   短期记忆: {len(self.short_term_memory)}条")
        print(f"   长期记忆: {len(self.long_term_memory)}条")

    def _load_short_term(self) -> List[Dict[str, Any]]:
        """加载短期记忆"""
        try:
            if self.short_term_file.exists():
                with open(self.short_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # print(f"📂 加载了 {len(data)} 条短期记忆")
                    return data
        except Exception as e:
            print(f"⚠️ 加载短期记忆失败: {e}")
        return []

    def _save_short_term(self):
        """保存短期记忆"""
        try:
            with open(self.short_term_file, 'w', encoding='utf-8') as f:
                json.dump(self.short_term_memory, f, ensure_ascii=False, indent=2)
            # print(f"💾 保存了 {len(self.short_term_memory)} 条短期记忆")
        except Exception as e:
            print(f"⚠️ 保存短期记忆失败: {e}")

    def _load_long_term(self) -> List[Dict[str, Any]]:
        """加载长期记忆"""
        try:
            if self.long_term_file.exists():
                with open(self.long_term_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # print(f"📂 加载了 {len(data)} 条长期记忆")
                    return data
        except Exception as e:
            print(f"⚠️ 加载长期记忆失败: {e}")
        return []

    def _save_long_term(self):
        """保存长期记忆"""
        try:
            with open(self.long_term_file, 'w', encoding='utf-8') as f:
                json.dump(self.long_term_memory, f, ensure_ascii=False, indent=2)
            # print(f"💾 保存了 {len(self.long_term_memory)} 条长期记忆")
        except Exception as e:
            print(f"⚠️ 保存长期记忆失败: {e}")

    def _load_embeddings(self) -> Optional[np.ndarray]:
        """加载向量"""
        if not HAS_NUMPY:
            return None

        try:
            if self.embeddings_file.exists():
                data = np.load(self.embeddings_file)
                # print(f"📊 加载了 {len(data)} 个向量")
                return data
        except Exception as e:
            print(f"⚠️ 加载向量失败: {e}")
        return None

    def _save_embeddings(self):
        """保存向量"""
        if not HAS_NUMPY or self.embeddings is None:
            return

        try:
            np.save(self.embeddings_file, self.embeddings)
            # print(f"💾 保存了 {len(self.embeddings)} 个向量")
        except Exception as e:
            print(f"⚠️ 保存向量失败: {e}")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本向量"""
        if not HAS_NUMPY:
            return None

        try:
            response = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v1,
                input=text
            )
            return response.output['embeddings'][0]['embedding']
        except Exception as e:
            print(f"⚠️ 向量化失败: {e}")
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def add_message(self, role: str, content: str):
        """添加消息到短期记忆"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }

        self.short_term_memory.append(message)

        # 立即保存短期记忆
        self._save_short_term()

        # 如果短期记忆满了，转移到长期记忆
        if len(self.short_term_memory) > self.max_short_term:
            self._move_to_long_term()

    def _move_to_long_term(self):
        """将旧的短期记忆转移到长期记忆"""
        if not HAS_NUMPY:
            # 如果没有numpy，只保留最近的对话
            self.short_term_memory = self.short_term_memory[-self.max_short_term:]
            return

        # 取出最老的对话对（user + assistant）
        if len(self.short_term_memory) >= 2:
            old_messages = self.short_term_memory[:2]
            self.short_term_memory = self.short_term_memory[2:]

            # 合并成一条记录
            conversation = {
                'user': old_messages[0]['content'],
                'assistant': old_messages[1]['content'] if len(old_messages) > 1 else '',
                'timestamp': old_messages[0]['timestamp']
            }

            # 生成向量
            text = f"用户: {conversation['user']}\nAtlas: {conversation['assistant']}"
            embedding = self._get_embedding(text)

            if embedding:
                self.long_term_memory.append(conversation)

                # 添加向量
                if self.embeddings is None:
                    self.embeddings = np.array([embedding])
                else:
                    self.embeddings = np.vstack([self.embeddings, embedding])

                # 保存
                self._save_long_term()
                self._save_embeddings()

    def search_memory(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """在长期记忆中搜索相关对话"""
        if not HAS_NUMPY or len(self.long_term_memory) == 0 or self.embeddings is None:
            return []

        # 获取查询向量
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return []

        query_vec = np.array(query_embedding)

        # 计算相似度
        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_vec, emb)
            similarities.append((i, sim))

        # 排序并返回top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, sim in similarities[:top_k]:
            if sim > 0.7:  # 相似度阈值
                results.append(self.long_term_memory[i])

        return results

    def format_for_qwen(self, include_long_term: bool = True, query: str = None) -> List[Dict[str, str]]:
        """格式化记忆供千问使用"""
        messages = []

        # 如果有查询，搜索相关的长期记忆
        if include_long_term and query and len(self.long_term_memory) > 0:
            relevant_memories = self.search_memory(query, top_k=3)
            if relevant_memories:
                context = "以下是相关的历史对话：\n"
                for mem in relevant_memories:
                    context += f"用户: {mem['user']}\nAtlas: {mem['assistant']}\n\n"
                messages.append({'role': 'system', 'content': context})

        # 添加短期记忆
        for msg in self.short_term_memory:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })

        return messages

    def get_summary(self) -> str:
        """获取记忆摘要"""
        return f"短期记忆: {len(self.short_term_memory)}条 | 长期记忆: {len(self.long_term_memory)}条"

    def clear_memory(self):
        """清空所有记忆"""
        self.short_term_memory = []
        self.long_term_memory = []
        self.embeddings = None

        try:
            if self.short_term_file.exists():
                self.short_term_file.unlink()
            if self.long_term_file.exists():
                self.long_term_file.unlink()
            if self.embeddings_file.exists():
                self.embeddings_file.unlink()
            print("🗑️ 记忆已清空")
        except Exception as e:
            print(f"⚠️ 清空记忆失败: {e}")

    def save_all(self):
        """保存所有记忆（程序退出时调用）"""
        self._save_short_term()
        if len(self.long_term_memory) > 0:
            self._save_long_term()
        if self.embeddings is not None:
            self._save_embeddings()
        print("💾 所有记忆已保存")
