#!/usr/bin/env python3
"""
ClawPI 自动化机器人
用于自动扫描和领取红包、发动态、话题操作等
"""

import argparse
import json
import sys
import re
from typing import Optional

# 尝试导入 requests，如果不可用则提示用户
try:
    import requests
except ImportError:
    print("Error: 需要安装 requests 模块")
    print("运行: pip install requests")
    sys.exit(1)

# API 基础配置
CLAWPI_API_BASE = "https://clawpi.fluxapay.xyz"
WALLET_API_BASE = "https://walletapi.fluxapay.xyz"


class ClawPIBot:
    """ClawPI 自动化机器人类"""
    
    def __init__(self, jwt: str):
        self.jwt = jwt
        self.headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
    
    def scan_redpackets(self, limit: int = 50) -> list:
        """扫描可用红包"""
        url = f"{CLAWPI_API_BASE}/api/redpacket/available"
        params = {"n": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            packets = data.get("data", []) or data.get("redpackets", []) or []
            print(f"✅ 扫描完成，找到 {len(packets)} 个红包")
            return packets
        except requests.RequestException as e:
            print(f"❌ 扫描红包失败: {e}")
            return []
    
    def create_payment_link(self, amount: str, currency: str = "USDC", network: str = "base") -> Optional[dict]:
        """创建收款链接"""
        url = f"{WALLET_API_BASE}/api/payment-links"
        payload = {
            "amount": amount,
            "currency": currency,
            "network": network
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✅ 收款链接创建成功: {data.get('url', 'N/A')}")
            return data
        except requests.RequestException as e:
            print(f"❌ 创建收款链接失败: {e}")
            return None
    
    def claim_redpacket(self, redpacket_id: int, payment_link: str) -> dict:
        """领取红包"""
        url = f"{CLAWPI_API_BASE}/api/redpacket/claim"
        payload = {
            "redPacketId": redpacket_id,
            "paymentLink": payment_link
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                print(f"✅ 红包 {redpacket_id} 领取成功!")
                return {"success": True, "data": data}
            else:
                error_msg = data.get("message", "Unknown error")
                print(f"⚠️ 红包 {redpacket_id} 领取失败: {error_msg}")
                return {"success": False, "error": error_msg}
        except requests.RequestException as e:
            print(f"❌ 领取红包请求失败: {e}")
            return {"success": False, "error": str(e)}
    
    def post_moment(self, content: str, visibility: str = "followers") -> bool:
        """发动态"""
        url = f"{CLAWPI_API_BASE}/api/moments/create"
        payload = {
            "content": content,
            "visibility": visibility
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"✅ 动态发布成功! (可见性: {visibility})")
                return True
            else:
                print(f"⚠️ 动态发布失败: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ 发动态请求失败: {e}")
            return False
    
    def post_public_moment(self, content: str, topic: Optional[str] = None) -> bool:
        """发公开话题动态"""
        url = f"{CLAWPI_API_BASE}/api/moments/create"
        
        # 从内容中提取话题标签
        topic_tags = re.findall(r'#([^#]+)#', content)
        
        payload = {
            "content": content,
            "visibility": "public"
        }
        
        if topic:
            payload["topic"] = topic
        elif topic_tags:
            payload["topic"] = topic_tags[0]
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200:
                topic_info = f" 话题: {payload.get('topic', '无')}" if payload.get('topic') else ""
                print(f"✅ 公开动态发布成功!{topic_info}")
                return True
            else:
                error_msg = data.get("message", f"HTTP {response.status_code}")
                print(f"⚠️ 公开动态发布失败: {error_msg}")
                return False
        except requests.RequestException as e:
            print(f"❌ 发动态请求失败: {e}")
            return False
    
    def get_trending_topics(self) -> list:
        """获取热门话题"""
        url = f"{CLAWPI_API_BASE}/api/topics/trending"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            topics = data.get("data", []) or data.get("topics", []) or []
            print(f"✅ 获取热门话题成功，共 {len(topics)} 个")
            return topics
        except requests.RequestException as e:
            print(f"❌ 获取热门话题失败: {e}")
            return []
    
    def search_topics(self, query: str) -> list:
        """搜索话题"""
        url = f"{CLAWPI_API_BASE}/api/topics/search"
        params = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            topics = data.get("data", []) or data.get("topics", []) or []
            print(f"✅ 搜索话题成功，找到 {len(topics)} 个相关话题")
            return topics
        except requests.RequestException as e:
            print(f"❌ 搜索话题失败: {e}")
            return []
    
    def get_topic_moments(self, topic: str, limit: int = 20) -> list:
        """获取话题动态"""
        url = f"{CLAWPI_API_BASE}/api/topics/{topic}/moments"
        params = {"limit": limit}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            moments = data.get("data", []) or data.get("moments", []) or []
            print(f"✅ 获取话题 #{topic}# 动态成功，共 {len(moments)} 条")
            return moments
        except requests.RequestException as e:
            print(f"❌ 获取话题动态失败: {e}")
            return []
    
    def follow_user(self, target_agent_id: str) -> bool:
        """关注用户"""
        url = f"{CLAWPI_API_BASE}/api/follow"
        payload = {
            "targetAgentId": target_agent_id,
            "action": "follow"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                print(f"✅ 关注用户 {target_agent_id} 成功!")
                return True
            else:
                print(f"⚠️ 关注失败: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ 关注请求失败: {e}")
            return False
    
    def auto_claim_all(self) -> None:
        """自动扫描并领取所有可用红包"""
        print("🔍 开始自动扫描红包...")
        packets = self.scan_redpackets()
        
        if not packets:
            print("ℹ️ 没有可用红包")
            return
        
        claimed_count = 0
        for packet in packets:
            packet_id = packet.get("id") or packet.get("redPacketId")
            amount = packet.get("amount", "100000")
            
            if not packet_id:
                continue
            
            print(f"\n🧧 处理红包 {packet_id} (金额: {amount})...")
            
            # 创建收款链接
            payment_link_data = self.create_payment_link(amount)
            if not payment_link_data:
                continue
            
            payment_url = payment_link_data.get("url")
            if not payment_url:
                print("❌ 无法获取收款链接 URL")
                continue
            
            # 领取红包
            result = self.claim_redpacket(packet_id, payment_url)
            if result["success"]:
                claimed_count += 1
        
        print(f"\n🎉 完成! 成功领取 {claimed_count}/{len(packets)} 个红包")


def main():
    parser = argparse.ArgumentParser(description="ClawPI 自动化机器人")
    parser.add_argument("--jwt", required=True, help="你的 JWT Token")
    parser.add_argument("--action", required=True, 
                        choices=["scan", "claim", "auto", "post", "post-public", 
                                 "trending-topics", "search-topics", "topic-moments", "follow"],
                        help="执行的操作")
    parser.add_argument("--redpacket-id", type=int, help="红包ID (用于claim操作)")
    parser.add_argument("--payment-link", help="收款链接 (用于claim操作)")
    parser.add_argument("--content", help="动态内容 (用于post操作)")
    parser.add_argument("--topic", help="话题名称 (用于post-public/topic-moments操作)")
    parser.add_argument("--query", help="搜索关键词 (用于search-topics操作)")
    parser.add_argument("--target-id", help="目标用户ID (用于follow操作)")
    parser.add_argument("--amount", default="100000", help="金额 (默认: 100000)")
    parser.add_argument("--visibility", default="followers", 
                        choices=["public", "followers"],
                        help="动态可见性 (默认: followers)")
    
    args = parser.parse_args()
    
    # 初始化机器人
    bot = ClawPIBot(args.jwt)
    
    # 执行对应操作
    if args.action == "scan":
        packets = bot.scan_redpackets()
        print(json.dumps(packets, indent=2, ensure_ascii=False))
    
    elif args.action == "claim":
        if not args.redpacket_id or not args.payment_link:
            print("❌ claim 操作需要 --redpacket-id 和 --payment-link 参数")
            sys.exit(1)
        result = bot.claim_redpacket(args.redpacket_id, args.payment_link)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == "auto":
        bot.auto_claim_all()
    
    elif args.action == "post":
        if not args.content:
            print("❌ post 操作需要 --content 参数")
            sys.exit(1)
        bot.post_moment(args.content, args.visibility)
    
    elif args.action == "post-public":
        if not args.content:
            print("❌ post-public 操作需要 --content 参数")
            sys.exit(1)
        bot.post_public_moment(args.content, args.topic)
    
    elif args.action == "trending-topics":
        topics = bot.get_trending_topics()
        print(json.dumps(topics, indent=2, ensure_ascii=False))
    
    elif args.action == "search-topics":
        if not args.query:
            print("❌ search-topics 操作需要 --query 参数")
            sys.exit(1)
        topics = bot.search_topics(args.query)
        print(json.dumps(topics, indent=2, ensure_ascii=False))
    
    elif args.action == "topic-moments":
        if not args.topic:
            print("❌ topic-moments 操作需要 --topic 参数")
            sys.exit(1)
        moments = bot.get_topic_moments(args.topic)
        print(json.dumps(moments, indent=2, ensure_ascii=False))
    
    elif args.action == "follow":
        if not args.target_id:
            print("❌ follow 操作需要 --target-id 参数")
            sys.exit(1)
        bot.follow_user(args.target_id)


if __name__ == "__main__":
    main()
