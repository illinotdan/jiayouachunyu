#!/usr/bin/env python3
"""
STRATZ API 测试和诊断脚本
用于诊断API访问问题并提供解决方案
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.stratz_service import StratzService
import json

def main():
    print("🎮 STRATZ API 诊断工具")
    print("=" * 50)
    
    # 您的API密钥
    api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiYzM1OGY4N2YtYjI3Ny00MTZiLTliOTQtNjQxNDUyZmVhZTdlIiwiU3RlYW1JZCI6IjE2NDgzNDU1NyIsIkFQSVVzZXIiOiJ0cnVlIiwibmJmIjoxNzU3OTk4MjE0LCJleHAiOjE3ODk1MzQyMTQsImlhdCI6MTc1Nzk5ODIxNCwiaXNzIjoiaHR0cHM6Ly9hcGkuc3RyYXR6LmNvbSJ9.r_3s8lSC3uXd7v0LhnP2cvYRByQf56EtUONikFS_x_4'
    
    # 初始化服务
    stratz = StratzService(api_key=api_key)
    
    # 运行完整测试
    test_results = stratz.test_api_access(debug=True)
    
    print("\n📊 测试结果汇总:")
    print("=" * 30)
    
    for endpoint, success in test_results['endpoints_tested'].items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{endpoint}: {status}")
    
    if test_results['recommendations']:
        print("\n💡 建议:")
        for i, rec in enumerate(test_results['recommendations'], 1):
            print(f"{i}. {rec}")
    
    # 额外测试：尝试不同的API调用方式
    print("\n🔧 额外诊断测试:")
    print("-" * 30)
    
    # 测试1: 检查Token格式
    print("1. Token格式检查:")
    try:
        import jwt
        decoded = jwt.decode(api_key, options={"verify_signature": False})
        print(f"   Token主题: {decoded.get('Subject', 'N/A')}")
        print(f"   Steam ID: {decoded.get('SteamID', 'N/A')}")
        print(f"   是否API用户: {decoded.get('APIUser', 'N/A')}")
        print(f"   过期时间: {decoded.get('exp', 'N/A')}")
        
        # 检查是否过期
        import time
        if decoded.get('exp') and decoded['exp'] < time.time():
            print("   ⚠️  Token已过期！")
        else:
            print("   ✅ Token未过期")
            
    except Exception as e:
        print(f"   ❌ Token解析失败: {e}")
    
    # 测试2: 尝试不同的认证方式
    print("\n2. 认证方式测试:")
    
    # 方式1: Bearer Token
    print("   测试 Bearer Token...")
    stratz.session.headers['Authorization'] = f'Bearer {api_key}'
    if 'X-API-Key' in stratz.session.headers:
        del stratz.session.headers['X-API-Key']
    
    result1 = stratz._make_request("hero", debug=False)
    print(f"   Bearer Token: {'✅ 成功' if result1 else '❌ 失败'}")
    
    # 方式2: X-API-Key
    print("   测试 X-API-Key...")
    if 'Authorization' in stratz.session.headers:
        del stratz.session.headers['Authorization']
    stratz.session.headers['X-API-Key'] = api_key
    
    result2 = stratz._make_request("hero", debug=False)
    print(f"   X-API-Key: {'✅ 成功' if result2 else '❌ 失败'}")
    
    # 测试3: 尝试公开端点
    print("\n3. 公开端点测试:")
    
    # 移除所有认证头
    headers_backup = dict(stratz.session.headers)
    if 'Authorization' in stratz.session.headers:
        del stratz.session.headers['Authorization']
    if 'X-API-Key' in stratz.session.headers:
        del stratz.session.headers['X-API-Key']
    
    public_result = stratz._make_request("hero", debug=False)
    print(f"   无认证访问: {'✅ 成功' if public_result else '❌ 失败'}")
    
    # 恢复认证头
    stratz.session.headers.update(headers_backup)
    
    # 测试4: 检查具体的403错误信息
    print("\n4. 详细错误分析:")
    try:
        import requests
        test_url = f"https://api.stratz.com/api/v1/Match/8464041509"
        test_headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'DotaAnalysis/1.0'
        }
        
        response = requests.get(test_url, headers=test_headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 403:
            print(f"   错误内容: {response.text[:200]}")
            
            # 分析可能的原因
            error_text = response.text.lower()
            if 'subscription' in error_text or 'plan' in error_text:
                print("   🎯 可能原因: 需要付费订阅才能访问此端点")
            elif 'invalid' in error_text or 'expired' in error_text:
                print("   🎯 可能原因: API密钥无效或已过期")
            elif 'permission' in error_text or 'access' in error_text:
                print("   🎯 可能原因: 没有访问权限")
            else:
                print("   🎯 可能原因: 未知的403错误")
        
    except Exception as e:
        print(f"   详细测试失败: {e}")
    
    print("\n🎯 解决方案建议:")
    print("=" * 30)
    print("1. 检查STRATZ账户是否有效且未过期")
    print("2. 确认API密钥是否正确复制（注意空格和换行）")
    print("3. 检查STRATZ账户的订阅状态（某些端点需要付费）")
    print("4. 尝试使用GraphQL接口替代REST API")
    print("5. 联系STRATZ支持团队确认API权限")
    
    print("\n🔄 替代方案:")
    print("=" * 30)
    print("1. 优先使用OpenDota API（完全免费）")
    print("2. 使用STRATZ的GraphQL接口（部分免费）")
    print("3. 实现多数据源的备用机制")
    
    return test_results

if __name__ == "__main__":
    try:
        results = main()
        
        # 保存测试结果
        with open('stratz_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试结果已保存到: stratz_test_results.json")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
