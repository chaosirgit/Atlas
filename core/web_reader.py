import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests.exceptions import Timeout, RequestException

def _get_proxies():
    """从环境变量加载代理设置"""
    http_proxy = os.getenv("PROXY_HTTP")
    https_proxy = os.getenv("PROXY_HTTPS")
    
    if not http_proxy or "your_proxy_address" in http_proxy:
        return None
        
    return {"http": http_proxy, "https": https_proxy}

def _is_foreign_site(url: str) -> bool:
    """检查是否为国外网站 (简单通过TLD判断)"""
    try:
        domain = urlparse(url).netloc
        if domain.endswith(".cn"):
            return False
        return True
    except Exception:
        return True # 解析失败时默认为是

def _make_request(url: str) -> requests.Response:
    """
    发起网络请求,包含代理和重试逻辑
    1. 判断是否国外网站,是则直接使用代理.
    2. 首次请求超时后,自动使用代理重试一次.
    3. 如果第二次还失败,则抛出异常.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    proxies = _get_proxies()
    use_proxy = proxies and _is_foreign_site(url)

    try:
        # 第一次尝试
        if use_proxy:
            print(f"[Web] 使用代理访问(国外站点): {url}")
            response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        else:
            print(f"[Web] 直接访问: {url}")
            response = requests.get(url, headers=headers, timeout=15)
        
        response.raise_for_status()
        return response

    except Timeout:
        # 如果第一次超时且未使用代理,则尝试使用代理重试
        if not use_proxy and proxies:
            print(f"[Web] 访问超时, 尝试使用代理重试: {url}")
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
                response.raise_for_status()
                return response
            except (Timeout, RequestException) as e:
                raise RequestException(f"代理重试失败: {e}")
        else:
            raise RequestException("访问超时") # 如果是国外网站或没有代理, 则直接失败
            
    except RequestException as e:
        raise e


def read_web_content(url: str) -> dict:
    """
    读取网页的主要文本内容.
    """
    try:
        response = _make_request(url)
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return {"success": True, "content": text, "message": f"网页内容读取成功: {url}"}

    except RequestException as e:
        return {"success": False, "message": f"网络请求失败: {e}"}
    except Exception as e:
        return {"success": False, "message": f"处理网页时出错: {e}"}

def list_web_resources(url: str) -> dict:
    """
    列出网页引用的所有资源 (CSS, JS, 图片等).
    """
    try:
        response = _make_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        resources = {'css': [], 'js': [], 'images': [], 'links': []}

        for link in soup.find_all('link', rel='stylesheet'):
            if href := link.get('href'):
                resources['css'].append(urljoin(url, href))

        for script in soup.find_all('script', src=True):
            if src := script.get('src'):
                resources['js'].append(urljoin(url, src))

        for img in soup.find_all('img', src=True):
            if src := img.get('src'):
                if not src.startswith('data:image'):
                    resources['images'].append(urljoin(url, src))
        
        for a in soup.find_all('a', href=True):
            if href := a.get('href'):
                if not href.startswith('#'):
                     resources['links'].append(urljoin(url, href))

        return {"success": True, "resources": resources, "message": f"网页资源列表成功: {url}"}

    except RequestException as e:
        return {"success": False, "message": f"网络请求失败: {e}"}
    except Exception as e:
        return {"success": False, "message": f"处理网页时出错: {e}"}
