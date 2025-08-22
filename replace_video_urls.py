#!/usr/bin/env python3
"""
腾讯云COS视频URL替换脚本
解析upload_result.log，生成签名URL，并替换网页中的视频调用

基于get_cos_csv.py中的get_cos_signed_url方法
"""

import os
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
UPLOAD_LOG_FILE = "upload_result.log"
COS_BASE_PATH = ""  # 从日志中直接解析完整路径
SIGN_URL_TIMEOUT = 157680000  # URL有效期（秒）约5年

# 需要更新的JSONL文件
JSONL_FILES = [
    "src/assets/demo_videos.jsonl",
    "src/assets/moviegen_benchmark.jsonl", 
    "src/assets/model_comparison_videos.jsonl"
]

def build_cos_public_url(cos_path: str, bucket_name: str = "texttoaudio-train-1258344703") -> str:
    """
    构建腾讯云COS的公共访问URL
    
    Args:
        cos_path: COS对象路径，如 "hunyuanvideo-foley_demo/demo_show/1-1.mp4"
        bucket_name: COS存储桶名称
    
    Returns:
        str: 公共访问URL
    """
    # 腾讯云COS公共访问URL格式
    # https://{bucket}.cos.{region}.myqcloud.com/{object_key}
    
    # 从存储桶名称推断地域（如果包含地域信息）
    # 通常格式为 bucket-appid，需要根据实际情况调整
    region = "ap-shanghai"  # 默认地域，可以根据实际情况修改
    
    public_url = f"https://{bucket_name}.cos.{region}.myqcloud.com/{cos_path}"
    logger.info(f"构建公共URL: {os.path.basename(cos_path)} -> {public_url}")
    return public_url

def get_cos_signed_url(remote_file_path: str) -> Optional[str]:
    """
    获取COS文件URL
    优先尝试使用coscmd生成签名URL，如果失败则使用公共URL
    """
    try:
        # 尝试使用coscmd生成签名URL
        result = subprocess.run(
            ['coscmd', 'signurl', '-t', str(SIGN_URL_TIMEOUT), remote_file_path], 
            capture_output=True, 
            check=True, 
            timeout=60
        )
        url = result.stdout.decode('utf-8').strip().split('\n')[0]
        
        # 增加健壮性处理，以防coscmd输出 "b'url'" 这种格式
        if url.startswith("b'") and url.endswith("'"):
            url = url[2:-1]
            
        logger.info(f"获取签名URL成功: {os.path.basename(remote_file_path)}")
        return url
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        # 如果coscmd失败，使用公共URL
        logger.info(f"coscmd不可用，使用公共URL: {os.path.basename(remote_file_path)}")
        return build_cos_public_url(remote_file_path)

def parse_upload_log(log_file: str) -> Dict[str, str]:
    """
    解析upload_result.log文件，提取本地文件路径到COS路径的映射
    
    Returns:
        Dict[str, str]: {本地文件名: COS远程路径}
    """
    file_mapping = {}
    
    if not os.path.exists(log_file):
        logger.error(f"日志文件不存在: {log_file}")
        return file_mapping
    
    # 正则表达式匹配上传日志格式
    # 例: Upload /path/to/local/file.mp4   =>   cos://bucket/remote/path/file.mp4
    pattern = r'Upload\s+(.+?)\s+=>\s+cos://[^/]+/(.+)'
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                local_path = match.group(1)
                cos_path = match.group(2)
                
                # 提取文件名
                local_filename = os.path.basename(local_path)
                
                file_mapping[local_filename] = cos_path
                logger.debug(f"映射: {local_filename} -> {cos_path}")
    
    logger.info(f"从日志文件解析出 {len(file_mapping)} 个文件映射")
    return file_mapping

def generate_video_url_mapping(file_mapping: Dict[str, str]) -> Dict[str, str]:
    """
    为每个视频文件生成签名URL
    
    Args:
        file_mapping: {文件名: COS路径}
        
    Returns:
        Dict[str, str]: {文件名: 签名URL}
    """
    url_mapping = {}
    
    for filename, cos_path in file_mapping.items():
        if filename.endswith('.mp4'):
            logger.info(f"正在生成签名URL: {filename}")
            signed_url = get_cos_signed_url(cos_path)
            
            if signed_url:
                url_mapping[filename] = signed_url
                logger.info(f"✅ {filename} -> URL已生成")
            else:
                logger.warning(f"❌ {filename} -> URL生成失败")
    
    logger.info(f"成功生成 {len(url_mapping)} 个签名URL")
    return url_mapping

def update_jsonl_file(jsonl_file: str, url_mapping: Dict[str, str]) -> int:
    """
    更新JSONL文件中的视频路径为COS签名URL
    
    Args:
        jsonl_file: JSONL文件路径
        url_mapping: {文件名: 签名URL}
        
    Returns:
        int: 更新的条目数量
    """
    if not os.path.exists(jsonl_file):
        logger.warning(f"文件不存在，跳过: {jsonl_file}")
        return 0
    
    updated_lines = []
    updates_count = 0
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                line_updated = False
                
                # 检查是否有videos字段
                if 'videos' in data:
                    for method, video_path in data['videos'].items():
                        # 提取文件名
                        filename = os.path.basename(video_path)
                        
                        # 如果有对应的签名URL，则替换
                        if filename in url_mapping:
                            old_path = data['videos'][method]
                            data['videos'][method] = url_mapping[filename]
                            logger.info(f"第{line_num}行 {method}: {old_path} -> {filename}")
                            line_updated = True
                
                if line_updated:
                    updates_count += 1
                
                updated_lines.append(json.dumps(data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                logger.error(f"第{line_num}行JSON解析错误: {e}")
                updated_lines.append(line)  # 保留原行
    
    # 写回文件
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for line in updated_lines:
            f.write(line + '\n')
    
    logger.info(f"文件 {jsonl_file} 更新完成，共更新 {updates_count} 条记录")
    return updates_count

def create_backup(file_path: str) -> str:
    """创建文件备份"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path):
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"已创建备份: {backup_path}")
    return backup_path

def main():
    """主函数"""
    logger.info("开始执行视频URL替换脚本")
    
    # 1. 解析上传日志
    logger.info("步骤1: 解析上传日志")
    file_mapping = parse_upload_log(UPLOAD_LOG_FILE)
    
    if not file_mapping:
        logger.error("未找到任何文件映射，退出")
        return
    
    # 2. 生成签名URL
    logger.info("步骤2: 生成签名URL")
    url_mapping = generate_video_url_mapping(file_mapping)
    
    if not url_mapping:
        logger.error("未生成任何签名URL，退出")
        return
    
    # 3. 更新JSONL文件
    logger.info("步骤3: 更新JSONL文件")
    total_updates = 0
    
    for jsonl_file in JSONL_FILES:
        logger.info(f"正在处理: {jsonl_file}")
        
        # 创建备份
        create_backup(jsonl_file)
        
        # 更新文件
        updates = update_jsonl_file(jsonl_file, url_mapping)
        total_updates += updates
    
    # 4. 生成URL映射文件（可选，用于调试）
    mapping_file = "video_url_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(url_mapping, f, ensure_ascii=False, indent=2)
    logger.info(f"URL映射已保存到: {mapping_file}")
    
    logger.info(f"✅ 脚本执行完成！共更新了 {total_updates} 条记录")
    logger.info(f"📋 处理的视频文件数量: {len(url_mapping)}")
    logger.info(f"🔗 签名URL有效期: {SIGN_URL_TIMEOUT // (365*24*3600):.1f} 年")

if __name__ == "__main__":
    main()
