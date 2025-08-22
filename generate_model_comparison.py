#!/usr/bin/env python3
import json
import csv
import os
from pathlib import Path

def read_csv_data(csv_path):
    """Read CSV data and return as list of dictionaries"""
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def extract_video_ids_and_models():
    """Extract unique video IDs and models from video filenames"""
    video_dir = Path("public/videos/demo_show")
    video_files = [f.name for f in video_dir.glob("*.mp4")]
    
    # Group videos by ID and model
    video_groups = {}
    
    for filename in video_files:
        # Skip the numbered videos (1-1.mp4, etc.) as they're in the existing JSONL
        if filename[0].isdigit() and '-' in filename:
            continue
            
        # Extract model and ID from filename
        if '_' in filename:
            # Handle special case for Ours model first
            if filename.startswith('Ours__128d_200k__'):
                model_name = 'HIFI-Foley'
                video_id = filename.replace('Ours__128d_200k__', '').replace('.mp4', '')
            else:
                parts = filename.replace('.mp4', '').split('_')
                if len(parts) >= 2:
                    # Handle V_AURA special case
                    if filename.startswith('V_AURA_'):
                        model_name = 'V_AURA'
                        video_id = parts[-1]  # Take the last part as video ID
                    else:
                        model_name = parts[0]
                        video_id = parts[-1]  # Take the last part as video ID
            
            if video_id not in video_groups:
                video_groups[video_id] = {}
            
            video_groups[video_id][model_name] = f"videos/demo_show/{filename}"
    
    return video_groups

def get_prompt_from_csv(csv_data, video_id):
    """Get prompt from CSV by matching video filename starting from row 63"""
    # Start from row 63 (index 63 in the list)
    for i in range(64, len(csv_data)):
        row = csv_data[i]
        video_path = row.get('video', '')
        
        if video_path:
            # Extract filename from path (e.g., "0.mp4" from "MovieGenAudioBenchSfx/video_with_audio/0.mp4")
            filename = video_path.split('/')[-1]
            video_name_without_ext = filename.replace('.mp4', '')
            
            video_name_without_ext = int(video_name_without_ext)
            # Match with video_id
            if video_name_without_ext == int(video_id):
                return row.get('SoundCaption', '')
    
    print(f"Warning: No matching video found for video ID {video_id}")
    return ""

def generate_model_comparison_jsonl():
    """Generate the new JSONL file for model comparison"""
    # Read CSV data
    csv_data = read_csv_data("public/test_aries_tv2a_sound.csv")
    
    # Get video groups
    video_groups = extract_video_ids_and_models()
    
    # Sort video IDs numerically
    sorted_video_ids = sorted(video_groups.keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))
    
    # Generate JSONL entries
    jsonl_entries = []
    
    for idx, video_id in enumerate(sorted_video_ids):
        models = video_groups[video_id]
        
        # Get prompt from CSV
        prompt = get_prompt_from_csv(csv_data, video_id)
        
        # Create entry
        entry = {
            "sequence_id": idx + 1,
            "video_id": video_id,
            "prompt": prompt,
            "videos": {}
        }
        
        # Map model names to standard names
        model_mapping = {
            'HIFI-Foley': 'hifi-foley',
            'FoleyCrafter': 'foleycrafter', 
            'Frieren': 'frieren',
            'MMAudio': 'mmaudio',
            'ThinkSound': 'thinksound',
            'V_AURA': 'v-aura'
        }
        
        for model_name, video_path in models.items():
            mapped_name = model_mapping.get(model_name, model_name.lower())
            entry["videos"][mapped_name] = video_path
        
        jsonl_entries.append(entry)
    
    # Write to JSONL file
    output_path = "src/assets/model_comparison_videos.jsonl"
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"Generated {len(jsonl_entries)} entries in {output_path}")
    print(f"Available models: {set().union(*[entry['videos'].keys() for entry in jsonl_entries])}")
    
    return jsonl_entries

if __name__ == "__main__":
    generate_model_comparison_jsonl()