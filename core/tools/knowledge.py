import json
from pathlib import Path
from typing import Dict, Any

# 知识库文件路径
KB_FILE = Path("atlas_workspace") / "memory" / "knowledge_base.json"

def _load_kb() -> Dict[str, Any]:
    """加载知识库文件"""
    if KB_FILE.exists():
        try:
            with open(KB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # 如果文件损坏或为空,返回一个空字典
            return {}
    return {}

def _save_kb(data: Dict[str, Any]):
    """保存知识库文件"""
    KB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(KB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def remember(key: str, value: str) -> Dict[str, Any]:
    """
    记住一个事实 (键值对).
    """
    if not isinstance(key, str) or not isinstance(value, str):
        return {"success": False, "message": "key 和 value 都必须是字符串"}
    if not key or not value:
        return {"success": False, "message": "key 和 value 都不能为空"}
        
    try:
        kb = _load_kb()
        kb[key] = value
        _save_kb(kb)
        return {"success": True, "message": f"好的, 我记住了 '{key}' 是 '{value}'."}
    except Exception as e:
        return {"success": False, "message": f"记忆时出错: {str(e)}"}

def recall(key: str) -> Dict[str, Any]:
    """
    回忆一个事实 (通过key).
    """
    if not isinstance(key, str) or not key:
        return {"success": False, "message": "key 必须是一个非空字符串"}

    kb = _load_kb()
    value = kb.get(key)
    
    if value is not None:
        return {"success": True, "value": value, "message": f"我记得 '{key}' 是 '{value}'."}
    else:
        return {"success": False, "value": None, "message": f"我的知识库里没有关于 '{key}' 的记忆."}

def forget(key: str) -> Dict[str, Any]:
    """
    忘记一个事实 (通过key).
    """
    if not isinstance(key, str) or not key:
        return {"success": False, "message": "key 必须是一个非空字符串"}
        
    kb = _load_kb()
    if key in kb:
        del kb[key]
        _save_kb(kb)
        return {"success": True, "message": f"好的, 我已经忘记了关于 '{key}' 的记忆."}
    else:
        return {"success": False, "message": f"我的知识库里本来就没有 '{key}'."}

def list_facts() -> Dict[str, Any]:
    """
    列出所有记住的事实.
    """
    kb = _load_kb()
    if kb:
        return {"success": True, "facts": kb, "message": f"我目前记住了 {len(kb)} 个事实."}
    else:
        return {"success": True, "facts": {}, "message": "我的知识库目前是空的."}

if __name__ == '__main__':
    # for testing
    print("--- 记忆测试 ---")
    print(remember("user_name", "Ethan"))
    print(remember("favorite_color", "蓝色"))
    print("\n--- 回忆测试 ---")
    print(recall("user_name"))
    print(recall("favorite_food"))
    print("\n--- 列表测试 ---")
    print(list_facts())
    print("\n--- 忘记测试 ---")
    print(forget("favorite_color"))
    print(list_facts())
    print(forget("non_existent_key"))
