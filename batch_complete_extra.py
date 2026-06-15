#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import requests
import json
import re
import time
import argparse
import unicodedata
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
COVERS_DIR = os.path.join(APP_DIR, 'covers')

# Ensure covers directory exists
os.makedirs(COVERS_DIR, exist_ok=True)

def get_db_connection():
    db_path = os.path.join(APP_DIR, 'movies.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_tmdb_key():
    if os.environ.get('TMDB_API_KEY'):
        return os.environ.get('TMDB_API_KEY')
    env_path = os.path.join(APP_DIR, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("TMDB_API_KEY="):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
    return ""

def clean_movie_filename(filename):
    base, _ = os.path.splitext(filename)
    cleaned = re.sub(r'[\._\-\[\]\(\)]', ' ', base)
    year_match = re.search(r'(?<!\d)(19\d{2}|20[0-3]\d)(?!\d)', cleaned)
    year = None
    if year_match:
        year = int(year_match.group(1))
        year_idx = year_match.start()
        cleaned_title = cleaned[:year_idx]
    else:
        cleaned_title = cleaned
        
    tags = [
        r'\b1080p\b', r'\b720p\b', r'\b4k\b', r'\b2160p\b', r'\bbluray\b', r'\bbdrip\b', 
        r'\bweb-dl\b', r'\bwebrip\b', r'\bhdrip\b', r'\bh264\b', r'\bx264\b', r'\bh265\b', 
        r'\bx265\b', r'\bhevc\b', r'\bdts\b', r'\braw\b', r'\bxvid\b', r'\bdivx\b', 
        r'\bremux\b', r'\bchs\b', r'\bcht\b', r'\beng\b', r'\bdual\b', r'\baac\b', r'\bdd5\.1\b'
    ]
    for tag in tags:
        cleaned_title = re.sub(tag, ' ', cleaned_title, flags=re.IGNORECASE)
        
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
    if not cleaned_title:
        cleaned_title = base
    return cleaned_title, year

def extract_metadata_from_path(physical_path):
    if not physical_path:
        return None, None, None
    first_path = physical_path.split(';')[0].strip()
    if not first_path:
        return None, None, None
    first_path = first_path.replace('\\', '/')
    filename = os.path.basename(first_path)
    path_title, path_year = clean_movie_filename(filename)
    
    lang_keywords = {
        'fa': ['persian', 'farsi', 'آینه'],
        'fr': ['french', 'fre', 'chanson'],
        'ja': ['japanese', 'jap'],
        'ko': ['korean', 'kor'],
        'es': ['spanish', 'esp', 'spa'],
        'it': ['italian', 'ita'],
        'de': ['german', 'ger', 'deutsch'],
        'ru': ['russian', 'rus'],
        'zh': ['chinese', 'chs', 'cht', 'mandarin', 'cctv', '国语', '粤语', '中字', '中文字幕', '简体', '繁体'],
        'en': ['english', 'eng']
    }
    
    fn_lower = filename.lower()
    detected_lang = None
    for lang_code, keywords in lang_keywords.items():
        if any(kw in fn_lower for kw in keywords):
            detected_lang = lang_code
            break
            
    return path_title, path_year, detected_lang

def split_chinese_english(title):
    if not title:
        return "", ""
    title = unicodedata.normalize('NFC', title)
    eng_tags = [
        r'\b1080p\b', r'\b720p\b', r'\b4k\b', r'\b2160p\b', r'\bbluray\b', r'\bbdrip\b', r'\bbd\b',
        r'\bweb-dl\b', r'\bwebrip\b', r'\bhdrip\b', r'\bh264\b', r'\bx264\b', r'\bh265\b', 
        r'\bx265\b', r'\bhevc\b', r'\bdts\b', r'\braw\b', r'\bxvid\b', r'\bdivx\b', 
        r'\bremux\b', r'\bchs\b', r'\bcht\b', r'\beng\b', r'\bdual\b', r'\baac\b', r'\bdd5\.1\b',
        r'\bmultiling\b', r'\bdvdrip\b', r'\bdvdriphd\b', r'\bhardsub\b', r'\bwebrip\b',
        r'\bmp4\b', r'\bmkv\b', r'\bavi\b', r'\brmvb\b', r'\bflv\b', r'\bmov\b', r'\bwmv\b', r'\bts\b', r'\bwebm\b',
        r'\bac3\b'
    ]
    zh_tags = [
        r'中英双字', r'中英双语', r'双语中字', r'国波双语', r'中字', r'中文字幕', r'国语配音', 
        r'国粤双语', r'国英双语', r'国语', r'粤语', r'双语', r'国英音轨', r'无水印', r'无极影视', 
        r'人人影视制作', r'人人影视', r'高清无水印', r'超清', r'高清', r'蓝光', r'加长版', r'国波'
    ]
    
    def clean_segment(text):
        if not text:
            return ""
        curr = text
        for tag in eng_tags:
            curr = re.sub(tag, ' ', curr, flags=re.IGNORECASE)
        for tag in zh_tags:
            curr = re.sub(tag, ' ', curr, flags=re.IGNORECASE)
        curr = re.sub(r'\b(?:19|20)\d{2}\b', ' ', curr)
        return curr

    cleaned = title
    bracket_contents = re.findall(r'[\[\(【（]([^\]\)】）]+)[\]\)】）]', cleaned)
    zh_parts = []
    en_parts = []
    
    cleaned_no_brackets = cleaned
    for content in bracket_contents:
        cleaned_content = clean_segment(content).strip()
        if not cleaned_content:
            try:
                cleaned_no_brackets = re.sub(r'[\[\(【（]' + re.escape(content) + r'[\]\)】）]', ' ', cleaned_no_brackets)
            except Exception:
                pass
            continue
            
        if re.search(r'[\u4e00-\u9fff]', cleaned_content):
            zh_parts.append(cleaned_content)
        else:
            en_parts.append(cleaned_content)
            
        try:
            cleaned_no_brackets = re.sub(r'[\[\(【（]' + re.escape(content) + r'[\]\)】）]', ' ', cleaned_no_brackets)
        except Exception:
            pass
            
    cleaned_no_brackets = clean_segment(cleaned_no_brackets)
    cleaned_no_brackets = re.sub(r'[\._\-\[\]\(\)]', ' ', cleaned_no_brackets)
    cleaned_no_brackets = clean_segment(cleaned_no_brackets)
        
    main_zh_matches = re.findall(r'[\u4e00-\u9fff\d：:，,！!]+', cleaned_no_brackets)
    for part in main_zh_matches:
        if re.search(r'[\u4e00-\u9fff]', part):
            zh_parts.append(part)
            cleaned_no_brackets = cleaned_no_brackets.replace(part, ' ')
            
    en_parts.append(cleaned_no_brackets)
    
    def clean_title_str(t_str):
        t_clean = t_str.replace('_', ' ')
        t_clean = re.sub(r'[^\w\s\-\:\uff1a]', ' ', t_clean)
        t_clean = clean_segment(t_clean)
        t_clean = re.sub(r'\s+', ' ', t_clean).strip()
        return t_clean
        
    zh_title = clean_title_str(" ".join(zh_parts))
    en_title = clean_title_str(" ".join(en_parts))
    return zh_title, en_title

def classify_ignore_candidate(title, physical_path=""):
    t_lower = str(title or "").lower()
    p_lower = str(physical_path or "").lower()
    
    if "mock movie" in t_lower or "test movie" in t_lower:
        return True, "Mock Data"
        
    tv_patterns = [
        r'\bs\d{1,2}e\d{1,2}\b',
        r'\bep\d+\b',
        r'\bepisode\s*\d+\b',
        r'第\s*\d+\s*[季集期]',
        r'\bs\d{1,2}\b'
    ]
    for pat in tv_patterns:
        if re.search(pat, t_lower) or re.search(pat, p_lower):
            return True, "TV Show/Episode"
            
    web_keywords = ["mafia ep", "mafia episode", "round 2", "ice nation", "walk the line", "youtube", "bilibili"]
    for kw in web_keywords:
        if kw in t_lower or kw in p_lower:
            return True, "Web/YouTube Video"
            
    yt_id_pattern = r'\[[a-zA-Z0-9_-]{11}\]'
    if re.search(yt_id_pattern, t_lower) or re.search(yt_id_pattern, p_lower):
        return True, "Web/YouTube Video"
        
    return False, ""

def generate_fuzzy_queries(title):
    if not title:
        return []
    queries = []
    cleaned = title.replace('_', ' ').replace('.', ' ').strip()
    stripped = re.sub(r'\s+[-–—]?\s*(?:[1-9]\d?|I{1,3}|IV|VI{0,3}|IX|X)\s*$', '', cleaned, flags=re.IGNORECASE)
    if stripped != cleaned and len(stripped) > 2:
        queries.append(stripped)
        
    words = cleaned.split()
    if len(words) >= 5:
        queries.append(" ".join(words[:4]))
        queries.append(" ".join(words[:3]))
        
    seen = set()
    dedup = []
    for q in queries:
        q_clean = re.sub(r'\s+', ' ', q).strip()
        if q_clean and q_clean.lower() != title.lower() and q_clean not in seen:
            seen.add(q_clean)
            dedup.append(q_clean)
    return dedup

def search_tmdb_movies(title, api_key):
    if not api_key:
        return []
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": title, "language": "en-US"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get('results', [])
    except Exception:
        pass
    return []

def get_tmdb_movie_details(tmdb_id, api_key, lang='zh'):
    if not api_key:
        return None
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    params = {"api_key": api_key, "language": lang, "append_to_response": "credits,external_ids"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def get_best_tmdb_match(title, key, m_dict=None):
    if not key:
        return None
        
    physical_path = m_dict.get('physical_path') if m_dict else None
    db_year = m_dict.get('year') if m_dict else None
    
    path_title, path_year, detected_lang = extract_metadata_from_path(physical_path)
    target_year = path_year or db_year
    
    search_results = []
    if target_year:
        try:
            url = f"https://api.themoviedb.org/3/search/movie"
            params = {"api_key": key, "query": title, "language": "en-US", "year": str(target_year)}
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                search_results = r.json().get('results', [])
        except Exception:
            pass
            
    if not search_results:
        search_results = search_tmdb_movies(title, key)
        
    if not search_results:
        return None
        
    scored_candidates = []
    for r in search_results:
        score = 0
        r_title = r.get('title', '')
        r_orig_title = r.get('original_title', '')
        
        rd = r.get('release_date', '')
        r_year = int(rd.split('-')[0]) if rd else None
        
        title_lower = title.lower().strip()
        r_title_lower = r_title.lower().strip()
        r_orig_title_lower = r_orig_title.lower().strip()
        
        if title_lower == r_title_lower or title_lower == r_orig_title_lower:
            score += 100
        elif title_lower in r_title_lower or title_lower in r_orig_title_lower or r_title_lower in title_lower or r_orig_title_lower in title_lower:
            score += 40
            
        if path_year:
            if r_year == path_year:
                score += 150
            elif r_year and abs(r_year - path_year) == 1:
                score += 80
            elif r_year and abs(r_year - path_year) == 2:
                score += 40
            else:
                score -= 60
        elif db_year:
            try:
                db_year_int = int(db_year)
                if r_year == db_year_int:
                    score += 100
                elif r_year and abs(r_year - db_year_int) == 1:
                    score += 50
                elif r_year and abs(r_year - db_year_int) == 2:
                    score += 20
                else:
                    score -= 40
            except ValueError:
                pass
                
        scored_candidates.append((score, r))
        
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    if scored_candidates:
        return scored_candidates[0][1]
    return None

def search_imdb_suggestion(title):
    if not title:
        return []
    import urllib.parse
    clean_q = title.lower().strip()
    clean_q = re.sub(r'[\s\._\-]+', '_', clean_q)
    clean_q = re.sub(r'[^\w_]', '', clean_q)
    if not clean_q:
        return []
    first_char = clean_q[0]
    if not ('a' <= first_char <= 'z' or '0' <= first_char <= '9'):
        first_char = '_'
    url = f"https://v3.sg.media-imdb.com/suggestion/{first_char}/{urllib.parse.quote(clean_q)}.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for item in data.get('d', []):
                imdb_id = item.get('id', '')
                if imdb_id.startswith('tt'):
                    results.append({
                        'id': imdb_id,
                        'title': item.get('l', ''),
                        'year': item.get('y'),
                        'actors': item.get('s', ''),
                        'cover_url': item.get('i', {}).get('imageUrl') if isinstance(item.get('i'), dict) else None,
                        'qid': item.get('qid', '')
                    })
            return results
    except Exception:
        pass
    return []

def find_tmdb_movie_by_imdb_id(imdb_id, api_key):
    if not imdb_id or not api_key:
        return None
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {
        "api_key": api_key,
        "external_source": "imdb_id",
        "language": "en-US"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get('movie_results', [])
            if results:
                return results[0]
    except Exception:
        pass
    return None

def fetch_wmdb_ratings(title_or_imdb):
    url = f"https://api.wmdb.tv/api/v1/movie"
    params = {"search": title_or_imdb} if not str(title_or_imdb).startswith('tt') else {"id": title_or_imdb}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
    except Exception:
        pass
    return None

def search_duckduckgo_fallback(query):
    import urllib.parse
    import html
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', r.text, re.DOTALL)
            cleaned_snippets = []
            for s in snippets:
                s_clean = re.sub(r'<[^>]+>', '', s)
                s_clean = html.unescape(s_clean).strip()
                if s_clean:
                    cleaned_snippets.append(s_clean)
            if not cleaned_snippets:
                return None, None
            desc = cleaned_snippets[0]
            guessed_year = None
            year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', " ".join(cleaned_snippets))
            if year_match:
                guessed_year = int(year_match.group(1))
            return desc, guessed_year
    except Exception:
        pass
    return None, None

def upload_poster_to_gdrive(movie_id, local_cover_path):
    try:
        TOKEN_PATH = '/Users/shanfu/cc/.agents/skills/google-drive-sync/token.json'
        JSON_MAP_PATH = os.path.join(APP_DIR, 'covers_gdrive.json')

        if not os.path.exists(TOKEN_PATH):
            return None

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            return None

        service = build('drive', 'v3', credentials=creds)

        query = "name = 'MovieLabelCovers' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files = results.get('files', [])
        if files:
            folder_id = files[0]['id']
        else:
            folder_meta = {'name': 'MovieLabelCovers', 'mimeType': 'application/vnd.google-apps.folder'}
            folder = service.files().create(body=folder_meta, fields='id').execute()
            folder_id = folder.get('id')
            service.permissions().create(
                fileId=folder_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()

        filename = f"{movie_id}.jpg"

        q = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
        existing = service.files().list(q=q, spaces='drive', fields='files(id)').execute().get('files', [])
        if existing:
            file_id = existing[0]['id']
        else:
            file_metadata = {'name': filename, 'parents': [folder_id]}
            media = MediaFileUpload(local_cover_path, mimetype='image/jpeg', resumable=True)
            uploaded = service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()
            file_id = uploaded.get('id')
            service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()

        mapping = {}
        if os.path.exists(JSON_MAP_PATH):
            with open(JSON_MAP_PATH, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        mapping[str(movie_id)] = file_id
        with open(JSON_MAP_PATH, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=4, ensure_ascii=False)
        return file_id
    except Exception:
        return None

def update_movie_fields(movie_id, fields_dict):
    conn = get_db_connection()
    cur = conn.cursor()
    set_clause = ", ".join([f"{k} = ?" for k in fields_dict.keys()])
    values = list(fields_dict.values())
    values.append(movie_id)
    cur.execute(f"UPDATE movies SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
    conn.commit()
    conn.close()

def get_movie_details(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}

def generate_report(results_log, start_time, interrupted=False):
    end_time = time.time()
    elapsed = end_time - start_time
    
    total = len(results_log)
    success_list = [r for r in results_log if r['status'] == 'success']
    partial_list = [r for r in results_log if r['status'] == 'partial']
    failed_list = [r for r in results_log if r['status'] == 'failed']
    ignored_list = [r for r in results_log if r['status'] == 'ignored']
    
    report_lines = []
    report_lines.append("="*60)
    status_str = "【任务被用户中断】" if interrupted else "【任务运行完成】"
    report_lines.append(f"{status_str} 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"总耗时: {elapsed:.2f} 秒 ({elapsed/60:.2f} 分钟)")
    report_lines.append(f"总处理影片数: {total}")
    report_lines.append(f"  - 成功 (Success): {len(success_list)}")
    report_lines.append(f"  - 部分成功 (Partial Success): {len(partial_list)}")
    report_lines.append(f"  - 失败 (Failed): {len(failed_list)}")
    report_lines.append(f"  - 忽略 (Ignored): {len(ignored_list)}")
    report_lines.append("="*60)
    
    if ignored_list:
        report_lines.append("\n🚫 忽略影片列表:")
        for r in ignored_list:
            report_lines.append(f"  ID: {r['id']} | {r['title']} (原因: {r.get('reason', '')})")
            
    if failed_list:
        report_lines.append("\n❌ 失败影片列表 (无法匹配或抓取错误):")
        for r in failed_list:
            report_lines.append(f"  ID: {r['id']} | {r['title']} (错误/详情: {r.get('error', '无匹配结果')})")
            
    if partial_list:
        report_lines.append("\n⚠️ 部分成功影片列表 (仅填充了部分信息，例如缺失豆瓣评分):")
        for r in partial_list:
            missing_info = r.get('missing', '未知')
            report_lines.append(f"  ID: {r['id']} | {r['title']} (缺失: {missing_info})")
            
    return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(description="补全影片补充信息命令行脚本 (batch_mode_extra)")
    parser.add_argument('--limit', type=int, default=None, help="最大处理影片数量")
    parser.add_argument('--empty-only', action='store_true', help="仅处理 plot 且 title_zh 均为空的影片 (忽略豆瓣评分状态)")
    parser.add_argument('--delay', type=float, default=1.0, help="每部影片请求间隔延迟(秒)")
    parser.add_argument('--no-gdrive', action='store_true', help="禁用 Google Drive 海报同步")
    args = parser.parse_args()
    
    print("🔍 正在初始化...")
    
    key = load_tmdb_key()
    if not key:
        print("❌ 错误: 未能在环境变量或 .env 中找到 TMDB_API_KEY，请先进行配置。")
        sys.exit(1)
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Target query
    if args.empty_only:
        query = """
            SELECT id, title, year, physical_path, physical_path_mac 
            FROM movies
            WHERE (plot IS NULL OR plot = '') 
              AND (title_zh IS NULL OR title_zh = '')
        """
    else:
        query = """
            SELECT id, title, year, physical_path, physical_path_mac 
            FROM movies
            WHERE plot IS NULL OR plot = ''
               OR title_zh IS NULL OR title_zh = ''
               OR douban_rating IS NULL OR douban_rating = 0
        """
        
    cur.execute(query)
    all_targets = cur.fetchall()
    conn.close()
    
    total_found = len(all_targets)
    if total_found == 0:
        print("🎉 数据库中没有需要补全信息的影片！")
        sys.exit(0)
        
    targets = all_targets
    if args.limit is not None and args.limit < total_found:
        targets = all_targets[:args.limit]
        
    total_to_process = len(targets)
    
    # Runtime Estimation
    # Assume 1.5 seconds network/processing time + user delay
    est_sec_per_movie = args.delay + 1.5
    total_est_seconds = total_to_process * est_sec_per_movie
    est_hours = int(total_est_seconds // 3600)
    est_minutes = int((total_est_seconds % 3600) // 60)
    est_seconds = int(total_est_seconds % 60)
    
    est_time_str = ""
    if est_hours > 0:
        est_time_str += f"{est_hours}小时"
    if est_minutes > 0 or est_hours > 0:
        est_time_str += f"{est_minutes}分钟"
    est_time_str += f"{est_seconds}秒"
    
    print("-" * 50)
    print(f"📊 数据库扫描完成:")
    print(f"  - 发现需要补全的影片总数: {total_found}")
    print(f"  - 本次任务计划处理影片数: {total_to_process}")
    print(f"  - 预估平均每部耗时: {est_sec_per_movie:.1f} 秒")
    print(f"  - 预估总运行时间: {est_time_str}")
    print("-" * 50)
    print("🚀 任务开始，按 Ctrl+C 可随时安全中断并保存当前进度报告。")
    print("-" * 50)
    
    results_log = []
    start_time = time.time()
    interrupted = False
    
    try:
        for idx, row in enumerate(targets):
            m_id = row['id']
            m_title = row['title']
            m_year = row['year']
            p_path = row['physical_path_mac'] or row['physical_path'] or ""
            
            # Print current processing item status
            sys.stdout.write(f"\r⏳ [{idx+1}/{total_to_process}] 正在处理: {m_title[:30]}...")
            sys.stdout.flush()
            
            # 1. Classify Ignore
            is_ignore, ignore_reason = classify_ignore_candidate(m_title, p_path)
            if is_ignore:
                results_log.append({
                    'id': m_id,
                    'title': m_title,
                    'status': 'ignored',
                    'reason': ignore_reason
                })
                continue
                
            # 2. Get existing db info for conditional updating
            existing = get_movie_details(m_id)
            def use_new_if_empty(k, new_val):
                return existing.get(k) if existing.get(k) else new_val
                
            # 3. Retrieve metadata
            m_dict = {"title": m_title, "year": m_year, "physical_path": p_path}
            best = get_best_tmdb_match(m_title, key, m_dict)
            
            details_en = None
            details_zh = None
            imdb_id = None
            tmdb_id_str = None
            imdb_rating = None
            poster_path = None
            
            category = "failed"
            imdb_cover = None
            imdb_actors = None
            matched_title = ""
            matched_year = None
            web_desc = None
            
            if best:
                category = "tmdb"
                tmdb_id = best['id']
                tmdb_id_str = str(tmdb_id)
                matched_title = best.get('title', '')
                rd = best.get('release_date', '')
                matched_year = int(rd.split('-')[0]) if rd else None
                imdb_rating = best.get('vote_average')
                
                try:
                    details_en = get_tmdb_movie_details(tmdb_id, key, lang='en-US')
                    details_zh = get_tmdb_movie_details(tmdb_id, key, lang='zh-CN')
                except Exception:
                    pass
            else:
                # IMDb suggestion fallback
                imdb_cands = search_imdb_suggestion(m_title)
                if not imdb_cands:
                    zh_t, en_t = split_chinese_english(m_title)
                    for q in [zh_t, en_t]:
                        if q and q != m_title:
                            imdb_cands = search_imdb_suggestion(q)
                            if imdb_cands:
                                break
                                
                if imdb_cands:
                    for cand in imdb_cands:
                        tmdb_movie = find_tmdb_movie_by_imdb_id(cand['id'], key)
                        if tmdb_movie:
                            best = tmdb_movie
                            tmdb_id = best['id']
                            tmdb_id_str = str(tmdb_id)
                            matched_title = best.get('title', '')
                            rd = best.get('release_date', '')
                            matched_year = int(rd.split('-')[0]) if rd else None
                            imdb_rating = best.get('vote_average')
                            category = "tmdb"
                            try:
                                details_en = get_tmdb_movie_details(tmdb_id, key, lang='en-US')
                                details_zh = get_tmdb_movie_details(tmdb_id, key, lang='zh-CN')
                            except Exception:
                                pass
                            break
                    
                    if not best:
                        cand = imdb_cands[0]
                        category = "imdb_only"
                        matched_title = cand["title"]
                        matched_year = cand["year"]
                        imdb_id = cand["id"]
                        imdb_actors = cand["actors"]
                        imdb_cover = cand["cover_url"]
                else:
                    # Duckduckgo fallback
                    desc, guessed_year = search_duckduckgo_fallback(m_title)
                    if desc:
                        category = "web"
                        web_desc = desc
                        matched_year = guessed_year
                        
            # Populate proposed fields
            proposed_fields = {}
            if details_en or details_zh:
                details = details_en if details_en else details_zh
                original_title = details.get('original_title')
                runtime = details.get('runtime')
                release_date = details.get('release_date')
                year = int(release_date.split('-')[0]) if release_date else None
                
                genre_names = [g.get('name') for g in (details_en or details).get('genres', [])]
                genres = ", ".join(genre_names)
                
                director_names = [c.get('name') for c in (details_en or details).get('credits', {}).get('crew', []) if c.get('job') == 'Director']
                director = ", ".join(director_names) if director_names else ""
                
                cast_names = [c.get('name') for c in (details_en or details).get('credits', {}).get('cast', [])][:15]
                actors = ", ".join(cast_names) if cast_names else ""
                
                plot = (details_en or details).get('overview')
                
                title_zh = (details_zh or details).get('title') if details_zh else ""
                director_names_zh = [c.get('name') for c in (details_zh or details).get('credits', {}).get('crew', []) if c.get('job') == 'Director']
                director_zh = ", ".join(director_names_zh) if director_names_zh else ""
                
                cast_names_zh = [c.get('name') for c in (details_zh or details).get('credits', {}).get('cast', [])][:15]
                actors_zh = ", ".join(cast_names_zh) if cast_names_zh else ""
                
                plot_zh = (details_zh or details).get('overview')
                countries = [c.get('name') for c in details.get('production_countries', [])]
                country = ", ".join(countries) if countries else ""
                orig_lang = details.get('original_language', '')
                
                spoken = details.get('spoken_languages', [])
                languages = ", ".join([l.get('english_name', '') for l in spoken if l.get('english_name')]) if spoken else ""
                
                external_ids = details.get('external_ids', {})
                imdb_id = external_ids.get('imdb_id') or imdb_id
                
                wmdb_data = fetch_wmdb_ratings(imdb_id if imdb_id else m_title)
                douban_id = None
                douban_rating = None
                if wmdb_data:
                    douban_id = wmdb_data.get('doubanId')
                    douban_rating = wmdb_data.get('doubanRating')
                    if wmdb_data.get('imdbRating'):
                        imdb_rating = wmdb_data.get('imdbRating')
                        
                poster_path = details.get('poster_path')
                
                proposed_fields = {
                    'original_title': use_new_if_empty('original_title', original_title),
                    'director': use_new_if_empty('director', director),
                    'actors': use_new_if_empty('actors', actors),
                    'genres': use_new_if_empty('genres', genres),
                    'year': use_new_if_empty('year', year),
                    'runtime': use_new_if_empty('runtime', runtime),
                    'country': use_new_if_empty('country', country),
                    'original_language': use_new_if_empty('original_language', orig_lang),
                    'languages': use_new_if_empty('languages', languages),
                    'plot': use_new_if_empty('plot', plot),
                    'title_zh': use_new_if_empty('title_zh', title_zh),
                    'director_zh': use_new_if_empty('director_zh', director_zh),
                    'actors_zh': use_new_if_empty('actors_zh', actors_zh),
                    'plot_zh': use_new_if_empty('plot_zh', plot_zh),
                    'imdb_id': use_new_if_empty('imdb_id', imdb_id),
                    'tmdb_id': use_new_if_empty('tmdb_id', tmdb_id_str),
                    'douban_id': use_new_if_empty('douban_id', douban_id),
                    'imdb_rating': use_new_if_empty('imdb_rating', imdb_rating),
                    'douban_rating': use_new_if_empty('douban_rating', douban_rating),
                }
            elif category == "imdb_only":
                proposed_fields = {
                    'original_title': use_new_if_empty('original_title', matched_title),
                    'year': use_new_if_empty('year', matched_year),
                    'actors': use_new_if_empty('actors', imdb_actors),
                    'imdb_id': use_new_if_empty('imdb_id', imdb_id),
                }
            elif category == "web" and web_desc:
                proposed_fields = {
                    'plot': use_new_if_empty('plot', web_desc),
                    'plot_zh': use_new_if_empty('plot_zh', web_desc),
                    'year': use_new_if_empty('year', matched_year)
                }
                
            # 4. Commit to database if we have fields
            if proposed_fields:
                update_movie_fields(m_id, proposed_fields)
                
            # 5. Poster sync
            local_cover = os.path.join(COVERS_DIR, f"{m_id}.jpg")
            poster_url = None
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            elif category == "imdb_only" and imdb_cover:
                poster_url = imdb_cover
                
            if poster_url:
                if not (os.path.exists(local_cover) and os.path.getsize(local_cover) > 0):
                    try:
                        img_r = requests.get(poster_url, timeout=10)
                        if img_r.status_code == 200:
                            with open(local_cover, 'wb') as img_f:
                                img_f.write(img_r.content)
                    except Exception:
                        pass
                        
            if os.path.exists(local_cover) and os.path.getsize(local_cover) > 0 and not args.no_gdrive:
                upload_poster_to_gdrive(m_id, local_cover)
                
            # 6. Evaluate success status
            if not proposed_fields:
                results_log.append({
                    'id': m_id,
                    'title': m_title,
                    'status': 'failed',
                    'error': 'TMDB & IMDb 均未找到相关匹配，Web 搜索 fallback 也无结果'
                })
            else:
                # Success vs Partial Success check
                has_douban = proposed_fields.get('douban_rating') is not None and proposed_fields.get('douban_rating') > 0
                has_plot = proposed_fields.get('plot_zh') or proposed_fields.get('plot')
                has_title_zh = proposed_fields.get('title_zh')
                
                missing = []
                if not has_douban:
                    missing.append("豆瓣评分")
                if not has_plot:
                    missing.append("剧情简介")
                if not has_title_zh:
                    missing.append("中文片名")
                    
                if not missing:
                    results_log.append({
                        'id': m_id,
                        'title': m_title,
                        'status': 'success'
                    })
                else:
                    results_log.append({
                        'id': m_id,
                        'title': m_title,
                        'status': 'partial',
                        'missing': ", ".join(missing)
                    })
                    
            time.sleep(args.delay)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 检测到 Ctrl+C 中断信号，正在生成当前进度报告并安全退出...")
        interrupted = True
        
    # Generate Report
    report = generate_report(results_log, start_time, interrupted)
    print("\n" + report)
    
    # Save log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"batch_complete_log_{timestamp}.txt"
    log_path = os.path.join(APP_DIR, log_filename)
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"💾 详细日志报告已保存至: {log_path}\n")
    except Exception as e:
        print(f"❌ 警告: 无法保存日志文件: {e}\n")

if __name__ == '__main__':
    main()
