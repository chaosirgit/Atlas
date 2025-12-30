import os
from tavily import TavilyClient
from typing import Dict, Any

def search(query: str) -> Dict[str, Any]:
    """
    使用 Tavily API 执行网络搜索.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or "your_tavily_api_key" in api_key:
        return {"success": False, "message": "Tavily API Key未配置或无效"}

    try:
        # 初始化 Tavily 客户端
        tavily = TavilyClient(api_key=api_key)
        
        # 执行搜索
        # include_answer=True 会让Tavily返回一个基于搜索结果的总结性答案
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        
        # 提取总结性答案和搜索结果
        answer = response.get("answer", "没有找到总结性答案.")
        results = response.get("results", [])
        
        # 格式化简单的结果以供LLM使用
        formatted_results = []
        for res in results:
            formatted_results.append({
                "title": res.get("title"),
                "url": res.get("url"),
                "snippet": res.get("content")[:200] + "..." # 截取前200个字符作为摘要
            })

        return {
            "success": True,
            "answer": answer,
            "results": formatted_results,
            "message": f"搜索 '{query}' 成功, 总结: {answer}"
        }

    except Exception as e:
        return {"success": False, "message": f"Tavily 搜索时出错: {str(e)}"}

if __name__ == '__main__':
    # for testing
    # 需要在环境变量中设置 TAVILY_API_KEY
    search_result = search("今天AI领域有什么大新闻?")
    import json
    print(json.dumps(search_result, indent=2, ensure_ascii=False))
