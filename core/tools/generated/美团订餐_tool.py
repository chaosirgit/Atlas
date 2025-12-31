import os
import logging
import requests

class 美团订餐Tool:
    """
    一个用于与美团API交互的工具类，支持查看外卖列表和下单功能。
    
    使用前请确保已设置环境变量 MEITUAN_API_KEY 和 MEITUAN_SECRET 以供认证使用。
    """

    def __init__(self):
        self.api_key = os.getenv('MEITUAN_API_KEY')
        self.secret = os.getenv('MEITUAN_SECRET')
        self.base_url = "https://api.meituan.com/v1/"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def execute(self, action, **kwargs):
        """
        根据指定的动作执行相应的操作。
        
        参数:
            action (str): 指定要执行的操作，如 'view_menu' 或 'place_order'.
            kwargs: 其他参数，根据action的不同而变化。
            
        返回:
            dict: API响应数据或错误信息。
        """
        if action == 'view_menu':
            return self.view_menu()
        elif action == 'place_order':
            order_details = kwargs.get('order_details', {})
            return self.place_order(order_details)
        else:
            self.logger.error(f"Unsupported action: {action}")
            return {"error": f"Unsupported action: {action}"}

    def view_menu(self):
        """获取并返回当前可用的外卖菜单。"""
        url = f"{self.base_url}menu"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch menu: {e}")
            return {"error": str(e)}

    def place_order(self, order_details):
        """
        下单购买指定商品。
        
        参数:
            order_details (dict): 包含订单详情的字典。
        """
        url = f"{self.base_url}orders"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, json=order_details, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to place order: {e}")
            return {"error": str(e)}