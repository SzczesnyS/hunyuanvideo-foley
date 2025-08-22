#!/usr/bin/env python3
"""
生成腾讯云COS签名URL的脚本
需要先配置coscmd工具的访问密钥
"""

import os
import json
import subprocess
import logging
from typing import Dict, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
URL_MAPPING_FILE = "video_url_mapping.json"
SIGNED_URL_MAPPING_FILE = "signed_video_url_mapping.json"
SIGN_URL_TIMEOUT = 157680000  # URL有效期（秒）约5年

def get_cos_signed_url(cos_path: str) -> Optional[str]:
    """
    使用coscmd获取文件的签名URL
    
    Args:
        cos_path: COS对象路径，如 "hunyuanvideo-foley_demo/demo_show/1-1.mp4"
    
    Returns:
        str: 签名URL，如果失败返回None
    """
    try:
        # 使用coscmd生成签名URL
        result = subprocess.run(
            ['coscmd', 'signurl', '-t', str(SIGN_URL_TIMEOUT), cos_path], 
            capture_output=True, 
            check=True, 
            timeout=60
        )
        url = result.stdout.decode('utf-8').strip().split('\n')[0]
        
        # 处理可能的格式问题
        if url.startswith("b'") and url.endswith("'"):
            url = url[2:-1]
            
        logger.info(f"✅ 生成签名URL成功: {os.path.basename(cos_path)}")
        return url
        
    except subprocess.TimeoutExpired:
        logger.error(f"❌ 获取URL超时: {cos_path}")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 获取URL失败: {cos_path}")
        logger.error(f"错误信息: {e.stderr.decode('utf-8')}")
        return None
    except FileNotFoundError:
        logger.error("❌ 'coscmd' 命令未找到。请先安装并配置coscmd。")
        logger.error("配置步骤：")
        logger.error("1. pip install coscmd")
        logger.error("2. coscmd config -a <SecretId> -s <SecretKey> -b <BucketName> -r <Region>")
        return None

def extract_cos_paths_from_mapping() -> Dict[str, str]:
    """
    从现有的URL映射文件中提取COS路径
    
    Returns:
        Dict[str, str]: {文件名: COS路径}
    """
    if not os.path.exists(URL_MAPPING_FILE):
        logger.error(f"URL映射文件不存在: {URL_MAPPING_FILE}")
        return {}
    
    cos_paths = {}
    
    with open(URL_MAPPING_FILE, 'r', encoding='utf-8') as f:
        url_mapping = json.load(f)
    
    for filename, public_url in url_mapping.items():
        # 从公共URL中提取COS路径
        # URL格式: https://bucket.cos.region.myqcloud.com/path
        if '/hunyuanvideo-foley_demo/' in public_url:
            cos_path = public_url.split('/hunyuanvideo-foley_demo/', 1)[1]
            cos_path = 'hunyuanvideo-foley_demo/' + cos_path
            cos_paths[filename] = cos_path
            logger.debug(f"提取路径: {filename} -> {cos_path}")
    
    logger.info(f"从映射文件提取出 {len(cos_paths)} 个COS路径")
    return cos_paths

def generate_signed_urls(cos_paths: Dict[str, str]) -> Dict[str, str]:
    """
    为所有COS路径生成签名URL
    
    Args:
        cos_paths: {文件名: COS路径}
        
    Returns:
        Dict[str, str]: {文件名: 签名URL}
    """
    signed_urls = {}
    
    logger.info("开始生成签名URL...")
    
    for filename, cos_path in cos_paths.items():
        logger.info(f"正在处理: {filename}")
        
        signed_url = get_cos_signed_url(cos_path)
        if signed_url:
            signed_urls[filename] = signed_url
        else:
            logger.warning(f"⚠️ 跳过文件: {filename}")
    
    logger.info(f"成功生成 {len(signed_urls)} 个签名URL")
    return signed_urls

def update_jsonl_files_with_signed_urls(signed_urls: Dict[str, str]):
    """
    使用签名URL更新JSONL文件
    """
    from replace_video_urls import JSONL_FILES, update_jsonl_file, create_backup
    
    logger.info("使用签名URL更新JSONL文件...")
    
    for jsonl_file in JSONL_FILES:
        if os.path.exists(jsonl_file):
            logger.info(f"正在更新: {jsonl_file}")
            create_backup(jsonl_file + ".signed")
            updates = update_jsonl_file(jsonl_file, signed_urls)
            logger.info(f"✅ {jsonl_file} 更新完成，共更新 {updates} 条记录")

def main():
    """主函数"""
    logger.info("🚀 开始生成腾讯云COS签名URL")
    
    # 检查coscmd是否可用
    try:
        result = subprocess.run(['coscmd', '--version'], capture_output=True, check=True)
        logger.info("✅ coscmd工具已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("❌ coscmd工具未安装或未配置")
        logger.error("请按以下步骤配置：")
        logger.error("1. 安装: pip install coscmd")
        logger.error("2. 配置: coscmd config -a <SecretId> -s <SecretKey> -b texttoaudio-train-1258344703 -r ap-shanghai")
        logger.error("3. 测试: coscmd list")
        return
    
    # 1. 从现有映射文件提取COS路径
    cos_paths = extract_cos_paths_from_mapping()
    if not cos_paths:
        logger.error("未找到COS路径，请先运行replace_video_urls.py")
        return
    
    # 2. 生成签名URL
    signed_urls = generate_signed_urls(cos_paths)
    if not signed_urls:
        logger.error("未生成任何签名URL")
        return
    
    # 3. 保存签名URL映射
    with open(SIGNED_URL_MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(signed_urls, f, ensure_ascii=False, indent=2)
    logger.info(f"📁 签名URL映射已保存到: {SIGNED_URL_MAPPING_FILE}")
    
    # 4. 更新JSONL文件
    update_jsonl_files_with_signed_urls(signed_urls)
    
    logger.info("🎉 签名URL生成完成！")
    logger.info(f"📊 处理文件数量: {len(signed_urls)}")
    logger.info(f"⏰ URL有效期: {SIGN_URL_TIMEOUT // (365*24*3600):.1f} 年")
    
    # 5. 显示一些示例URL
    logger.info("📋 示例签名URL:")
    for i, (filename, url) in enumerate(list(signed_urls.items())[:3]):
        logger.info(f"  {filename}: {url[:80]}...")
        if i >= 2:
            break

if __name__ == "__main__":
    main()
