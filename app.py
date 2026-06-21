import os
import sys

# ☁️ Cloud Port Auto-Adaptor: 
# If running in cloud environment (not local), dynamically override port to Streamlit's default 8501 
# so cloud health check and routing work seamlessly out-of-the-box.
# Streamlit Cloud runs inside /mount/src container environment, while local is /Users/shanfu.
is_cloud = "/mount/src" in __file__ or "mount/src" in os.getcwd() or os.environ.get("IS_STREAMLIT_CLOUD") == "true"

if is_cloud:
    # 1. Force override in process environment variables which streamlit reads first
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["PORT"] = "8501"
    
    # 2. Force override inside sys.argv BEFORE streamlit is imported
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--server.port"):
            sys.argv[i] = "--server.port=8501"
            break
    else:
        sys.argv.extend(["--server.port", "8501"])


import streamlit as st
import sqlite3
import requests
import base64
import json
import re
from PIL import Image

# Define relative path base
APP_DIR = os.path.dirname(os.path.abspath(__file__))
covers_dir = os.path.join(APP_DIR, 'covers')




# Translation maps for genres and countries in Simplified Chinese
GENRE_MAP_ZH = {
    "Action": "动作",
    "Adventure": "冒险",
    "Animation": "动画",
    "Biography": "传记",
    "Comedy": "喜剧",
    "Crime": "犯罪",
    "Documentary": "纪录",
    "Drama": "剧情",
    "Family": "家庭",
    "Fantasy": "奇幻",
    "History": "历史",
    "Horror": "恐怖",
    "Music": "音乐",
    "Musical": "歌舞",
    "Mystery": "悬疑",
    "Romance": "爱情",
    "Sci-Fi": "科幻",
    "Short": "短片",
    "Sport": "运动",
    "Thriller": "惊悚",
    "War": "战争",
    "Western": "西部",
    "Science Fiction": "科幻",
    "TV Movie": "电视电影",
    "Action & Adventure": "动作冒险",
    "Sci-Fi & Fantasy": "科幻奇幻",
    "Film-Noir": "黑色电影",
    "News": "新闻",
    "Talk-Show": "脱口秀",
    "Reality-TV": "真人秀",
    "Game-Show": "游戏竞技",
    "Adult": "成人"
}

COUNTRY_MAP_ZH = {
    "Afghanistan": "阿富汗",
    "Albania": "阿尔巴尼亚",
    "Algeria": "阿尔及利亚",
    "Argentina": "阿根廷",
    "Australia": "澳大利亚",
    "Austria": "奥地利",
    "Azerbaijan": "阿塞拜疆",
    "Bahamas": "巴哈马",
    "Belarus": "白俄罗斯",
    "Belgium": "比利时",
    "Bhutan": "不丹",
    "Bosnia And Herzegovina": "波黑",
    "Bosnia and Herzegovina": "波黑",
    "Brazil": "巴西",
    "Bulgaria": "保加利亚",
    "Cambodia": "柬埔寨",
    "Canada": "加拿大",
    "Cayman Islands": "开曼群岛",
    "Chile": "智利",
    "China": "中国",
    "Colombia": "哥伦比亚",
    "Cuba": "古巴",
    "Cyprus": "塞浦路斯",
    "Czech Republic": "捷克",
    "Czechia": "捷克",
    "Czechoslovakia": "捷克斯洛伐克",
    "Denmark": "丹麦",
    "Dominican Republic": "多米尼加",
    "East Germany": "东德",
    "Ecuador": "厄瓜多尔",
    "Egypt": "埃及",
    "Estonia": "爱沙尼亚",
    "Federal Republic Of Yugoslavia": "南斯拉夫",
    "Fin": "芬兰",
    "Finland": "芬兰",
    "France": "法国",
    "Georgia": "格鲁吉亚",
    "Germany": "德国",
    "Ghana": "加纳",
    "Greece": "希腊",
    "Guatemala": "危地马拉",
    "Hong Kong": "中国香港",
    "Hungary": "匈牙利",
    "Iceland": "冰岛",
    "India": "印度",
    "Indonesia": "印度尼西亚",
    "Iran": "伊朗",
    "Iraq": "伊拉克",
    "Lithuania": "立陶宛",
    "Croatia": "克罗地亚",
    "Ireland": "爱尔兰",
    "Isle Of Man": "马恩岛",
    "Israel": "以色列",
    "It": "意大利",
    "Italy": "意大利",
    "Japan": "日本",
    "Jordan": "约旦",
    "Kazakhstan": "哈萨克斯坦",
    "Kenya": "肯尼亚",
    "Kuwait": "科威特",
    "Laos": "老挝",
    "Latvia": "拉脱维亚",
    "Lebanon": "黎巴嫩",
    "Libya": "利比亚",
    "Liechtenstein": "列支敦士登",
    "Luxembourg": "卢森堡",
    "Macao SAR China": "中国澳门",
    "Malawi": "马拉维",
    "Malta": "马耳他",
    "Mauritania": "毛里塔尼亚",
    "Mexico": "墨西哥",
    "Monaco": "摩纳哥",
    "Mongolia": "蒙古",
    "Montenegro": "黑山",
    "Morocco": "摩洛哥",
    "Nepal": "尼泊尔",
    "Netherlands": "荷兰",
    "New Zealand": "新西兰",
    "Norway": "挪威",
    "Palestine": "巴勒斯坦",
    "Papua New Guinea": "巴布亚新几内亚",
    "Paraguay": "巴拉圭",
    "Peru": "秘鲁",
    "Philippines": "菲律宾",
    "Poland": "波兰",
    "Portugal": "葡萄牙",
    "Puerto Rico": "波多黎各",
    "Qatar": "卡塔尔",
    "Republic Of North Macedonia": "北马其顿",
    "Macedonia": "北马其顿",
    "Romania": "罗马尼亚",
    "Russia": "俄罗斯",
    "Rwanda": "卢旺达",
    "Serbia": "塞尔维亚",
    "Singapore": "新加坡",
    "Slovakia": "斯洛伐克",
    "Slovenia": "斯洛文尼亚",
    "South Africa": "南非",
    "South Korea": "韩国",
    "Soviet Union": "苏联",
    "Spain": "西班牙",
    "Sudan": "苏丹",
    "Sw": "瑞典",
    "Sweden": "瑞典",
    "Switzerland": "瑞士",
    "Taiwan": "中国台湾",
    "Tajikistan": "塔吉克斯坦",
    "Thailand": "泰国",
    "Tunisia": "突尼斯",
    "Turkey": "土耳其",
    "UK": "英国",
    "USA": "美国",
    "Ukraine": "乌克兰",
    "United Arab Emirates": "阿联酋",
    "United Kingdom": "英国",
    "United States": "美国",
    "United States of America": "美国",
    "Uruguay": "乌拉圭",
    "Venezuela": "委内瑞拉",
    "Vietnam": "越南",
    "West Germany": "西德",
    "Yugoslavia": "南斯拉夫",
    "Ethiopia": "埃塞俄比亚",
    "Namibia": "纳米比亚",
    "Northern Ireland": "北爱尔兰",
    "Palestinian Territory": "巴勒斯坦",
    "Saudi Arabia": "沙特阿拉伯"
}

LANGUAGE_MAP_ZH = {
    "English": "英语",
    "French": "法语",
    "Japanese": "日语",
    "Hindi": "印地语",
    "Chinese": "中文",
    "Portuguese": "葡萄牙语",
    "Italian": "意大利语",
    "Swedish": "瑞典语",
    "German": "德语",
    "Tibetan": "藏语",
    "Danish": "丹麦语",
    "Spanish": "西班牙语",
    "Turkish": "土耳其语",
    "Romanian": "罗马尼亚语",
    "Arabic": "阿拉伯语",
    "Hebrew": "希伯来语",
    "Polish": "波兰语",
    "Norwegian": "挪威语",
    "Wayuu": "瓦尤语",
    "Korean": "韩语",
    "Hungarian": "匈牙利语",
    "Russian": "俄语",
    "Maya": "玛雅语",
    "Persian": "波斯语",
    "Czech": "捷克语",
    "Finnish": "芬兰语",
    "Flemish": "弗拉芒语",
    "Thai": "泰语",
    "Serbian": "塞尔维亚语",
    "Urdu": "乌尔都语",
    "Neapolitan": "那不勒斯语",
    "Tamil": "泰米尔语",
    "Dutch": "荷兰语",
    "Ukrainian Sign Language": "乌克兰手语",
    "Georgian": "格鲁吉亚语",
    "Croatian": "克罗地亚语",
    "Estonian": "爱沙尼亚语",
    "Mandarin": "普通话",
    "Indonesian": "印尼语",
    "Latin": "拉丁语",
    "Bulgarian": "保加利亚语",
    "Serbo-Croatian": "塞尔维亚-克罗地亚语",
    "Latvian": "拉脱维亚语",
    "Macedonian": "马其顿语",
    "Swiss German": "瑞士德语",
    "Khmer": "高棉语",
    "Icelandic": "冰岛语",
    "Lao": "老挝语",
    "Tagalog": "他加禄语",
    "Greek": "希腊语",
    "Saami": "萨米语",
    "Lithuanian": "立陶宛语",
    "Maltese": "马耳他语",
    "Cantonese": "粤语",
    "Sign Languages": "手语",
    "Bengali": "孟加拉语",
    "Armenian": "亚美尼亚语",
    "Kurdish": "库尔德语",
    "Ukrainian": "乌克兰语",
    "Hakka": "客家话",
    "Romany": "罗姆语",
    "Dari": "达里语",
    "Slovak": "斯洛伐克语",
    "Dzongkha": "宗喀语",
    "Basque": "巴斯克语",
    "Slovenian": "斯洛文尼亚语",
    "Kazakh": "哈萨克语",
    "Aboriginal": "原住民语",
    "Albanian": "阿尔巴尼亚语",
    "Vietnamese": "越南语",
    "Low German": "低地德语",
    "Scots": "苏格兰语",
    "Southern Sotho": "南索托语",
    "Bangla": "孟加拉语",
    "Catalan": "加泰罗尼亚语",
    "American Sign Language": "美国手语",
    "Filipino": "菲律宾语",
    "Mongolian": "蒙古语",
    "Afrikaans": "南非荷兰语",
    "Scanian": "斯堪尼亚语",
    "Chechen": "车臣语",
    "Telugu": "泰卢固语",
    "Zulu": "祖鲁语",
    "Aramaic": "阿拉米语",
    "Bosnian": "波斯尼亚语",
    "Irish": "爱尔兰语",
    "Abkhazian": "阿布哈兹语",
    "Akan": "阿肯语",
    "Amharic": "阿姆哈拉语",
    "Azerbaijani": "阿塞拜疆语",
    "Bambara": "班巴拉语",
    "Belarusian": "白俄罗斯语",
    "Breton": "布列塔尼语",
    "Burmese": "缅甸语",
    "Chichewa; Nyanja": "尼扬贾语",
    "Cornish": "康瓦尔语",
    "Corsican": "科西嘉语",
    "Cree": "克里语",
    "Esperanto": "世界语",
    "Ewe": "埃维语",
    "Gaelic": "盖尔语",
    "Galician": "加利西亚语",
    "Guarani": "瓜拉尼语",
    "Gujarati": "古吉拉特语",
    "Haitian; Haitian Creole": "海地克里奥尔语",
    "Ido": "伊多语",
    "Inuktitut": "因纽特语",
    "Kinyarwanda": "卢旺达语",
    "Kirghiz": "吉尔吉斯语",
    "Limburgish": "林堡语",
    "Lingala": "林加拉语",
    "Malay": "马来语",
    "Maori": "毛利语",
    "Marathi": "马拉地语",
    "Navajo": "纳瓦霍语",
    "Nepali": "尼泊尔语",
    "No Language": "无对白",
    "None": "无对白",
    "Northern Sami": "北萨米语",
    "Occitan": "奥克语",
    "Punjabi": "旁遮普语",
    "Pushto": "普什图语",
    "Quechua": "克丘亚语",
    "Raeto-Romance": "罗曼什语",
    "Samoan": "萨摩亚语",
    "Sanskrit": "梵语",
    "Sinhalese": "僧伽罗语",
    "Somali": "索马里语",
    "Sotho": "索托语",
    "Swahili": "斯瓦希里语",
    "Tahitian": "塔希提语",
    "Tajik": "塔吉克语",
    "Tatar": "鞑靼语",
    "Tswana": "茨瓦纳语",
    "Uighur": "维吾尔语",
    "Uzbek": "乌兹别克语",
    "Welsh": "威尔士语",
    "Wolof": "沃洛夫语",
    "Xhosa": "科萨语",
    "Yiddish": "意第绪语",
    "Yoruba": "约鲁巴语",
    "ar": "阿拉伯语",
    "bo": "藏语",
    "cn": "粤语",
    "da": "丹麦语",
    "de": "德语",
    "dz": "宗喀语",
    "el": "希腊语",
    "en": "英语",
    "es": "西班牙语",
    "et": "爱沙尼亚语",
    "fa": "波斯语",
    "fi": "芬兰语",
    "fr": "法语",
    "ga": "爱尔兰语",
    "it": "意大利语",
    "ja": "日语",
    "ko": "韩语",
    "no": "挪威语",
    "pt": "葡萄牙语",
    "ro": "罗马尼亚语",
    "ru": "俄语",
    "sr": "塞尔维亚语",
    "tr": "土耳其语",
    "zh": "中文"
}

def get_country_zh(c):
    if not c:
        return ""
    val = c.strip()
    for k in (val, val.title(), val.lower(), val.upper()):
        if k in COUNTRY_MAP_ZH:
            return COUNTRY_MAP_ZH[k]
    return val

def get_language_zh(l):
    if not l:
        return ""
    val = l.strip()
    for k in (val, val.title(), val.lower(), val.upper()):
        if k in LANGUAGE_MAP_ZH:
            return LANGUAGE_MAP_ZH[k]
    return val

def pinyin_sort_key(s):
    try:
        from pypinyin import lazy_pinyin
        return lazy_pinyin(s)
    except ImportError:
        return [s]

# Initialize Session State Language & Theme early
details_ratio = 40
if "d_width" in st.query_params:
    try:
        details_ratio = int(st.query_params["d_width"])
    except:
        pass
st.session_state.details_width_ratio = details_ratio

if 'lang' not in st.session_state:
    def load_env_var_init(var_name, default_value=""):
        env_path = os.path.join(APP_DIR, '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith(f"{var_name}="):
                            return line.split('=', 1)[1].strip()
            except Exception:
                pass
        return default_value
    
    url_lang = st.query_params.get('lang')
    if url_lang in ['zh', 'en']:
        st.session_state.lang = url_lang
    else:
        env_lang = load_env_var_init('UI_LANG', 'zh')
        st.session_state.lang = env_lang if env_lang in ['zh', 'en'] else 'zh'

if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Set page config
st.set_page_config(
    page_title="Movie Label Revived",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🌐 Internationalization (i18n) Dictionary
I18N = {
    "zh": {
        "title": "🎬 电影收藏管理系统 (Movie Label Revived)",
        "subtitle": "您的 legacy 电影收藏数据库已无损复活、高度增强，并为未来云端同步做好准备。",
        "settings_stats": "⚙️ 其它设置",
        "batch_meta_title": "✨ 批量补全",
        "total_movies": "电影总数",
        "watched": "已看占比",
        "tmdb_key_label": "🔑 TMDB API Key (可选)",
        "tmdb_key_help": "在 themoviedb.org 免费申请 Key 以启用高清海报下载和智能信息补全。",
        "save_key_btn": "💾 保存 API Key",
        "save_key_success": "API Key 已永久保存！",
        "add_entry_title": "添加新电影",
        "add_entry_placeholder": "输入新电影标题...",
        "create_entry_btn": "创建电影条目",
        "create_entry_success": "电影条目 #{id} 创建成功！",
        "search_placeholder": "🔍 搜索电影 (支持中文名、英文名)",
        "filter_genre": "🎭 类型",
        "filter_status": "👁️ 观看状态",
        "filter_country": "🌍 国家/地区",
        "filter_language": "🗣️ 语言",
        "filter_year": "📅 年份",
        "filter_imdb": "⭐ IMDb 评分范围",
        "status_all": "全部",
        "status_seen": "已看",
        "status_unseen": "未看",
        "poster_wall_title": "🎬 电影海报墙",
        "movies_found": "部电影已找到",
        "prev_page": "⬅️ 上一页",
        "next_page": "下一页 ➡️",
        "page_info": "第 {current} 页 / 共 {total} 页",
        "select_prompt": "👈 请在左侧海报墙中选择一部电影以查看详情、自动补全或编辑。",
        "plot_label": "剧情梗概",
        "plot_missing": "暂无剧情简介。请使用下方的‘智能自动补全’选项卡一键填充。",
        "director_label": "导演",
        "genres_label": "类型",
        "actors_label": "演员阵容",
        "path_label": "📂 物理盘片位置 / 视频文件路径",
        "path_missing": "未定义物理路径。请在下方编辑以设定位置。",
        "tab_status": "👁️ 状态与路径",
        "tab_auto": "🤖 智能自动补全",
        "tab_manual": "✏️ 手动编辑字段",
        "manage_status_title": "管理观看状态与物理路径",
        "mark_seen_checkbox": "标记为已看",
        "path_input_label": "物理盘片位置或视频文件路径:",
        "save_status_btn": "保存状态与路径",
        "save_status_success": "观看状态与路径更新成功！",
        "auto_complete_title": "从 IMDb, TMDB & 豆瓣一键补全元数据",
        "search_keywords_label": "输入搜索关键字:",
        "search_tmdb_btn": "检索互联网索引 (TMDB & WMDB)",
        "no_key_warning": "⚠️ TMDB API Key 是必需的。请在设置中配置并永久保存。",
        "no_results_info": "未找到匹配记录，请尝试调整关键字。",
        "match_this_btn": "一键匹配此项",
        "match_success": "元数据与高清海报更新成功！",
        "manual_edit_title": "手动微调/编辑电影基础字段",
        "form_title": "电影标题:",
        "form_orig_title": "原版英文名/别名:",
        "form_year": "年份:",
        "form_runtime": "片长 (分钟):",
        "form_orig_lang": "原语言:",
        "form_audio_lang": "音轨语言 (逗号分隔):",
        "form_genres": "类型标签 (逗号分隔):",
        "form_director": "导演 (逗号分隔):",
        "form_actors": "演员名单 (逗号分隔):",
        "form_plot": "剧情大纲:",
        "form_imdb_id": "IMDb ID:",
        "form_imdb_rating": "IMDb 评分:",
        "form_douban_id": "豆瓣 ID:",
        "form_douban_rating": "豆瓣 评分:",
        "form_country": "国家/地区:",
        "form_tmdb_id": "TMDB ID:",
        "form_submit": "保存手动微调内容",
        "form_success": "电影基本字段保存成功！",
        "batch_title": "🤖 批量元数据补全",
        "batch_warning": "⚠️ 当前有 **{count}** 部电影缺失元数据。",
        "batch_limit_label": "单次运行最大数量",
        "batch_key_warning": "请先配置并永久保存您的 TMDB API Key 以启用批量补全。",
        "batch_start_btn": "🚀 开始批量补全",
        "batch_empty": "没有找到需要补全的电影。",
        "batch_status_label": "正在进行批量补全，请勿关闭浏览器...",
        "batch_status_processing": "正在补全 ({current}/{total}): {title}",
        "batch_success": "🎉 批量运行结束！成功补全: {success} 部，跳过: {skip} 部。",
        "batch_mode_basic": "📋 基础信息",
        "batch_mode_basic_help": "补充缺失：英文片名、海报、年份、类型、IMDb评分、片长、语言、地区",
        "batch_mode_basic_count": "缺失基础信息",
        "batch_mode_extra": "📝 补充信息",
        "batch_mode_extra_help": "补充缺失：剧情简介（英/中）、中文片名、导演、演员、豆瓣评分",
        "batch_mode_extra_count": "缺失补充信息",
        "unnamed_movie": "无名电影",
        "no_alt_title": "无原版别名",
        "unknown_year": "未知年份",
        "unknown_runtime": "未知片长",
        "unknown_language": "未知语言",
        "unknown_country": "未知地区",
        "unknown_director": "未知导演",
        "unknown_genres": "未知类型",
        "unknown_actors": "未知演员",
        "unknown_val": "未知",
        "matching_results": "### 匹配结果:",
        "plot_outline_label": "剧情大纲: ",
        "search_label": "🔍 搜索电影",
        "load_more": "加载更多电影...",
        "columns_slider_label": "🖼️ 列数",
        "sort_label": "🔃 排序方式",
        "sort_year": "出品年份",
        "sort_imdb": "IMDb 评分",
        "sort_douban": "豆瓣评分",
        "sort_alpha": "标题拼音/字母",
        "sort_added": "加入时间",
        "local_play_title": "📂 本地播放与路径映射",
        "path_mapping_section": "路径映射设置",
        "path_mapping_help": "如果数据库中保存的是 legacy Windows 路径（例如 e:\\movies），可以映射为 Mac 挂载路径（例如 /Volumes/movies）。若有多个不同的历史前缀，可用分号 `;` 分割（例如 e:\\movies; f:\\movie; g:\\）。",
        "win_prefix_label": "Windows 路径前缀（若有多个用分号 `;` 隔开）:",
        "mac_prefix_label": "Mac 路径前缀 (例如 /Volumes/movies):",
        "save_mapping_btn": "💾 保存路径映射",
        "save_mapping_success": "路径映射已保存！",
        "browse_btn": "选择目录",
        "scan_drive_title": "🔍 扫描硬盘入库",
        "scan_dir_label": "输入扫描目录路径 (例如 /Volumes/movies):",
        "scan_subdirs_checkbox": "包含子目录",
        "scan_add_new_checkbox": "自动加入影片库 (若影片不存在，则创建新条目)",
        "scan_link_existing_checkbox": "自动关联现有影片 (若影片已存在，且无文件路径，则绑定路径)",
        "start_scan_btn": "🚀 开始扫描硬盘",
        "scan_dir_missing": "请输入有效的扫描目录路径。",
        "scan_dir_not_found": "目录不存在，请输入正确的路径。",
        "import_title": "📥 批量数据导入",
        "import_file_label": "选择 CSV 或 Excel 文件 (.csv, .xlsx):",
        "import_mode_label": "数据匹配冲突处理:",
        "import_mode_fill": "仅填补空缺 (不覆盖已有字段)",
        "import_mode_overwrite": "完全覆盖 (覆盖所有字段)",
        "import_mode_skip": "跳过已有 (只导入新影片)",
        "import_start_btn": "🚀 开始导入数据",
        "import_no_file": "请先选择需要导入的文件。",
        "add_choose_method": "请选择添加方式",
        "manual_add_title": "✍️ 手动添加",
        "scan_drive_title_simple": "🚀 扫描硬盘",
        "batch_import_title_simple": "📥 批量导入",
        "manual_add_card": "手动添加",
        "scan_drive_card": "扫描硬盘",
        "batch_import_card": "批量导入",
        "back_btn": "⬅️ 返回",
        "path_mapping_current": "📋 当前映射规则",
        "path_mapping_none": "暂无映射规则",
        "path_mapping_add": "➕ 添加新映射",
        "path_mapping_win_lbl": "Windows 前缀",
        "path_mapping_mac_lbl": "Mac 前缀",
        "path_mapping_add_btn": "💾 添加",
        "path_mapping_input_err": "请输入完整前缀",
        "manual_loc_zh_header": "本地化 (中文)",
        "manual_zh_title": "译名 (中文)",
        "manual_zh_director": "导演 (中文)",
        "manual_zh_actors": "演员 (中文)",
        "manual_zh_plot": "剧情梗概 (中文)",
        "manual_file_watch_header": "📁 物理与播放状态",
        "manual_file_path": "物理路径",
        "manual_watched": "标记为已看",
        "scan_report_header": "📊 扫描报告",
        "scan_report_stats": "📁 文件总数: **{total}** | ➕ 新增: **{added}** | 🔗 关联: **{linked}** | ⏭️ 跳过: **{skipped}**",
        "import_report_header": "📊 导入报告",
        "import_report_stats": "📄 行总数: **{total}** | ➕ 新增: **{added}** | 🔄 更新: **{updated}** | ⏭️ 跳过: **{skipped}**",
        "detailed_log": "📄 详细日志",
        "title_required_err": "标题不能为空",
        "select_btn": "选择",
        "close_btn": "关闭",
        "confirm_btn": "确认",
        "cancel_btn": "取消",
        "delete_confirm_msg": "确定要永久删除这部影片吗？",
        "select_dir_prompt": "选择扫描目录:",
        "path_input_placeholder": "输入物理路径...",
        "play_path_not_found": " (⚠️ 路径未找到)",
        "toast_playing": "正在播放: {filename}",
        "error_playback_failed": "播放失败: {err}",
        "duplicate_approval_title": "📋 同名影片路径修改与重复审批",
        "duplicate_approval_help": "以下视频在本地已存在同名但路径不同的记录，请选择处理方式 (可选择修改存储路径或添加映射)：",
        "btn_all_update": "全部更新路径",
        "btn_all_mapping": "全部设为映射",
        "btn_all_add": "全部作为新片入库",
        "btn_all_link": "全部关联为多版本",
        "btn_all_skip": "全部跳过",
        "table_hdr_movie": "影片名",
        "table_hdr_orig_path": "原片存放路径",
        "table_hdr_curr_path": "当前扫描路径",
        "table_hdr_action": "处理方式",
        "action_update": "🔄 更新",
        "action_mapping": "🗺️ 映射",
        "action_add": "➕ 新增",
        "action_link": "🔗 多版本",
        "action_skip": "⏭️ 跳过",
        "status_moved": "原文件不存在 (移动/重命名)",
        "status_duplicate": "原文件仍存在 (疑似重复)",
        "suggested_mappings_title": "💡 推荐路径映射规则 (批量添加)",
        "suggested_mappings_help": "检测到本地文件路径与数据库中不一致。你可以选择勾选以下规则，系统将自动添加映射，无需逐一修改数据库：",
        "toast_mapping_saved": "路径映射已成功保存！",
        "approval_success": "🎉 审批处理完成！新增 {added} 部，更新/关联 {linked} 部，跳过 {skipped} 部。",
        "scan_err_dir_not_found": "❌ 目录不存在: {path}",
        "scan_err_read_failed": "❌ 读取目录失败: {err}",
        "scan_info_no_videos": "ℹ️ 未找到视频文件。",
        "scan_log_linked": "🔗 关联成功: {title} ➡️ {filename}",
        "scan_log_path_updated": "🔄 路径更新: {title} ➡️ {filename}",
        "scan_log_autolinked_multi": "🔗 自动关联多版本: {title} ➡️ {filename}",
        "scan_log_added_new": "➕ 新增影片: {title} ({year}) ➡️ {filename}",
        "scan_log_insert_failed": "❌ 新增失败 {title}: {err}",
        "import_err_unsupported": "❌ 不支持的文件格式 (仅支持 CSV 或 Excel)。",
        "import_err_read_failed": "❌ 读取文件失败: {err}",
        "import_info_empty": "ℹ️ 文件中没有数据。",
        "import_err_no_title_col": "❌ 未在文件中找到“标题”或“Title”列。",
        "import_log_updated": "🔄 更新成功: {title} (ID: {id})",
        "import_log_update_failed": "❌ 更新失败 {title}: {err}",
        "import_log_imported_new": "➕ 导入新增: {title}",
        "import_log_import_failed": "❌ 导入失败 {title}: {err}",
        "duplicate_check_section": "🎬 重复影片检查",
        "run_duplicate_check_btn": "🔍 运行重复检查",
        "duplicate_check_dialog_title": "重复影片检查 (Duplicate Check)",
        "no_duplicates_found": "🎉 未检测到任何重复影片！",
        "duplicates_warning": "⚠️ 检测到 {count} 组疑似重复的影片条目：",
        "duplicate_movies_unit": "个重复条目",
        "close_btn": "关闭",
        "mismatch_help": "⚠️ 检测到相同关联 ID 但物理路径年份冲突的影片（疑似数据库导入或自动匹配错误，请点击编辑修正）：",
        "mismatch_movies_unit": "个关联条目"
    },
    "en": {
        "title": "🎬 Movie Label Revived",
        "subtitle": "Your legacy movie catalog database resurrected, enhanced, and ready for future cloud sync.",
        "settings_stats": "⚙️ Other Settings",
        "batch_meta_title": "✨ Batch Metadata",
        "total_movies": "Total Movies",
        "watched": "Watched Ratio",
        "tmdb_key_label": "🔑 TMDB API Key (Optional)",
        "tmdb_key_help": "Get a free key at themoviedb.org to enable HD poster downloading and complete metadata autocompletion.",
        "save_key_btn": "💾 Save API Key",
        "save_key_success": "API Key saved permanently!",
        "add_entry_title": "Add Movie",
        "add_entry_placeholder": "Enter new movie title...",
        "create_entry_btn": "Create Movie Entry",
        "create_entry_success": "Movie entry #{id} created successfully!",
        "search_placeholder": "🔍 Search Movies (by Chinese or English title)",
        "filter_genre": "🎭 Genre",
        "filter_status": "👁️ Watch Status",
        "filter_country": "🌍 Country/Region",
        "filter_language": "🗣️ Language",
        "filter_year": "📅 Year",
        "filter_imdb": "⭐ IMDb Rating",
        "status_all": "All",
        "status_seen": "Watched",
        "status_unseen": "Not Watched",
        "poster_wall_title": "🎬 Poster Wall",
        "movies_found": "movies found",
        "prev_page": "⬅️ Prev",
        "next_page": "Next ➡️",
        "page_info": "Page {current} of {total}",
        "select_prompt": "👈 Select a movie from the Poster Wall to inspect details, autocomplete ratings, or manage watch statuses.",
        "plot_label": "PLOT SYNOPSIS",
        "plot_missing": "No plot summary available. Use the Auto-Complete tab below to populate metadata instantly.",
        "director_label": "DIRECTOR",
        "genres_label": "GENRES",
        "actors_label": "CAST LIST",
        "path_label": "📂 MOVIE PATH / PHYSICAL DISCS",
        "path_missing": "Not defined. Edit status below to define location.",
        "tab_status": "👁️ Status & Path",
        "tab_auto": "🤖 Auto-Complete Metadata",
        "tab_manual": "✏️ Edit Fields Manually",
        "manage_status_title": "Manage Status & Physical Files",
        "mark_seen_checkbox": "Mark as Watched",
        "path_input_label": "Physical Disc or Movie Path:",
        "save_status_btn": "Save Status & Location",
        "save_status_success": "Successfully updated watch status and path details!",
        "auto_complete_title": "Auto-Complete metadata from IMDb, TMDB & Douban",
        "search_keywords_label": "Enter search keywords:",
        "search_tmdb_btn": "Search TMDB & WMDB Index",
        "no_key_warning": "⚠️ TMDB API Key is required. Please configure and permanently save it in settings.",
        "no_results_info": "No matching records found. Try modifying the keywords.",
        "match_this_btn": "Match This",
        "match_success": "Metadata and high-resolution cover successfully updated!",
        "manual_edit_title": "Manual Editing of Basic Fields",
        "form_title": "Title:",
        "form_orig_title": "Original Title:",
        "form_year": "Year:",
        "form_runtime": "Runtime (Mins):",
        "form_orig_lang": "Original Language:",
        "form_audio_lang": "Audio Languages (comma-separated):",
        "form_genres": "Genres (comma-separated):",
        "form_director": "Director (comma-separated):",
        "form_actors": "Cast List (comma-separated):",
        "form_plot": "Plot Outline:",
        "form_imdb_id": "IMDb ID:",
        "form_imdb_rating": "IMDb Rating:",
        "form_douban_id": "Douban ID:",
        "form_douban_rating": "Douban Rating:",
        "form_country": "Country/Region:",
        "form_tmdb_id": "TMDB ID:",
        "form_submit": "Save Manual Corrections",
        "form_success": "Successfully updated movie details!",
        "batch_title": "🤖 Batch Autocomplete",
        "batch_warning": "⚠️ Currently **{count}** movies are missing basic metadata.",
        "batch_limit_label": "Max movies to process in this run",
        "batch_key_warning": "Please configure and permanently save your TMDB API Key in settings first.",
        "batch_start_btn": "🚀 Start Batch Autocomplete",
        "batch_empty": "No movies found that require autocompletion.",
        "batch_status_label": "Performing batch autocomplete, do not close your browser...",
        "batch_status_processing": "Processing ({current}/{total}): {title}",
        "batch_success": "🎉 Batch run complete! Successfully updated: {success} movies, skipped: {skip} movies.",
        "unnamed_movie": "Unnamed Movie",
        "no_alt_title": "No alternative title",
        "unknown_year": "Unknown Year",
        "unknown_runtime": "Unknown Runtime",
        "unknown_language": "Unknown Language",
        "unknown_country": "Unknown Country",
        "unknown_director": "Unknown Director",
        "unknown_genres": "Unknown Genres",
        "unknown_actors": "Unknown Cast",
        "unknown_val": "Unknown",
        "matching_results": "### Matching Results:",
        "plot_outline_label": "Plot Outline: ",
        "search_label": "🔍 Search Movies",
        "load_more": "Load More Movies...",
        "columns_slider_label": "🖼️ Cols",
        "sort_label": "🔃 Sort By",
        "sort_year": "Year",
        "sort_imdb": "IMDb Rating",
        "sort_douban": "Douban Rating",
        "sort_alpha": "Alphabetical",
        "sort_added": "Date Added",
        "local_play_title": "📂 Local Playback & Mapping",
        "path_mapping_section": "Path Mapping Settings",
        "path_mapping_help": "If the database stores legacy Windows paths (e.g., e:\\movies), you can map them to Mac mount paths (e.g., /Volumes/movies). If you have multiple historic prefixes, separate them with semicolons `;` (e.g., e:\\movies; f:\\movie; g:\\).",
        "win_prefix_label": "Windows Path Prefixes (separate with semicolons `;`):",
        "mac_prefix_label": "Mac Path Prefix (e.g., /Volumes/movies):",
        "save_mapping_btn": "💾 Save Path Mapping",
        "save_mapping_success": "Path mapping saved successfully!",
        "browse_btn": "Browse...",
        "scan_drive_title": "🔍 Scan Hard Drive",
        "scan_dir_label": "Enter Directory Path (e.g., /Volumes/movies):",
        "scan_subdirs_checkbox": "Scan Subdirectories",
        "scan_add_new_checkbox": "Automatically Add New Movies (Create entry if not exists)",
        "scan_link_existing_checkbox": "Automatically Link Existing Movies (Bind path if exists with empty path)",
        "start_scan_btn": "🚀 Start Scanning Directory",
        "scan_dir_missing": "Please enter a valid directory path.",
        "scan_dir_not_found": "Directory not found. Please enter a correct path.",
        "import_title": "📥 Batch Data Import",
        "import_file_label": "Choose CSV or Excel File (.csv, .xlsx):",
        "import_mode_label": "Conflict Resolution Mode:",
        "import_mode_fill": "Fill Empty (Do not overwrite existing values)",
        "import_mode_overwrite": "Overwrite (Replace existing values)",
        "import_mode_skip": "Skip Existing (Only import new movies)",
        "import_start_btn": "🚀 Start Import Process",
        "import_no_file": "Please choose a file to import first.",
        "add_choose_method": "Choose Add Method:",
        "manual_add_title": "✍️ Manual Add",
        "scan_drive_title_simple": "🚀 Scan Hard Drive",
        "batch_import_title_simple": "📥 Batch Import",
        "manual_add_card": "Manual Add",
        "scan_drive_card": "Scan Hard Drive",
        "batch_import_card": "Batch Import",
        "back_btn": "⬅️ Back",
        "path_mapping_current": "📋 Current Mappings",
        "path_mapping_none": "No mapping rules configured",
        "path_mapping_add": "➕ Add New Mapping",
        "path_mapping_win_lbl": "Win Prefix",
        "path_mapping_mac_lbl": "Mac Prefix",
        "path_mapping_add_btn": "💾 Add",
        "path_mapping_input_err": "Input required",
        "manual_loc_zh_header": "Localizations (Chinese)",
        "manual_zh_title": "Chinese Title",
        "manual_zh_director": "Chinese Director",
        "manual_zh_actors": "Chinese Cast",
        "manual_zh_plot": "Chinese Plot Outline",
        "manual_file_watch_header": "📁 File & Watch Status",
        "manual_file_path": "File Path",
        "manual_watched": "Watched",
        "scan_report_header": "📊 Scan Report",
        "scan_report_stats": "📁 Total: **{total}** | ➕ Added: **{added}** | 🔗 Linked: **{linked}** | ⏭️ Skipped: **{skipped}**",
        "import_report_header": "📊 Import Report",
        "import_report_stats": "📄 Total Rows: **{total}** | ➕ Added: **{added}** | 🔄 Updated: **{updated}** | ⏭️ Skipped: **{skipped}**",
        "detailed_log": "📄 Detailed Log",
        "title_required_err": "Title is required",
        "select_btn": "Select",
        "close_btn": "Close",
        "confirm_btn": "Confirm",
        "cancel_btn": "Cancel",
        "delete_confirm_msg": "Are you sure you want to permanently delete this movie?",
        "select_dir_prompt": "Choose Movie Directory:",
        "path_input_placeholder": "Enter file path...",
        "play_path_not_found": " (⚠️ Path Not Found)",
        "toast_playing": "Playing: {filename}",
        "error_playback_failed": "Playback failed: {err}",
        "duplicate_approval_title": "📋 Duplicate Movies and Path Mapping Approval",
        "duplicate_approval_help": "The following videos have matching titles in the database but different paths. Please choose an action (e.g., update path or add mapping):",
        "btn_all_update": "All Update",
        "btn_all_mapping": "All Map Prefix",
        "btn_all_add": "All Add",
        "btn_all_link": "All Link",
        "btn_all_skip": "All Skip",
        "table_hdr_movie": "Movie",
        "table_hdr_orig_path": "Original Path",
        "table_hdr_curr_path": "Current Path",
        "table_hdr_action": "Action",
        "action_update": "🔄 Update",
        "action_mapping": "🗺️ Map Prefix",
        "action_add": "➕ Add New",
        "action_link": "🔗 Link",
        "action_skip": "⏭️ Skip",
        "status_moved": "Original file missing (Moved/Renamed)",
        "status_duplicate": "Original file exists (Suspected duplicate)",
        "suggested_mappings_title": "💡 Recommended Path Mapping Rules (Batch Add)",
        "suggested_mappings_help": "Detected path mismatches. You can check the rules below to automatically add mapping rules without modifying the database paths:",
        "toast_mapping_saved": "Path mappings saved successfully!",
        "approval_success": "🎉 Approvals processed! Added {added}, updated/linked {linked}, skipped {skipped}.",
        "scan_err_dir_not_found": "❌ Directory not found: {path}",
        "scan_err_read_failed": "❌ Read directory failed: {err}",
        "scan_info_no_videos": "ℹ️ No video files found.",
        "scan_log_linked": "🔗 Linked: {title} ➡️ {filename}",
        "scan_log_path_updated": "🔄 Path updated: {title} ➡️ {filename}",
        "scan_log_autolinked_multi": "🔗 Auto-linked multi-part: {title} ➡️ {filename}",
        "scan_log_added_new": "➕ Added new: {title} ({year}) ➡️ {filename}",
        "scan_log_insert_failed": "❌ Insert failed for {title}: {err}",
        "import_err_unsupported": "❌ Unsupported format (only CSV or Excel).",
        "import_err_read_failed": "❌ Read file failed: {err}",
        "import_info_empty": "ℹ️ Uploaded file is empty.",
        "import_err_no_title_col": "❌ Could not find 'title' column in the uploaded file.",
        "import_log_updated": "🔄 Updated: {title} (ID: {id})",
        "import_log_update_failed": "❌ Update failed for {title}: {err}",
        "import_log_imported_new": "➕ Imported new: {title}",
        "import_log_import_failed": "❌ Import failed for {title}: {err}",
        "duplicate_check_section": "🎬 Duplicate Check",
        "run_duplicate_check_btn": "🔍 Run Duplicate Check",
        "duplicate_check_dialog_title": "Duplicate Movie Check",
        "no_duplicates_found": "🎉 No duplicate movies detected!",
        "duplicates_warning": "⚠️ Detected {count} groups of suspected duplicate movie entries:",
        "duplicate_movies_unit": "duplicates",
        "close_btn": "Close",
        "mismatch_help": "⚠️ Conflicting filename years detected sharing the same metadata ID (suspected import/autocomplete mismatch, edit to correct):",
        "mismatch_movies_unit": "linked entries"
    }
}

# Translation helper function
def t(key, **kwargs):
    lang = st.session_state.get('lang', 'zh')
    text = I18N[lang].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# Centered Web Dialog Preview Helper
if hasattr(st, "dialog"):
    @st.dialog("网页预览 (Web Preview)", width="large")
    def show_web_dialog(title, url):
        st.markdown(f"""
        <div style="background-color: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 0.85rem; line-height: 1.4;">
            🔒 <b>安全提示</b>: 目标主站 ({title}) 启用了防跨站嵌套 (SAMEORIGIN) 或 Cloudflare 人机安全校验。如果下方内嵌区域因浏览器安全策略显示空白或人机验证报错，请直接点击下方按钮打开独立窗口访问：
        </div>
        """, unsafe_allow_html=True)
        
        # Display high-fidelity native link button at the top
        st.link_button(f"🚀 访问 {title} 官网独立页面", url, use_container_width=True)
        st.divider()
        
        # Embedded web preview iframe
        st.components.v1.iframe(url, height=500, scrolling=True)
else:
    def show_web_dialog(title, url):
        st.session_state.web_preview_title = title
        st.session_state.web_preview_url = url

# Dynamic Premium Color Theme Variables
if st.session_state.theme == 'light':
    bg_color = "#F8FAFC"
    text_color = "#0F172A"
    sub_text_color = "#475569"
    card_bg = "#FFFFFF"
    card_border = "rgba(15, 23, 42, 0.08)"
    panel_bg = "#F1F5F9"
    panel_border = "rgba(15, 23, 42, 0.1)"
    scrollbar_track = "#F1F5F9"
    scrollbar_thumb = "#CBD5E1"
    card_hover_border = "rgba(56, 189, 248, 0.6)"
    header_gradient = "linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%)"
    header_border = "rgba(15, 23, 42, 0.08)"
    header_title_color = "#0F172A"
    code_bg = "#E2E8F0"
    code_text = "#0F172A"
    tab_text = "#475569"
    active_tab_border = "#38BDF8"
    poster_placeholder_bg = "linear-gradient(135deg, #E2E8F0 0%, #F1F5F9 100%)"
    poster_placeholder_text = "#475569"
    poster_border_color = "rgba(15, 23, 42, 0.08)"
    control_border = "rgba(15, 23, 42, 0.15)"
else:
    bg_color = "#0F172A"
    text_color = "#F8FAFC"
    sub_text_color = "#94A3B8"
    card_bg = "#1E293B"
    card_border = "rgba(255, 255, 255, 0.08)"
    panel_bg = "#1E293B"
    panel_border = "rgba(255, 255, 255, 0.12)"
    scrollbar_track = "#0F172A"
    scrollbar_thumb = "#334155"
    card_hover_border = "rgba(56, 189, 248, 0.6)"
    header_gradient = "linear-gradient(135deg, #1E293B 0%, #0F172A 100%)"
    header_border = "rgba(255, 255, 255, 0.1)"
    header_title_color = "#F8FAFC"
    code_bg = "#1E293B"
    code_text = "#38BDF8"
    tab_text = "#94A3B8"
    active_tab_border = "#38BDF8"
    poster_placeholder_bg = "linear-gradient(135deg, #1E293B 0%, #0F172A 100%)"
    poster_placeholder_text = "#64748B"
    poster_border_color = "rgba(255, 255, 255, 0.15)"
    control_border = "rgba(255, 255, 255, 0.2)"

# Inject Dynamic Premium CSS for styling
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    @import url('https://cdn.jsdelivr.net/npm/lxgw-wenkai-screen-webfont/style.css');
    
    :root {{
        --font: 'Outfit', 'LXGW WenKai Screen', 'STKaiti', 'Kaiti SC', 'KaiTi', 'BiauKai', serif !important;
        --sans-serif: 'Outfit', 'LXGW WenKai Screen', 'STKaiti', 'Kaiti SC', 'KaiTi', 'BiauKai', serif !important;
    }}
    
    html, body, [class*="css"], [class*="st-"] {{
        font-family: 'Outfit', 'LXGW WenKai Screen', 'STKaiti', 'Kaiti SC', 'KaiTi', 'BiauKai', serif !important;
    }}
    
    /* Universal font override, excluding code elements and icons to preserve formatting/glyphs */
    *:not(code):not(pre):not(kbd):not(samp):not(.stCodeBlock):not([class*="code"]):not([data-testid="stIcon"]):not([class*="Icon"]):not([class*="icon"]):not(style):not(script) {{
        font-family: 'Outfit', 'LXGW WenKai Screen', 'STKaiti', 'Kaiti SC', 'KaiTi', 'BiauKai', serif !important;
    }}
    
    code, pre, kbd, samp, .stCodeBlock, [class*="code"] {{
        font-family: monospace !important;
    }}
    
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    
    /* Force selectbox, slider, and text input labels to adjust color based on active theme */
    label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, .stWidgetLabel {{
        color: {text_color} !important;
    }}
    
    .header-label {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: {sub_text_color} !important;
        white-space: nowrap !important;
        text-align: right !important;
        opacity: 0.85 !important;
    }}
    
    .toggle-label-left, .toggle-label-right {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: {sub_text_color} !important;
        opacity: 0.85 !important;
        white-space: nowrap !important;
        display: inline-block !important;
    }}
    
    /* Inline flex container for toggles with left and right text labels */
    div[data-testid="stColumn"]:has(.toggle-label-left):not(:has([data-testid="stHorizontalBlock"])) > div[data-testid="stVerticalBlock"] {{
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0.35rem !important;
        width: auto !important;
        justify-content: flex-start !important;
    }}
    div[data-testid="stColumn"]:has(.toggle-label-left):not(:has([data-testid="stHorizontalBlock"])) > div[data-testid="stVerticalBlock"] > div {{
        width: auto !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    /* Completely hide Streamlit top header bar and Deploy button to save space */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    
    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {{
        display: none !important;
    }}
    
    /* Reclaim wasted white space and lock vertical scroll on container level */
    div[data-testid="stAppViewBlockContainer"],
    div[data-testid="stMainBlockContainer"],
    .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }}
    
    /* Force all Streamlit wrapper layers to full width */
    section[data-testid="stMain"],
    div[data-testid="stMainBlockContainer"],
    .main .block-container,
    [data-testid="stAppViewContainer"] > section,
    [data-testid="stAppViewContainer"] > section > div {{
        max-width: 100% !important;
        width: 100% !important;
        padding-right: 0 !important;
    }}
    
    /* Force the columns flex container (parent of col_wall and col_details) to fill full width */
    div[data-testid="stHorizontalBlock"]:has(.poster-wall-marker),
    div[data-testid="stHorizontalBlock"]:has(.details-panel-marker) {{
        width: 100% !important;
        max-width: 100% !important;
        flex-wrap: nowrap !important;
    }}
    
    /* Absolutely fix the top header and filter bar so they never scroll away */
    /* By using nested stVerticalBlock selectors, we target the header container but exclude the root container */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        padding-top: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        padding-bottom: 0.5rem !important;
        background-color: {bg_color} !important;
        z-index: 99999 !important;
        border-bottom: 1px solid {card_border} !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    }}

    /* Align all filter columns to the bottom baseline so search and dropdowns are in one perfect line */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) div[data-testid="stColumn"] {{
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }}
    
    /* Force specific native Streamlit containers to perfectly fit the viewport and scroll independently */
    /* Left pane scrolls naturally with the page, no fixed height */
    div[data-testid="stColumn"]:has(.poster-wall-marker) {{
        padding-bottom: 2rem;
        padding-right: 1rem;
    }}
    
    /* (CSS overlay for poster clicks removed to prevent layout bugs) */

    /* Highlight search input */
    div[data-testid="stTextInput"]:has(input[placeholder*="🔍"]) input {{
        border: 2px solid #38BDF8 !important;
        background-color: rgba(56, 189, 248, 0.05) !important;
        font-weight: 600 !important;
        font-size: 1.02rem !important;
        border-radius: 8px !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.15) !important;
        transition: all 0.3s ease !important;
    }}
    div[data-testid="stTextInput"]:has(input[placeholder*="🔍"]) input:focus {{
        border-color: #818CF8 !important;
        box-shadow: 0 0 15px rgba(129, 140, 248, 0.3) !important;
        background-color: rgba(129, 140, 248, 0.08) !important;
    }}

    .stat-number {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        color: #38BDF8 !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.4) !important;
        line-height: 1 !important;
        display: inline-block;
        vertical-align: middle;
        padding: 0 0.1rem;
    }}

    
    /* Right pane is sticky/floating so it never leaves the viewport */
    div[data-testid="stColumn"]:has(.details-panel-marker) {{
        position: sticky !important;
        top: 150px !important;
        height: calc(100vh - 160px) !important;
        align-self: flex-start;
        padding-right: 0 !important;
        margin-right: 0 !important;
    }}
    
    div[data-testid="stColumn"]:has(.details-panel-marker) > div[data-testid="stVerticalBlock"] {{
        height: 100% !important;
        overflow-y: scroll !important;
        overflow-x: hidden !important;
        scrollbar-gutter: stable !important;
        background: {panel_bg};
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid {panel_border};
        border-right: none;
        border-radius: 20px 0 0 20px;
        padding: 1.5rem;
        padding-right: 1.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        transition: background 0.3s ease, border-color 0.3s ease;
    }}
    
    .movie-poster-container {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        border: 1px solid {poster_border_color};
        margin-bottom: 1.2rem;
    }}
    
    .poster-img-container {{
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
        background-color: {poster_placeholder_bg};
        display: flex;
        position: relative;
    }}

    .poster-status-badge {{
        position: absolute;
        top: 8px;
        right: 8px;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 800;
        z-index: 5;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 0.15rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        line-height: 1;
        white-space: nowrap;
    }}
    
    .poster-status-seen {{
        background-color: #22C55E !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }}
    
    .poster-status-unseen {{
        background-color: rgba(15, 23, 42, 0.75) !important;
        color: #94A3B8 !important;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    
    .poster-img {{
        width: 100%;
        height: 100%;
        aspect-ratio: 2 / 3 !important;
        object-fit: fill !important;
        border-radius: 8px !important;
        display: block;
        border: 1px solid {poster_border_color} !important;
        box-sizing: border-box !important;
    }}
    
    .movie-poster-placeholder {{
        display: flex;
        align-items: center;
        justify-content: center;
        height: 360px;
        background: {poster_placeholder_bg};
        color: {poster_placeholder_text};
        font-size: 4rem;
        border-radius: 12px;
        border: 1px dashed rgba(255, 255, 255, 0.1);
    }}
    
    .movie-title-header {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {text_color};
        margin-bottom: 0.25rem;
        line-height: 1.2;
    }}
    
    .movie-orig-title {{
        font-size: 1.1rem;
        color: {sub_text_color};
        font-style: italic;
        margin-bottom: 1rem;
    }}
    
    /* Custom Badges */
    .badge-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1.2rem;
    }}
    
    .custom-badge {{
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        transition: all 0.2s ease;
    }}
    
    .badge-year {{ background: rgba(56, 189, 248, 0.1); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.2); }}
    .badge-runtime {{ background: rgba(129, 140, 248, 0.1); color: #818CF8; border: 1px solid rgba(129, 140, 248, 0.2); }}
    .badge-country {{ background: rgba(244, 63, 94, 0.1); color: #F43F5E; border: 1px solid rgba(244, 63, 94, 0.2); }}
    .badge-language {{ background: rgba(52, 211, 153, 0.1); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.2); }}
    
    .badge-imdb {{ background: #E5A93B; color: #000000; font-weight: 800; cursor: pointer; }}
    .badge-imdb:hover {{ background: #f5c518 !important; transform: scale(1.05); }}
    .badge-douban {{ background: #42BD56; color: #FFFFFF; font-weight: 800; cursor: pointer; }}
    .badge-douban:hover {{ background: #2E963D !important; transform: scale(1.05); }}
    .badge-tmdb {{ background: #01B4E4; color: #FFFFFF; font-weight: 800; cursor: pointer; }}
    .badge-tmdb:hover {{ background: #0093be !important; transform: scale(1.05); }}
    .badge-status-seen {{ background: rgba(34, 197, 94, 0.1); color: #4ADE80; border: 1px solid rgba(34, 197, 94, 0.2); }}
    .badge-status-unseen {{ background: rgba(239, 68, 68, 0.1); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.2); }}
    
    .movie-metadata-label {{
        color: {sub_text_color};
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }}
    
    .movie-metadata-value {{
        color: {text_color};
        font-size: 0.95rem;
        margin-bottom: 1rem;
        opacity: 0.9;
    }}
    
    /* Styling scrollbars */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {scrollbar_track};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {scrollbar_thumb};
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #334155;
    }}
    
    /* Hide Streamlit Status/Running Indicator Bar */
    [data-testid="stStatusWidget"] {{
        display: none !important;
    }}
    
    /* Override code blocks */
    code {{
        background-color: {code_bg} !important;
        color: {code_text} !important;
    }}
    
    /* Premium Title highlight style */
    .title-highlight {{
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* Adapter styling for inputs */
    .stTextInput>div>div>input {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {control_border} !important;
    }}
    
    .stSelectbox>div>div>div {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {control_border} !important;
    }}

    /* Absolutely force beautiful high-contrast text on all secondary and popover buttons */
    .stApp button[data-testid="stPopoverButton"], 
    .stApp button[data-testid="stBaseButton-secondary"],
    .stApp button[data-testid="stBaseButton-secondaryFormSubmit"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {control_border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }}
    .stApp button[data-testid="stPopoverButton"]:hover, 
    .stApp button[data-testid="stBaseButton-secondary"]:hover,
    .stApp button[data-testid="stBaseButton-secondaryFormSubmit"]:hover {{
        border-color: {card_hover_border} !important;
        background-color: rgba(56, 189, 248, 0.08) !important;
        color: #38BDF8 !important;
    }}
    .stApp button[data-testid="stPopoverButton"] *, 
    .stApp button[data-testid="stBaseButton-secondary"] *,
    .stApp button[data-testid="stBaseButton-secondaryFormSubmit"] * {{
        color: inherit !important;
    }}
    
    /* Hide the default dropdown arrow/chevron icon in the popover button */
    .stApp button[data-testid="stPopoverButton"] svg,
    .stApp button[data-testid="stPopoverButton"] [data-testid="stIcon"],
    .stApp button[data-testid="stPopoverButton"] span[data-testid="stIcon"],
    .stApp button[data-testid="stPopoverButton"] *:not(:first-child) {{
        display: none !important;
    }}

    /* Robust overrides for inputs and select components under different states */
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {control_border} !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {control_border} !important;
    }}
    
    /* High contrast selectbox svg/chevron icon color */
    div[data-baseweb="select"] svg {{
        fill: {text_color} !important;
        color: {text_color} !important;
    }}

    /* Premium Dropdown list popover overrides */
    div[data-baseweb="popover"] ul {{
        background-color: {card_bg} !important;
        border: 1px solid {control_border} !important;
        border-radius: 8px !important;
        padding: 0.25rem !important;
    }}
    div[data-baseweb="popover"] li {{
        color: {text_color} !important;
        background-color: transparent !important;
        transition: all 0.2s ease !important;
        border-radius: 4px !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.9rem !important;
    }}
    div[data-baseweb="popover"] li:hover {{
        background-color: rgba(56, 189, 248, 0.15) !important;
        color: #38BDF8 !important;
    }}
    div[data-baseweb="popover"] li[aria-selected="true"] {{
        background-color: rgba(129, 140, 248, 0.2) !important;
        color: #818CF8 !important;
        font-weight: 600 !important;
    }}

    @media (max-width: 768px) {{
        /* Make block container padding friendly on mobile */
        div[data-testid="stAppViewBlockContainer"],
        div[data-testid="stMainBlockContainer"],
        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}

        /* Change header sticky bar to relative so it flows naturally on mobile and doesn't block the screen */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) {{
            position: relative !important;
            padding-top: 0.5rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            box-shadow: none !important;
            border-bottom: 1px solid {card_border} !important;
        }}

        /* Hide the spacer since the header is relative */
        .sticky-spacer {{
            display: none !important;
            height: 0px !important;
        }}

        /* Let the layout wrap (stack poster wall and details panel vertically) */
        div[data-testid="stHorizontalBlock"]:has(.poster-wall-marker),
        div[data-testid="stHorizontalBlock"]:has(.details-panel-marker) {{
            flex-wrap: wrap !important;
        }}

        /* Make both panes full width on mobile */
        div[data-testid="stColumn"]:has(.poster-wall-marker) {{
            width: 100% !important;
            max-width: 100% !important;
            padding-right: 0 !important;
        }}

        div[data-testid="stColumn"]:has(.details-panel-marker) {{
            position: relative !important;
            top: 0 !important;
            height: auto !important;
            width: 100% !important;
            max-width: 100% !important;
            margin-top: 1rem !important;
        }}

        div[data-testid="stColumn"]:has(.details-panel-marker) > div[data-testid="stVerticalBlock"] {{
            height: auto !important;
            overflow-y: visible !important;
            border-radius: 12px !important;
            border-right: 1px solid {panel_border} !important;
            padding: 1rem !important;
        }}

        /* Flex controls wrapping: logo/title row and buttons row stack */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) > div[data-testid="stHorizontalBlock"]:first-of-type {{
            flex-direction: column !important;
            gap: 0.8rem !important;
        }}
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) > div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"] {{
            min-width: 100% !important;
            width: 100% !important;
            flex: 1 1 100% !important;
        }}

        /* Make filters and sort container wrap fields into columns on mobile */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) div[data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
        }}
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
            min-width: calc(50% - 0.25rem) !important;
            flex: 1 1 calc(50% - 0.25rem) !important;
            margin: 0 !important;
        }}

        /* Keep Search and Reset next to each other, taking 70% and 20% */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child {{
            min-width: 70% !important;
            flex: 1 1 70% !important;
        }}
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {{
            min-width: 20% !important;
            flex: 1 1 20% !important;
        }}

        /* Make slider column take full width (100%) so slider widgets are legible */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(div.sticky-header-marker) div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:has(div.header-label) {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}
        
        /* Ensure logo container doesn't overflow */
        .app-logo {{
            width: 32px !important;
            height: 32px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# Database Helper Functions
def get_db_connection():
    db_path = os.path.join(APP_DIR, 'movies.db')
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    # WAL mode gives much better concurrent read performance and avoids
    # "database locked" errors when multiple Streamlit sessions hit the DB
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    # Auto-initialize database schema if tables don't exist
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(movies)")
    columns = [info[1] for info in cur.fetchall()]
    if columns:
        if 'title_zh' not in columns:
            cur.execute("ALTER TABLE movies ADD COLUMN title_zh TEXT")
            cur.execute("ALTER TABLE movies ADD COLUMN director_zh TEXT")
            cur.execute("ALTER TABLE movies ADD COLUMN actors_zh TEXT")
            cur.execute("ALTER TABLE movies ADD COLUMN plot_zh TEXT")
            conn.commit()
        if 'physical_path_mac' not in columns:
            cur.execute("ALTER TABLE movies ADD COLUMN physical_path_mac TEXT")
            conn.commit()
        
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                original_title TEXT,
                director TEXT,
                actors TEXT,
                genres TEXT,
                year INTEGER,
                runtime INTEGER,
                country TEXT,
                plot TEXT,
                imdb_id TEXT,
                imdb_rating REAL,
                douban_id TEXT,
                douban_rating REAL,
                tmdb_id TEXT,
                physical_path TEXT,
                physical_path_mac TEXT,
                watch_status TEXT DEFAULT 'Unseen',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    return conn

def check_duplicates():
    from collections import defaultdict
    import re
    
    def extract_year_from_path(path):
        if not path:
            return 0
        matches = re.finditer(r'\b(18[89]\d|19\d\d|20[0-2]\d)\b', path)
        valid_years = []
        for match in matches:
            year_str = match.group(1)
            val = int(year_str)
            if val in (1080, 2160, 720, 576, 480):
                continue
            start, end = match.span()
            preceding = path[max(0, start-1):start]
            following = path[end:min(len(path), end+1)]
            if preceding.lower() in ('x', '*', 'p') or following.lower() in ('x', '*', 'p'):
                continue
            if val == 1920:
                context = path[end:min(len(path), end+10)].lower()
                if re.match(r'^[\s\._\-]*x?1080', context):
                    continue
            valid_years.append(val)
        if valid_years:
            return valid_years[-1]
        return 0

    def get_primary_year(m):
        py = extract_year_from_path(m['physical_path']) or extract_year_from_path(m['physical_path_mac']) or 0
        if py > 0:
            return py
        try:
            return int(m['year']) if m['year'] else 0
        except (ValueError, TypeError):
            return 0

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies")
    movies = cur.fetchall()
    conn.close()
    
    by_imdb = defaultdict(list)
    by_douban = defaultdict(list)
    by_tmdb = defaultdict(list)
    by_title_year = defaultdict(list)
    by_path = defaultdict(list)
    
    for row in movies:
        m_id = row['id']
        title = row['title']
        imdb_id = row['imdb_id']
        douban_id = row['douban_id']
        tmdb_id = row['tmdb_id']
        path = row['physical_path']
        
        # Get primary year (prioritize path year)
        p_year = get_primary_year(row)
        
        # Duplicates by IMDb ID
        if imdb_id and str(imdb_id).strip():
            by_imdb[str(imdb_id).strip()].append(row)
            
        # Duplicates by Douban ID
        if douban_id and str(douban_id).strip():
            by_douban[str(douban_id).strip()].append(row)
            
        # Duplicates by TMDb ID
        if tmdb_id and str(tmdb_id).strip():
            by_tmdb[str(tmdb_id).strip()].append(row)
            
        # Duplicates by Title & Year
        if title and str(title).strip():
            norm_title = str(title).strip().lower()
            key = (norm_title, p_year)
            by_title_year[key].append(row)
            
        # Duplicates by Physical Path
        if path and str(path).strip():
            by_path[str(path).strip()].append(row)
            
    def filter_id_duplicates_and_mismatches(d):
        filtered_dups = {}
        filtered_mismatches = {}
        for key, row_list in d.items():
            if len(row_list) > 1:
                partitioned_groups = []
                for m in row_list:
                    y = get_primary_year(m)
                    placed = False
                    for g in partitioned_groups:
                        conflict = False
                        for existing in g:
                            ey = get_primary_year(existing)
                            if y != 0 and ey != 0 and y != ey:
                                conflict = True
                                break
                        if not conflict:
                            g.append(m)
                            placed = True
                            break
                    if not placed:
                        partitioned_groups.append([m])
                
                # Check for year conflicts among non-zero years
                non_zero_years = set()
                for g in partitioned_groups:
                    for m in g:
                        y = get_primary_year(m)
                        if y > 0:
                            non_zero_years.add(y)
                
                if len(non_zero_years) > 1:
                    filtered_mismatches[key] = row_list
                
                # Filter out groups of size 1 for actual duplicates
                valid_groups = [g for g in partitioned_groups if len(g) > 1]
                for idx, group in enumerate(valid_groups):
                    group_key = key if len(valid_groups) == 1 else f"{key} (Group {idx+1})"
                    filtered_dups[group_key] = group
        return filtered_dups, filtered_mismatches

    dup_imdb, mismatch_imdb = filter_id_duplicates_and_mismatches(by_imdb)
    dup_douban, mismatch_douban = filter_id_duplicates_and_mismatches(by_douban)
    dup_tmdb, mismatch_tmdb = filter_id_duplicates_and_mismatches(by_tmdb)
    
    dup_mismatches = {}
    for k, v in mismatch_imdb.items():
        dup_mismatches[f"IMDb: {k}"] = v
    for k, v in mismatch_douban.items():
        dup_mismatches[f"豆瓣: {k}" if st.session_state.lang == 'zh' else f"Douban: {k}"] = v
    for k, v in mismatch_tmdb.items():
        dup_mismatches[f"TMDb: {k}"] = v

    dup_ty = {k: v for k, v in by_title_year.items() if len(v) > 1}
    dup_path = {k: v for k, v in by_path.items() if len(v) > 1}
    
    return dup_imdb, dup_douban, dup_tmdb, dup_ty, dup_path, dup_mismatches

def load_genres():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT genres FROM movies WHERE genres IS NOT NULL AND genres != ''")
    rows = cur.fetchall()
    conn.close()
    
    genres_set = set()
    for row in rows:
        parts = [g.strip() for g in row['genres'].split(',')]
        for p in parts:
            if p:
                genres_set.add(p)
    return sorted(list(genres_set))

def load_countries():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT country FROM movies WHERE country IS NOT NULL AND country != ''")
    rows = cur.fetchall()
    conn.close()
    
    countries_set = set()
    for row in rows:
        import re
        parts = [c.strip() for c in re.split(r'[,/]', row['country']) if c.strip()]
        for p in parts:
            if p:
                countries_set.add(p)
    return sorted(list(countries_set))

def load_languages():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT original_language FROM movies WHERE original_language IS NOT NULL AND original_language != ''")
    rows1 = cur.fetchall()
    cur.execute("SELECT DISTINCT languages FROM movies WHERE languages IS NOT NULL AND languages != ''")
    rows2 = cur.fetchall()
    conn.close()
    
    langs_set = set()
    for rows in [rows1, rows2]:
        for row in rows:
            import re
            val = row[0] if row[0] else ""
            parts = [c.strip() for c in re.split(r'[,/]', val) if c.strip()]
            for p in parts:
                if p:
                    langs_set.add(p)
    return sorted(list(langs_set))

def load_years():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT year FROM movies WHERE year IS NOT NULL AND year != ''")
    rows = cur.fetchall()
    conn.close()
    
    years_list = [str(int(row['year'])) for row in rows]
    return sorted(years_list, key=lambda x: int(x), reverse=True)

def search_movies(query, genre_filter, status_filter, country_filter, year_filter, lang_filter, imdb_filter=None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    sql = "SELECT id, title, original_title, title_zh, year, watch_status, genres, imdb_rating, douban_rating, created_at FROM movies WHERE 1=1"
    params = []
    
    if query:
        # Title-only fuzzy search across all name fields
        sql += " AND (title LIKE ? OR original_title LIKE ? OR title_zh LIKE ?)"
        query_param = f"%{query}%"
        params.extend([query_param, query_param, query_param])
        
    if genre_filter and genre_filter not in ["All", "全部"]:
        # Find equivalents (e.g. if '动作' selected, also search 'Action'; if 'Action' selected, also search '动作')
        equivalents = {genre_filter}
        # Chinese to English lookup
        for en, zh in GENRE_MAP_ZH.items():
            if zh == genre_filter:
                equivalents.add(en)
            elif en == genre_filter:
                equivalents.add(zh)
        
        # Build SQL OR clause for all equivalents
        genre_clauses = []
        for eq in equivalents:
            genre_clauses.append("genres LIKE ?")
            params.append(f"%{eq}%")
        sql += " AND (" + " OR ".join(genre_clauses) + ")"
        
    if status_filter != "All":
        sql += " AND watch_status = ?"
        params.append("Seen" if status_filter == "Seen" else "Unseen")
        
    if country_filter and country_filter not in ["All", "全部"]:
        # Find all equivalents (e.g. if '美国' selected, search 'USA', 'United States', etc.)
        equivalents = {country_filter}
        canonical_zh = get_country_zh(country_filter)
        if canonical_zh:
            equivalents.add(canonical_zh)
            for en, zh in COUNTRY_MAP_ZH.items():
                if zh == canonical_zh:
                    equivalents.add(en)
        
        country_clauses = []
        for eq in equivalents:
            country_clauses.append("country LIKE ?")
            params.append(f"%{eq}%")
        sql += " AND (" + " OR ".join(country_clauses) + ")"
        
    if year_filter and year_filter not in ["All", "全部"]:
        sql += " AND year = ?"
        params.append(int(year_filter))
        
    if lang_filter and lang_filter not in ["All", "全部"]:
        # Find all equivalents (e.g. if '中文' selected, search 'zh', 'cn', 'Chinese', 'Mandarin', etc.)
        equivalents = {lang_filter}
        canonical_zh = get_language_zh(lang_filter)
        if canonical_zh:
            equivalents.add(canonical_zh)
            for en, zh in LANGUAGE_MAP_ZH.items():
                if zh == canonical_zh:
                    equivalents.add(en)
        
        lang_clauses = []
        for eq in equivalents:
            lang_clauses.append("original_language LIKE ?")
            lang_clauses.append("languages LIKE ?")
            params.extend([f"%{eq}%", f"%{eq}%"])
        sql += " AND (" + " OR ".join(lang_clauses) + ")"
        
    if imdb_filter is not None:
        min_val, max_val = imdb_filter
        if min_val > 0.0 or max_val < 10.0:
            sql += " AND imdb_rating >= ? AND imdb_rating <= ?"
            params.extend([min_val, max_val])
            
    sql += " ORDER BY id DESC"
    
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    
    if not query:
        return rows
    
    # Compute relevance score for each result (lower = more relevant)
    q_lower = query.strip().lower()
    scored = []
    for row in rows:
        title_v = (row['title'] or '').lower()
        orig_v = (row['original_title'] or '').lower()
        zh_v = (row['title_zh'] or '').lower()
        all_titles = [title_v, orig_v, zh_v]
        
        best = 99
        for t_val in all_titles:
            if not t_val:
                continue
            if t_val == q_lower:
                best = min(best, 0)   # exact match
            elif t_val.startswith(q_lower):
                best = min(best, 1)   # prefix match
            elif q_lower in t_val:
                # closer to start = better
                pos = t_val.index(q_lower)
                best = min(best, 2 + pos / max(len(t_val), 1))
            else:
                best = min(best, 5)
        scored.append((best, row))
    
    scored.sort(key=lambda x: x[0])
    return [r for _, r in scored]

def get_movie_details(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_movie_fields(movie_id, fields_dict):
    conn = get_db_connection()
    cur = conn.cursor()
    
    set_clause = ", ".join([f"{k} = ?" for k in fields_dict.keys()])
    values = list(fields_dict.values())
    values.append(movie_id)
    
    cur.execute(f"UPDATE movies SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_movie(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()

def insert_new_movie(title):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO movies (title, watch_status) VALUES (?, 'Unseen')", (title,))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id

# Metadata Fetching (TMDB & WMDB APIs)
def search_tmdb_movies(title, api_key):
    if not api_key:
        return []
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {"api_key": api_key, "query": title, "language": "en-US"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 401:
            st.error("❌ TMDB API Key 无效（401），请在设置页面重新填入有效的 Key。")
            return []
        if r.status_code == 200:
            return r.json().get('results', [])
    except Exception as e:
        st.error(f"TMDB search failed: {e}")
    return []

def get_tmdb_movie_details(tmdb_id, api_key, lang=None):
    if not api_key:
        return None
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    req_lang = lang if lang else st.session_state.get('lang', 'zh')
    params = {"api_key": api_key, "language": req_lang, "append_to_response": "credits,external_ids"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"TMDB details fetch failed: {e}")
    return None

def generate_fuzzy_queries(title):
    if not title:
        return []
    queries = []
    
    # 1. Clean the basic title (separators to spaces)
    cleaned = title.replace('_', ' ').replace('.', ' ').strip()
    
    # 2. Try to strip trailing sequential numbers or Roman numerals
    # Matches patterns like " Saga 2", " Part II", " 3", " - 4", etc. at the end
    # Avoid stripping years (4 digits)
    stripped = re.sub(r'\s+[-–—]?\s*(?:[1-9]\d?|I{1,3}|IV|VI{0,3}|IX|X)\s*$', '', cleaned, flags=re.IGNORECASE)
    if stripped != cleaned and len(stripped) > 2:
        queries.append(stripped)
        
    # 3. Try N-words truncation for very long titles
    words = cleaned.split()
    if len(words) >= 5:
        # Try first 4 words
        queries.append(" ".join(words[:4]))
        # Try first 3 words
        queries.append(" ".join(words[:3]))
        
    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for q in queries:
        q_clean = re.sub(r'\s+', ' ', q).strip()
        if q_clean and q_clean.lower() != title.lower() and q_clean not in seen:
            seen.add(q_clean)
            dedup.append(q_clean)
            
    return dedup

def search_imdb_suggestion(title):
    if not title:
        return []
    import urllib.parse
    clean_q = title.lower().strip()
    # Replace separators with underscores for IMDb autocomplete format
    clean_q = re.sub(r'[\s\._\-]+', '_', clean_q)
    # Remove any non-alphanumeric chars except underscores
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

# Base64 Poster Helper
def get_cover_base64(movie_id):
    # 1. Try local cover first
    covers_dir = os.path.join(APP_DIR, 'covers')
    cover_file = os.path.join(covers_dir, f"{movie_id}.jpg")
    if os.path.exists(cover_file) and os.path.getsize(cover_file) > 0:
        try:
            with open(cover_file, "rb") as f:
                return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass
            
    # 2. Fallback to Google Drive CDN URL from mapping file
    json_path = os.path.join(APP_DIR, 'covers_gdrive.json')
    if os.path.exists(json_path):
        try:
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                file_id = mapping.get(str(movie_id))
                if file_id:
                    # Using super-stable public Drive CDN proxy to enable proxy-free loading inside China
                    return f"https://wsrv.nl/?url=https://drive.google.com/thumbnail?id={file_id}%26sz=w500"
        except Exception:
            pass
            
    return None

# Google Drive poster upload helper
def upload_poster_to_gdrive(movie_id, local_cover_path, force_update=False):
    """Upload a newly-downloaded poster to Google Drive and record the file_id
    in covers_gdrive.json.  Runs synchronously but silently on failure."""
    try:
        CREDENTIALS_PATH = '/Users/shanfu/cc/.agents/skills/google-drive-sync/credentials.json'
        TOKEN_PATH = '/Users/shanfu/cc/.agents/skills/google-drive-sync/token.json'
        JSON_MAP_PATH = os.path.join(APP_DIR, 'covers_gdrive.json')

        if not os.path.exists(TOKEN_PATH):
            return  # Not authenticated — skip silently

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            return

        service = build('drive', 'v3', credentials=creds)

        # Find or create the MovieLabelCovers folder
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

        # Check if file already exists remotely
        q = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
        existing = service.files().list(q=q, spaces='drive', fields='files(id)').execute().get('files', [])
        if existing:
            file_id = existing[0]['id']
            if force_update:
                media = MediaFileUpload(local_cover_path, mimetype='image/jpeg', resumable=True)
                service.files().update(
                    fileId=file_id, media_body=media
                ).execute()
        else:
            file_metadata = {'name': filename, 'parents': [folder_id]}
            media = MediaFileUpload(local_cover_path, mimetype='image/jpeg', resumable=True)
            uploaded = service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()
            file_id = uploaded.get('id')
            # Make the file individually public (folder permission is NOT inherited by files)
            service.permissions().create(
                fileId=file_id,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()

        # Update local mapping JSON
        mapping = {}
        if os.path.exists(JSON_MAP_PATH):
            with open(JSON_MAP_PATH, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        mapping[str(movie_id)] = file_id
        with open(JSON_MAP_PATH, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=4, ensure_ascii=False)
    except Exception:
        pass  # Upload failures are non-blocking

# TMDB Key Load/Save Helpers
def load_env_var(var_name, default_value=""):
    env_path = os.path.join(APP_DIR, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith(f"{var_name}="):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
    return default_value

def save_env_vars(vars_dict):
    env_path = os.path.join(APP_DIR, '.env')
    current_vars = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            current_vars[parts[0].strip()] = parts[1].strip()
        except Exception:
            pass
    
    current_vars.update(vars_dict)
    
    try:
        with open(env_path, 'w') as f:
            for k, v in current_vars.items():
                f.write(f"{k}={v}\n")
        return True
    except Exception:
        return False

def load_tmdb_key():
    if 'tmdb_key' in st.session_state and st.session_state['tmdb_key']:
        return st.session_state['tmdb_key']
    if os.environ.get('TMDB_API_KEY'):
        st.session_state['tmdb_key'] = os.environ.get('TMDB_API_KEY')
        return os.environ.get('TMDB_API_KEY')
    key = load_env_var('TMDB_API_KEY', '')
    if key:
        st.session_state['tmdb_key'] = key
    return key

def save_tmdb_key_permanently(key):
    st.session_state['tmdb_key'] = key
    return save_env_vars({'TMDB_API_KEY': key})

def load_path_mappings():
    map_path = os.path.join(APP_DIR, 'path_mappings.json')
    if os.path.exists(map_path):
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    win_p = data.get("win_prefix", "").strip()
                    mac_p = data.get("mac_prefix", "").strip()
                    if win_p or mac_p:
                        win_prefixes = [p.strip() for p in win_p.replace(',', ';').split(';') if p.strip()]
                        rules = []
                        for wp in win_prefixes:
                            rules.append({"win": wp, "mac": mac_p})
                        return rules
        except Exception:
            pass
    return []

def save_path_mappings(rules):
    map_path = os.path.join(APP_DIR, 'path_mappings.json')
    try:
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def to_win_path(mac_path, rules=None):
    if not mac_path:
        return ""
    if rules is None:
        rules = load_path_mappings()
    norm_path = mac_path.replace('\\', '/')
    for r in rules:
        mac_pref = r.get("mac", "").replace('\\', '/').rstrip('/')
        win_pref = r.get("win", "").rstrip('\\/')
        if mac_pref and norm_path.lower().startswith(mac_pref.lower()):
            rel_part = norm_path[len(mac_pref):]
            win_rel = rel_part.replace('/', '\\')
            win_path = win_pref + win_rel
            if not win_path.startswith(win_pref):
                win_path = win_pref + '\\' + win_path.lstrip('\\')
            return win_path
    if norm_path.startswith('/') or ':' not in norm_path:
        return mac_path
    return mac_path.replace('/', '\\')

def to_mac_path(win_path, rules=None):
    if not win_path:
        return ""
    if rules is None:
        rules = load_path_mappings()
    norm_path = win_path.replace('\\', '/')
    for r in rules:
        win_pref = r.get("win", "").replace('\\', '/').rstrip('/')
        mac_pref = r.get("mac", "").rstrip('/')
        if win_pref and norm_path.lower().startswith(win_pref.lower()):
            rel_part = norm_path[len(win_pref):]
            mac_path = mac_pref + rel_part
            return mac_path
    return win_path.replace('\\', '/')

def resolve_case_insensitive_path(path):
    if not path:
        return None
    if os.path.exists(path):
        return path
    norm_path = os.path.normpath(path)
    parts = norm_path.split(os.sep)
    if path.startswith('/'):
        current = '/'
        start_idx = 1
    elif len(parts) > 0 and parts[0].endswith(':'):
        current = parts[0] + os.sep
        start_idx = 1
    else:
        current = '.'
        start_idx = 0
    for part in parts[start_idx:]:
        if not part:
            continue
        try:
            if not os.path.isdir(current):
                return None
            children = os.listdir(current)
            matched_child = None
            part_lower = part.lower()
            for child in children:
                if child.lower() == part_lower:
                    matched_child = child
                    break
            if matched_child is None:
                return None
            current = os.path.join(current, matched_child)
        except Exception:
            return None
    return current

def exists_case_insensitive(path):
    return resolve_case_insensitive_path(path) is not None

def apply_path_mapping(raw_path):
    return to_mac_path(raw_path)

def find_accessible_path(raw_path):
    if not raw_path:
        return ""
    mapped_path = apply_path_mapping(raw_path)
    resolved = resolve_case_insensitive_path(mapped_path)
    if resolved:
        return resolved
    norm_path = raw_path.replace('\\', '/')
    rel_part = ""
    if len(norm_path) >= 2 and norm_path[1] == ':':
        rel_part = norm_path[2:].lstrip('/')
    else:
        if norm_path.startswith('/Volumes/'):
            parts = [p for p in norm_path.split('/') if p]
            if len(parts) >= 3:
                rel_part = '/'.join(parts[2:])
            else:
                rel_part = norm_path.lstrip('/')
        else:
            rel_part = norm_path.lstrip('/')
    if sys.platform == 'darwin':
        if exists_case_insensitive('/Volumes'):
            try:
                for vol in os.listdir('/Volumes'):
                    vol_path = os.path.join('/Volumes', vol)
                    if os.path.isdir(vol_path) and not vol.startswith('.'):
                        cand = os.path.join(vol_path, rel_part)
                        resolved = resolve_case_insensitive_path(cand)
                        if resolved:
                            return resolved
            except Exception:
                pass
    elif sys.platform.startswith('win'):
        import string
        for letter in string.ascii_uppercase:
            cand = f"{letter}:\\{rel_part.replace('/', '\\')}"
            resolved = resolve_case_insensitive_path(cand)
            if resolved:
                return resolved
    return ""



def clean_movie_filename(filename):
    # Strip extension
    base, _ = os.path.splitext(filename)
    
    # Replace separators with spaces
    cleaned = re.sub(r'[\._\-\[\]\(\)]', ' ', base)
    
    # Try to extract year (4-digit number starting with 19 or 20)
    year_match = re.search(r'(?<!\d)(19\d{2}|20[0-3]\d)(?!\d)', cleaned)
    year = None
    if year_match:
        year = int(year_match.group(1))
        year_idx = year_match.start()
        cleaned_title = cleaned[:year_idx]
    else:
        cleaned_title = cleaned
        
    # Remove common video release tags
    tags = [
        r'\b1080p\b', r'\b720p\b', r'\b4k\b', r'\b2160p\b', r'\bbluray\b', r'\bbdrip\b', 
        r'\bweb-dl\b', r'\bwebrip\b', r'\bhdrip\b', r'\bh264\b', r'\bx264\b', r'\bh265\b', 
        r'\bx265\b', r'\bhevc\b', r'\bdts\b', r'\braw\b', r'\bxvid\b', r'\bdivx\b', 
        r'\bremux\b', r'\bchs\b', r'\bcht\b', r'\beng\b', r'\bdual\b', r'\baac\b', r'\bdd5\.1\b'
    ]
    for tag in tags:
        cleaned_title = re.sub(tag, ' ', cleaned_title, flags=re.IGNORECASE)
        
    # Strip extra spaces
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
    
    if not cleaned_title:
        cleaned_title = base
        
    return cleaned_title, year

def extract_metadata_from_path(physical_path):
    if not physical_path:
        return None, None, None
    
    # Take the first path if there are multiple separated by semicolon
    first_path = physical_path.split(';')[0].strip()
    if not first_path:
        return None, None, None
        
    # Normalize backslashes for cross-platform basename extraction
    first_path = first_path.replace('\\', '/')
    filename = os.path.basename(first_path)
    path_title, path_year = clean_movie_filename(filename)
    
    # Language detection keywords
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

def get_best_tmdb_match(title, key, m_dict=None):
    if not key:
        return None
        
    physical_path = m_dict.get('physical_path') if m_dict else None
    db_year = m_dict.get('year') if m_dict else None
    
    path_title, path_year, detected_lang = extract_metadata_from_path(physical_path)
    
    # 1. Determine target search year
    target_year = path_year or db_year
    
    # 2. Search TMDB
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
            
    # If no results with year, or no target year, search without year filter
    if not search_results:
        search_results = search_tmdb_movies(title, key)
        
    if not search_results:
        return None
        
    # 3. Score and rank candidates
    scored_candidates = []
    for r in search_results:
        score = 0
        r_title = r.get('title', '')
        r_orig_title = r.get('original_title', '')
        r_lang = r.get('original_language', '')
        
        rd = r.get('release_date', '')
        r_year = int(rd.split('-')[0]) if rd else None
        
        # A. Title similarity scoring
        title_lower = title.lower().strip()
        r_title_lower = r_title.lower().strip()
        r_orig_title_lower = r_orig_title.lower().strip()
        
        if title_lower == r_title_lower or title_lower == r_orig_title_lower:
            score += 100
        elif title_lower in r_title_lower or title_lower in r_orig_title_lower or r_title_lower in title_lower or r_orig_title_lower in title_lower:
            score += 40
            
        # B. Year proximity scoring
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
                    score -= 30
            except ValueError:
                pass
                
        # C. Language matching scoring
        if detected_lang:
            if r_lang == detected_lang:
                score += 150
            elif detected_lang != 'en' and r_lang == 'en':
                score -= 80
            elif detected_lang == 'en' and r_lang == 'en':
                score += 20
                
        # D. Popularity / Vote count tie-breaker
        pop = r.get('popularity', 0)
        score += min(pop / 5.0, 15.0)
        votes = r.get('vote_count', 0)
        score += min(votes / 100.0, 10.0)
        
        scored_candidates.append((score, r))
        
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    return scored_candidates[0][1]

def get_normalization_key(t_str):
    if not t_str:
        return ""
    # Lowercase, keep only letters, numbers and Chinese characters
    t_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', t_str.lower())
    return t_clean

def split_chinese_english(title):
    if not title:
        return "", ""
        
    import unicodedata
    title = unicodedata.normalize('NFC', title)
        
    # Tags to strip (case-insensitive)
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
    
    # Pre-clean tags and brackets helper
    def clean_segment(text):
        if not text:
            return ""
        curr = text
        for tag in eng_tags:
            curr = re.sub(tag, ' ', curr, flags=re.IGNORECASE)
        for tag in zh_tags:
            curr = re.sub(tag, ' ', curr, flags=re.IGNORECASE)
        # Strip years
        curr = re.sub(r'\b(?:19|20)\d{2}\b', ' ', curr)
        return curr

    cleaned = title
    
    # Split Chinese and English/other languages using brackets and characters.
    # Extract anything inside bracket markers: 【 】, [ ], ( ), （ ）
    bracket_contents = re.findall(r'[\[\(【（]([^\]\)】）]+)[\]\)】）]', cleaned)
    
    zh_parts = []
    en_parts = []
    
    # Process contents inside brackets
    cleaned_no_brackets = cleaned
    for content in bracket_contents:
        cleaned_content = clean_segment(content).strip()
        if not cleaned_content:
            # Remove empty bracketed parts
            try:
                cleaned_no_brackets = re.sub(r'[\[\(【（]' + re.escape(content) + r'[\]\)】）]', ' ', cleaned_no_brackets)
            except Exception:
                pass
            continue
            
        # Check if bracket content contains Chinese
        if re.search(r'[\u4e00-\u9fff]', cleaned_content):
            zh_parts.append(cleaned_content)
        else:
            en_parts.append(cleaned_content)
            
        # Remove the bracketed part from the main string to avoid duplication
        try:
            cleaned_no_brackets = re.sub(r'[\[\(【（]' + re.escape(content) + r'[\]\)】）]', ' ', cleaned_no_brackets)
        except Exception:
            pass
            
    # Clean the remaining part outside brackets
    cleaned_no_brackets = clean_segment(cleaned_no_brackets)
    # Replace common separators with spaces
    cleaned_no_brackets = re.sub(r'[\._\-\[\]\(\)]', ' ', cleaned_no_brackets)
    # Clean again in case separators blocked boundaries
    cleaned_no_brackets = clean_segment(cleaned_no_brackets)
        
    # Now split the remaining string outside brackets
    # Any continuous block of Chinese characters plus trailing/leading digits or simple symbols
    main_zh_matches = re.findall(r'[\u4e00-\u9fff\d：:，,！!]+', cleaned_no_brackets)
    for part in main_zh_matches:
        # It must contain at least one Chinese character to be a Chinese title part
        if re.search(r'[\u4e00-\u9fff]', part):
            zh_parts.append(part)
            # Remove it from the main string
            cleaned_no_brackets = cleaned_no_brackets.replace(part, ' ')
            
    # The remaining part is the English/Latin title
    en_parts.append(cleaned_no_brackets)
    
    # Clean up and join
    def clean_title_str(t_str):
        # Remove punctuation except letters, digits, spaces, and simple colons/dashes
        t_clean = t_str.replace('_', ' ')
        t_clean = re.sub(r'[^\w\s\-\:\uff1a]', ' ', t_clean)
        # Strip tags again just in case
        t_clean = clean_segment(t_clean)
        # Collapse multiple spaces
        t_clean = re.sub(r'\s+', ' ', t_clean).strip()
        return t_clean
        
    zh_title = clean_title_str(" ".join(zh_parts))
    en_title = clean_title_str(" ".join(en_parts))
    
    return zh_title, en_title

def classify_ignore_candidate(title, physical_path=""):
    t_lower = str(title or "").lower()
    p_lower = str(physical_path or "").lower()
    
    # 1. Mock Data
    if "mock movie" in t_lower or "test movie" in t_lower:
        return True, "Mock Data"
        
    # 2. TV Show Episodes
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
            
    # 3. YouTube/Web Videos
    web_keywords = ["mafia ep", "mafia episode", "round 2", "ice nation", "walk the line", "youtube", "bilibili"]
    for kw in web_keywords:
        if kw in t_lower or kw in p_lower:
            return True, "Web/YouTube Video"
            
    yt_id_pattern = r'\[[a-zA-Z0-9_-]{11}\]'
    if re.search(yt_id_pattern, t_lower) or re.search(yt_id_pattern, p_lower):
        return True, "Web/YouTube Video"
        
    return False, ""

def search_duckduckgo_fallback(query):
    """Scrapes DuckDuckGo HTML search results for basic metadata fallback.
    Returns: (plot/description, guessed_year)"""
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
                
            # Combine first two snippets for description
            desc = " | ".join(cleaned_snippets[:2])
            
            # Try to extract a year from the snippets
            year_match = re.search(r'(?<!\d)(19\d{2}|20[0-3]\d)(?!\d)', desc)
            guessed_year = int(year_match.group(1)) if year_match else None
            
            return desc, guessed_year
    except Exception:
        pass
    return None, None

def autocomplete_movie_metadata_if_needed(m_id, db_movie, force=False):
    m_dict = dict(db_movie)
    covers_dir_local = os.path.join(APP_DIR, 'covers')
    local_cover = os.path.join(covers_dir_local, f"{m_id}.jpg")
    has_cover = os.path.exists(local_cover) and os.path.getsize(local_cover) > 0

    # Basic fields check
    missing_basic = (
        not m_dict.get("original_title")
        or not has_cover
        or not m_dict.get("year")
        or not m_dict.get("genres")
        or not m_dict.get("imdb_rating") or float(m_dict.get("imdb_rating") or 0.0) == 0.0
        or not m_dict.get("runtime")
        or not m_dict.get("country")
    )
    # Supplementary fields check
    missing_extra = (
        not m_dict.get("imdb_id")
        or not m_dict.get("plot")
        or not m_dict.get("plot_zh")
    )
    
    if not force and not (missing_basic or missing_extra):
        return False

    key = load_tmdb_key()
    if not key:
        return False
        
    title_to_search = m_dict.get("title") or m_dict.get("original_title") or m_dict.get("title_zh")
    if not title_to_search:
        return False
        
    try:
        zh_t, en_t = split_chinese_english(title_to_search)
        search_queries = [title_to_search]
        
        # Add aka splits
        if " aka " in title_to_search.lower():
            for part in re.split(r'\s+aka\s+', title_to_search, flags=re.IGNORECASE):
                search_queries.append(part.strip())
                
        if zh_t and zh_t != title_to_search:
            search_queries.append(zh_t)
            if " aka " in zh_t.lower():
                for part in re.split(r'\s+aka\s+', zh_t, flags=re.IGNORECASE):
                    search_queries.append(part.strip())
        if en_t and en_t != title_to_search:
            search_queries.append(en_t)
            if " aka " in en_t.lower():
                for part in re.split(r'\s+aka\s+', en_t, flags=re.IGNORECASE):
                    search_queries.append(part.strip())
                    
        best = None
        for query in search_queries:
            best = get_best_tmdb_match(query, key, m_dict)
            if best:
                break
                
        # Try fuzzy queries if still not found
        if not best:
            fuzzy_queries = []
            for q in search_queries:
                fuzzy_queries.extend(generate_fuzzy_queries(q))
            fuzzy_queries = list(dict.fromkeys(fuzzy_queries))
            for q in fuzzy_queries:
                best = get_best_tmdb_match(q, key, m_dict)
                if best:
                    break
                    
        # Try IMDb suggestion search if still not found
        imdb_candidates = []
        if not best:
            imdb_candidates = search_imdb_suggestion(title_to_search)
            if not imdb_candidates:
                for q in search_queries:
                    imdb_candidates = search_imdb_suggestion(q)
                    if imdb_candidates:
                        break
            if imdb_candidates:
                for cand in imdb_candidates:
                    tmdb_movie = find_tmdb_movie_by_imdb_id(cand['id'], key)
                    if tmdb_movie:
                        best = tmdb_movie
                        break

        if best:
            tmdb_id = best['id']
            details_en = get_tmdb_movie_details(tmdb_id, key, lang='en-US')
            details_zh = get_tmdb_movie_details(tmdb_id, key, lang='zh-CN')
            
            details = details_en if details_en else details_zh
            if not details:
                return False

            tmdb_id_str = str(details.get('id', ''))
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
            if country:
                country = re.sub(r'(?<!中国)台湾', '中国台湾', country)
                country = re.sub(r'(?<!China )Taiwan', 'China Taiwan Province', country)

            external_ids = details.get('external_ids', {})
            imdb_id = external_ids.get('imdb_id')

            wmdb_data = fetch_wmdb_ratings(imdb_id if imdb_id else title_to_search)
            douban_id = None
            douban_rating = None
            imdb_rating = details.get('vote_average')

            if wmdb_data:
                douban_id = wmdb_data.get('doubanId')
                douban_rating = wmdb_data.get('doubanRating')
                if wmdb_data.get('imdbRating'):
                    imdb_rating = wmdb_data.get('imdbRating')

            # Poster download & upload
            poster_path = (details_zh or {}).get('poster_path') or (details_en or {}).get('poster_path') or details.get('poster_path')
            local_cover = os.path.join(covers_dir_local, f"{m_id}.jpg")
            if poster_path:
                poster_downloaded = False
                if force or not (os.path.exists(local_cover) and os.path.getsize(local_cover) > 0):
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    try:
                        import requests
                        img_r = requests.get(poster_url, timeout=10)
                        if img_r.status_code == 200:
                            with open(local_cover, 'wb') as img_f:
                                img_f.write(img_r.content)
                            poster_downloaded = True
                    except Exception:
                        pass
                
                # Always ensure it is uploaded to GDrive if the local cover exists
                if os.path.exists(local_cover) and os.path.getsize(local_cover) > 0:
                    upload_poster_to_gdrive(m_id, local_cover, force_update=poster_downloaded)

            # Helper to update fields if missing
            def use_new_if_empty(k, new_val):
                val = m_dict.get(k)
                if force:
                    return new_val if new_val else val
                return val if val else new_val

            update_movie_fields(m_id, {
                'original_title': use_new_if_empty('original_title', original_title),
                'director': use_new_if_empty('director', director),
                'actors': use_new_if_empty('actors', actors),
                'genres': use_new_if_empty('genres', genres),
                'year': use_new_if_empty('year', year),
                'runtime': use_new_if_empty('runtime', runtime),
                'country': use_new_if_empty('country', country),
                'plot': use_new_if_empty('plot', plot),
                'title_zh': use_new_if_empty('title_zh', title_zh),
                'director_zh': use_new_if_empty('director_zh', director_zh),
                'actors_zh': use_new_if_empty('actors_zh', actors_zh),
                'plot_zh': use_new_if_empty('plot_zh', plot_zh),
                'imdb_id': use_new_if_empty('imdb_id', imdb_id),
                'tmdb_id': use_new_if_empty('tmdb_id', tmdb_id_str),
                'douban_id': use_new_if_empty('douban_id', douban_id),
                'imdb_rating': use_new_if_empty('imdb_rating', imdb_rating),
                'douban_rating': use_new_if_empty('douban_rating', douban_rating)
            })
            return True
            
        elif imdb_candidates:
            cand = imdb_candidates[0]
            imdb_id = cand['id']
            original_title = cand['title']
            year = cand['year']
            actors = cand['actors']
            cover_url = cand['cover_url']
            
            def use_new_if_empty(k, new_val):
                val = m_dict.get(k)
                if force:
                    return new_val if new_val else val
                return val if val else new_val
                
            update_movie_fields(m_id, {
                'original_title': use_new_if_empty('original_title', original_title),
                'year': use_new_if_empty('year', year),
                'actors': use_new_if_empty('actors', actors),
                'imdb_id': use_new_if_empty('imdb_id', imdb_id),
            })
            
            local_cover = os.path.join(covers_dir_local, f"{m_id}.jpg")
            poster_downloaded = False
            if cover_url:
                if force or not (os.path.exists(local_cover) and os.path.getsize(local_cover) > 0):
                    try:
                        img_r = requests.get(cover_url, timeout=10)
                        if img_r.status_code == 200:
                            with open(local_cover, 'wb') as img_f:
                                img_f.write(img_r.content)
                            poster_downloaded = True
                    except Exception:
                        pass
            if os.path.exists(local_cover) and os.path.getsize(local_cover) > 0:
                upload_poster_to_gdrive(m_id, local_cover, force_update=poster_downloaded)
            return True
    except Exception:
        pass
    return False

def suggest_mapping_rule(db_path, local_path):
    if not db_path or not local_path:
        return None, None
    dp = db_path.replace('\\', '/').strip()
    lp = local_path.replace('\\', '/').strip()
    
    dp_parts = dp.split('/')
    lp_parts = lp.split('/')
    
    match_count = 0
    for i in range(1, min(len(dp_parts), len(lp_parts)) + 1):
        if dp_parts[-i].lower() == lp_parts[-i].lower():
            match_count = i
        else:
            break
            
    if match_count > 0:
        db_pref_parts = dp_parts[:-match_count]
        lp_pref_parts = lp_parts[:-match_count]
        
        if '\\' in db_path or (':' in db_path and '/' not in db_path):
            db_pref = '\\'.join(db_pref_parts)
            if db_pref and not db_pref.endswith('\\'):
                db_pref += '\\'
        else:
            db_pref = '/'.join(db_pref_parts)
            if db_pref and not db_pref.endswith('/'):
                db_pref += '/'
                
        lp_pref = '/'.join(lp_pref_parts)
        if lp_pref and not lp_pref.endswith('/'):
            lp_pref += '/'
            
        if db_pref and lp_pref:
            return db_pref, lp_pref
    return None, None

def scan_local_directory(dir_path, scan_subdirs, add_new, link_existing):
    logs = []
    stats = {"total_files": 0, "added": 0, "linked": 0, "skipped": 0, "errors": 0}
    
    if not os.path.isdir(dir_path):
        return [t("scan_err_dir_not_found", path=dir_path)], stats
        
    video_exts = ('.mp4', '.mkv', '.avi', '.mov', '.rmvb', '.wmv', '.flv', '.m4v')
    scanned_files = []
    
    try:
        if scan_subdirs:
            for root, dirs, files in os.walk(dir_path):
                for f in files:
                    if f.startswith('.'):
                        continue
                    if f.lower().endswith(video_exts):
                        scanned_files.append(os.path.join(root, f))
        else:
            for f in os.listdir(dir_path):
                if f.startswith('.'):
                    continue
                if f.lower().endswith(video_exts) and os.path.isfile(os.path.join(dir_path, f)):
                    scanned_files.append(os.path.join(dir_path, f))
    except Exception as e:
        return [t("scan_err_read_failed", err=e)], stats
 
    stats["total_files"] = len(scanned_files)
    if not scanned_files:
        return [t("scan_info_no_videos")], stats
 
    # Initialize Streamlit session state pending approvals list
    try:
        if "pending_scan_approvals" not in st.session_state:
            st.session_state.pending_scan_approvals = []
        st.session_state.pending_scan_approvals = []
    except Exception:
        pass
 
    # Load all existing movies to match in memory (high performance)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, original_title, title_zh, physical_path, physical_path_mac, year FROM movies")
    movies_db_list = [dict(r) for r in cur.fetchall()]
    
    # Build lookup dictionaries
    lookup_map = {}
    path_filename_map = {}
    for m in movies_db_list:
        keys = set()
        for field in ["title", "original_title", "title_zh"]:
            val = m.get(field)
            if val:
                norm_k = get_normalization_key(val)
                if norm_k:
                    keys.add(norm_k)
        for k in keys:
            if k not in lookup_map:
                lookup_map[k] = []
            lookup_map[k].append(m)
            
        # Check both physical_path and physical_path_mac for path_filename_map
        paths_to_add = []
        if m.get("physical_path"):
            paths_to_add.extend(m["physical_path"].split(';'))
        if m.get("physical_path_mac"):
            paths_to_add.extend(m["physical_path_mac"].split(';'))
            
        for path in paths_to_add:
            p_str = path.strip()
            if p_str:
                fname = os.path.basename(p_str.replace('\\', '/')).lower()
                if fname:
                    if fname not in path_filename_map:
                        path_filename_map[fname] = []
                    if m not in path_filename_map[fname]:
                        path_filename_map[fname].append(m)
            
    # Track paths that are already linked in the DB to avoid duplicates
    rules = load_path_mappings()
    existing_paths = set()
    for m in movies_db_list:
        paths_to_track = []
        if m.get("physical_path"):
            paths_to_track.extend(m["physical_path"].split(';'))
        if m.get("physical_path_mac"):
            paths_to_track.extend(m["physical_path_mac"].split(';'))
            
        for path in paths_to_track:
            p_str = path.strip()
            if p_str:
                existing_paths.add(p_str.lower())
                try:
                    mac_p = os.path.abspath(to_mac_path(p_str, rules)).lower()
                    existing_paths.add(mac_p)
                except Exception:
                    pass
                try:
                    win_p = to_win_path(p_str, rules).lower()
                    existing_paths.add(win_p)
                except Exception:
                    pass
 
    # Start processing files
    for filepath in scanned_files:
        abs_path = os.path.abspath(filepath)
        filename = os.path.basename(filepath)
        
        # Translate local macOS path to database Windows format
        db_format_path = to_win_path(abs_path, rules)
        
        # Check if this exact file is already linked and accessible
        is_already_linked = False
        if abs_path.lower() in existing_paths:
            is_already_linked = True
        elif db_format_path.lower() in existing_paths:
            is_already_linked = True

        if is_already_linked:
            stats["skipped"] += 1
            continue
            
        guessed_title, guessed_year = clean_movie_filename(filename)
        zh_guess, en_guess = split_chinese_english(guessed_title)
        
        norm_zh = get_normalization_key(zh_guess)
        norm_en = get_normalization_key(en_guess)
        norm_guess = get_normalization_key(guessed_title)
        
        matched_movie = None
        matches = []
        
        # 1. First prioritize exact physical path filename match
        filename_lower = filename.lower()
        if filename_lower in path_filename_map:
            candidates = path_filename_map[filename_lower]
            if len(candidates) == 1:
                matched_movie = candidates[0]
            else:
                best_match = None
                for cand in candidates:
                    db_year = cand.get("year")
                    try:
                        db_year_int = int(db_year) if db_year is not None else None
                    except (ValueError, TypeError):
                        db_year_int = None
                    if db_year_int and guessed_year and db_year_int == guessed_year:
                        best_match = cand
                        break
                if not best_match:
                    for cand in candidates:
                        cand_keys = set()
                        for field in ["title", "original_title", "title_zh"]:
                            val = cand.get(field)
                            if val:
                                norm_k = get_normalization_key(val)
                                if norm_k:
                                    cand_keys.add(norm_k)
                        if (norm_zh and norm_zh in cand_keys) or (norm_en and norm_en in cand_keys):
                            best_match = cand
                            break
                matched_movie = best_match if best_match else candidates[0]
                
        # 2. Fall back to title/year based matching if no filename match
        if not matched_movie:
            # Exact match on Chinese name part
            if norm_zh and norm_zh in lookup_map:
                matches.extend(lookup_map[norm_zh])
                
            # Exact match on English name part
            if norm_en and norm_en in lookup_map:
                matches.extend(lookup_map[norm_en])
                
            # Typo-tolerant edit distance match on English name part if no exact match found
            if not matches and norm_en:
                for k, movies in lookup_map.items():
                    if re.search(r'[\u4e00-\u9fff]', k):
                        continue
                    if len(k) >= 3 and len(norm_en) >= 3:
                        diff_len = abs(len(k) - len(norm_en))
                        if diff_len <= 2:
                            m_dist = 0
                            for char1, char2 in zip(k, norm_en):
                                if char1 != char2:
                                    m_dist += 1
                            m_dist += diff_len
                            if m_dist <= 2:
                                matches.extend(movies)
                                break
                                
            if matches:
                # Rank matches by year proximity
                def get_match_score(m):
                    db_year = m.get("year")
                    try:
                        db_year_int = int(db_year) if db_year is not None else None
                    except (ValueError, TypeError):
                        db_year_int = None
                    
                    if guessed_year and db_year_int:
                        diff = abs(db_year_int - guessed_year)
                        if diff == 0:
                            return 0  # Best
                        elif diff <= 2:
                            return 1  # Very close
                        else:
                            return 3  # Far
                    else:
                        return 2  # One of them has no year
                
                matches.sort(key=get_match_score)
                valid_matches = []
                for m in matches:
                    score = get_match_score(m)
                    if score <= 2 or len(matches) == 1:
                        valid_matches.append(m)
                
                if valid_matches:
                    matched_movie = valid_matches[0]
 
        if matched_movie:
            db_win = matched_movie.get("physical_path") or ""
            db_mac = matched_movie.get("physical_path_mac") or ""
            
            scanned_win = to_win_path(abs_path, rules)
            scanned_mac = to_mac_path(abs_path, rules)
            
            if not db_win and not db_mac:
                # Scenario A: Exists in DB with no path -> auto link it!
                if link_existing:
                    cur.execute("""
                        UPDATE movies 
                        SET physical_path = ?, physical_path_mac = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (scanned_win, scanned_mac, matched_movie["id"]))
                    stats["linked"] += 1
                    logs.append(t("scan_log_linked", title=matched_movie['title'], filename=filename))
                else:
                    stats["skipped"] += 1
            else:
                # Scenario B: Check if they are part of a multi-part media set (e.g. CD1 and CD2)
                is_multi_part = False
                f_lower = filename.lower()
                
                # Check if new file has a part marker
                has_part_marker = False
                for pattern in [r'cd\s*\d', r'part\s*\d', r'dvd\s*\d', r'disc\s*\d', r'pt\s*\d']:
                    if re.search(pattern, f_lower):
                        has_part_marker = True
                        break
                        
                if has_part_marker:
                    # Check if any of the old paths also has a part marker
                    old_paths = [p.strip() for p in (db_win or db_mac).split(';') if p.strip()]
                    for p in old_paths:
                        p_lower = os.path.basename(p).lower()
                        for pattern in [r'cd\s*\d', r'part\s*\d', r'dvd\s*\d', r'disc\s*\d', r'pt\s*\d']:
                            if re.search(pattern, p_lower):
                                is_multi_part = True
                                break
                        if is_multi_part:
                            break
                            
                if is_multi_part:
                    if link_existing:
                        # Append to the existing path lists
                        new_win = db_win
                        new_mac = db_mac
                        
                        db_win_paths = [p.strip().lower() for p in db_win.split(';') if p.strip()]
                        if scanned_win.lower() not in db_win_paths:
                            new_win = (db_win + "; " + scanned_win) if db_win else scanned_win
                            
                        db_mac_paths = [p.strip().lower() for p in db_mac.split(';') if p.strip()]
                        if scanned_mac.lower() not in db_mac_paths:
                            new_mac = (db_mac + "; " + scanned_mac) if db_mac else scanned_mac
                            
                        cur.execute("""
                            UPDATE movies 
                            SET physical_path = ?, physical_path_mac = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (new_win, new_mac, matched_movie["id"]))
                        stats["linked"] += 1
                        logs.append(t("scan_log_autolinked_multi", title=matched_movie['title'], filename=filename))
                    else:
                        stats["skipped"] += 1
                else:
                    # Check if the scanned path matches current OS path in DB
                    is_diff = False
                    is_curr_mac = sys.platform == 'darwin'
                    is_curr_win = sys.platform.startswith('win')
                    
                    if is_curr_mac:
                        if db_mac:
                            db_mac_paths = [p.strip().lower() for p in db_mac.split(';') if p.strip()]
                            if scanned_mac.lower() not in db_mac_paths:
                                is_diff = True
                        else:
                            if db_win:
                                db_win_mapped_mac = to_mac_path(db_win, rules)
                                if db_win_mapped_mac.lower() != scanned_mac.lower():
                                    is_diff = True
                            else:
                                is_diff = True
                    else:
                        if db_win:
                            db_win_paths = [p.strip().lower() for p in db_win.split(';') if p.strip()]
                            if scanned_win.lower() not in db_win_paths:
                                is_diff = True
                        else:
                            if db_mac:
                                db_mac_mapped_win = to_win_path(db_mac, rules)
                                if db_mac_mapped_win.lower() != scanned_win.lower():
                                    is_diff = True
                            else:
                                is_diff = True
                                
                    if is_diff:
                        # Determine scenario
                        scenario = None
                        if db_win and not db_mac and is_curr_win:
                            scenario = "i"
                        elif db_win and not db_mac and is_curr_mac:
                            scenario = "ii"
                        elif db_mac and not db_win and is_curr_win:
                            scenario = "iii"
                        elif db_win and db_mac:
                            scenario = "iv"
                        else:
                            scenario = "i" if is_curr_win else "iv"
                            
                        # Check if old file exists for help label
                        old_file_exists = False
                        if is_curr_mac and db_mac:
                            old_file_exists = any(os.path.exists(p.strip()) for p in db_mac.split(';') if p.strip())
                        elif is_curr_mac and db_win:
                            old_file_exists = any(os.path.exists(to_mac_path(p.strip(), rules)) for p in db_win.split(';') if p.strip())
                        elif is_curr_win and db_win:
                            old_file_exists = any(os.path.exists(p.strip()) for p in db_win.split(';') if p.strip())
                        elif is_curr_win and db_mac:
                            old_file_exists = any(os.path.exists(to_win_path(p.strip(), rules)) for p in db_mac.split(';') if p.strip())
                            
                        try:
                            st.session_state.pending_scan_approvals.append({
                                "filepath": abs_path,
                                "db_format_path": db_format_path,
                                "filename": filename,
                                "guessed_title": guessed_title,
                                "guessed_year": guessed_year,
                                "guessed_zh_title": zh_guess,
                                "guessed_en_title": en_guess,
                                "db_movie": matched_movie,
                                "old_file_exists": old_file_exists,
                                "scenario": scenario,
                                "scanned_win": scanned_win,
                                "scanned_mac": scanned_mac
                            })
                        except Exception:
                            pass
                        stats["skipped"] += 1
                    else:
                        stats["skipped"] += 1
        else:
            if add_new:
                try:
                    scanned_win = to_win_path(abs_path, rules)
                    scanned_mac = to_mac_path(abs_path, rules)
                    cur.execute("""
                        INSERT INTO movies (title, year, physical_path, physical_path_mac, watch_status)
                        VALUES (?, ?, ?, ?, 'Unseen')
                    """, (guessed_title, guessed_year, scanned_win, scanned_mac))
                    new_id = cur.lastrowid
                    stats["added"] += 1
                    logs.append(t("scan_log_added_new", title=guessed_title, year=(guessed_year or t("unknown_year")), filename=filename))
                    
                    new_movie_dict = {
                        "id": new_id,
                        "title": guessed_title,
                        "original_title": "",
                        "title_zh": "",
                        "physical_path": scanned_win,
                        "physical_path_mac": scanned_mac,
                        "year": guessed_year
                    }
                    if norm_guess:
                        if norm_guess not in lookup_map:
                            lookup_map[norm_guess] = []
                        lookup_map[norm_guess].append(new_movie_dict)
                        
                    # Auto-complete metadata from TMDB/IMDb/Douban synchronously
                    autocomplete_movie_metadata_if_needed(new_id, new_movie_dict)
                except Exception as e:
                    stats["errors"] += 1
                    logs.append(t("scan_log_insert_failed", title=guessed_title, err=e))
            else:
                stats["skipped"] += 1
 
    conn.commit()
    conn.close()
    return logs, stats

def import_metadata_file(uploaded_file, import_mode):
    import pandas as pd
    logs = []
    stats = {"total_rows": 0, "added": 0, "updated": 0, "skipped": 0, "errors": 0}
    
    try:
        filename = uploaded_file.name.lower()
        if filename.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            return [t("import_err_unsupported")], stats
    except Exception as e:
        return [t("import_err_read_failed", err=e)], stats

    stats["total_rows"] = len(df)
    if df.empty:
        return [t("import_info_empty")], stats
        
    col_mapping = {}
    known_columns = [
        "title", "original_title", "director", "actors", "genres", "year", "runtime", 
        "country", "plot", "imdb_id", "imdb_rating", "douban_id", "douban_rating", 
        "tmdb_id", "physical_path", "watch_status"
    ]
    zh_mapping = {
        "标题": "title", "电影标题": "title", "中文名": "title_zh", "原名": "original_title",
        "原版名称": "original_title", "别名": "original_title", "导演": "director", 
        "演员": "actors", "主演": "actors", "类型": "genres", "年份": "year", 
        "出品年份": "year", "片长": "runtime", "时长": "runtime", "国家": "country", 
        "地区": "country", "制片国家": "country", "剧情": "plot", "简介": "plot", 
        "梗概": "plot", "imdb": "imdb_id", "imdb评分": "imdb_rating", "豆瓣": "douban_id", 
        "豆瓣评分": "douban_rating", "tmdb": "tmdb_id", "路径": "physical_path", 
        "物理路径": "physical_path", "状态": "watch_status", "观看状态": "watch_status"
    }
    
    for col in df.columns:
        col_clean = str(col).strip().lower()
        if col_clean in known_columns:
            col_mapping[col] = col_clean
        elif col in zh_mapping:
            col_mapping[col] = zh_mapping[col]
        else:
            for k in known_columns:
                if k in col_clean:
                    col_mapping[col] = k
                    break
            
    title_col = None
    for k, v in col_mapping.items():
        if v == 'title':
            title_col = k
            break
            
    if not title_col:
        return [t("import_err_no_title_col")], stats

    conn = get_db_connection()
    cur = conn.cursor()
    
    for index, row in df.iterrows():
        raw_title = row.get(title_col)
        if pd.isna(raw_title) or not str(raw_title).strip():
            stats["skipped"] += 1
            continue
            
        title = str(raw_title).strip()
        
        row_data = {}
        for col_name, db_col in col_mapping.items():
            val = row.get(col_name)
            if not pd.isna(val):
                if db_col in ['year', 'runtime']:
                    try:
                        row_data[db_col] = int(float(val))
                    except (ValueError, TypeError):
                        row_data[db_col] = None
                elif db_col in ['imdb_rating', 'douban_rating']:
                    try:
                        row_data[db_col] = float(val)
                    except (ValueError, TypeError):
                        row_data[db_col] = None
                else:
                    row_data[db_col] = str(val).strip()
            else:
                row_data[db_col] = None

        matched_id = None
        for id_col in ['tmdb_id', 'imdb_id', 'douban_id']:
            if row_data.get(id_col):
                cur.execute(f"SELECT id FROM movies WHERE {id_col} = ?", (row_data[id_col],))
                res = cur.fetchone()
                if res:
                    matched_id = res[0]
                    break
                    
        if not matched_id:
            norm_title = get_normalization_key(title)
            cur.execute("SELECT id, title, title_zh FROM movies")
            all_m = cur.fetchall()
            for m in all_m:
                if get_normalization_key(m["title"]) == norm_title or (m["title_zh"] and get_normalization_key(m["title_zh"]) == norm_title):
                    matched_id = m["id"]
                    break

        if matched_id:
            if import_mode == "Skip":
                stats["skipped"] += 1
                continue
                
            cur.execute("SELECT * FROM movies WHERE id = ?", (matched_id,))
            existing_movie = dict(cur.fetchone())
            
            update_dict = {}
            for k, new_v in row_data.items():
                if k == 'id':
                    continue
                old_v = existing_movie.get(k)
                
                if import_mode == "Overwrite":
                    if new_v is not None and str(new_v).strip() != "":
                        update_dict[k] = new_v
                elif import_mode == "Fill Empty":
                    if (old_v is None or str(old_v).strip() == "") and new_v is not None and str(new_v).strip() != "":
                        update_dict[k] = new_v

            if update_dict:
                set_clause = ", ".join(f"{k} = ?" for k in update_dict.keys())
                params = list(update_dict.values()) + [matched_id]
                try:
                    cur.execute(f"UPDATE movies SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)
                    stats["updated"] += 1
                    logs.append(t("import_log_updated", title=title, id=matched_id))
                except Exception as e:
                    stats["errors"] += 1
                    logs.append(t("import_log_update_failed", title=title, err=e))
            else:
                stats["skipped"] += 1
        else:
            row_data.pop('id', None)
            row_data['title'] = title
            
            if 'watch_status' not in row_data or not row_data['watch_status']:
                row_data['watch_status'] = 'Unseen'
                
            cols = ", ".join(row_data.keys())
            placeholders = ", ".join("?" for _ in row_data)
            params = list(row_data.values())
            
            try:
                cur.execute(f"INSERT INTO movies ({cols}) VALUES ({placeholders})", params)
                stats["added"] += 1
                logs.append(t("import_log_imported_new", title=title))
            except Exception as e:
                stats["errors"] += 1
                logs.append(t("import_log_import_failed", title=title, err=e))

    conn.commit()
    conn.close()
    return logs, stats


# Compute Statistics for Header
try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM movies")
    total_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM movies WHERE watch_status = 'Seen'")
    seen_count = cur.fetchone()[0]
    conn.close()
except Exception as _db_err:
    total_count = 0
    seen_count = 0

# Check Query Parameters for select trigger
query_params = st.query_params
if "movie_id" in query_params:
    try:
        st.session_state.selected_movie_id = int(query_params["movie_id"])
    except ValueError:
        pass

# Pre-initialize selected_movie_id if not present or invalid
if 'selected_movie_id' not in st.session_state:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM movies ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        st.session_state.selected_movie_id = row['id']
        st.query_params["movie_id"] = str(row['id'])
else:
    # Always keep query parameters synced with the session state selection to prevent resets on theme/lang switch
    st.query_params["movie_id"] = str(st.session_state.selected_movie_id)


# Read and initialize loaded_count from query parameters or session state
url_loaded = query_params.get('loaded_count')
if url_loaded:
    try:
        st.session_state.loaded_count = int(url_loaded)
    except ValueError:
        pass

# Helper to render Settings Popover (Hidden in Cloud)



@st.dialog("✨ Batch Meta")
def batch_metadata_dialog(covers_dir):
    st.markdown("<style>button[aria-label='Close'] { display: none; }</style>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top:0;'>{t('batch_title')}</h3>", unsafe_allow_html=True)
    
    if st.session_state.get('batch_running', False) or st.session_state.get('batch_paused', False):
        targets = st.session_state.batch_targets
        idx = st.session_state.batch_index
        total = len(targets)
        batch_mode = st.session_state.get('batch_mode', 'basic')
        
        # Phase 1: Analysis loop
        if not st.session_state.get('batch_analysis_done', False):
            if idx >= total:
                st.session_state.batch_analysis_done = True
                st.session_state.batch_index = 0
                st.rerun()
                
            m_id, m_title, m_year = targets[idx]
            status_label = "正在分析" if st.session_state.lang == 'zh' else "Analyzing"
            st.markdown(f"**🔍 {status_label}:** {m_title} ({idx+1}/{total})")
            st.progress(idx / total if total > 0 else 0)
            
            # Process 1 movie analysis
            key = load_tmdb_key()
            m_dict = {"title": m_title, "year": m_year}
            try:
                conn_temp = get_db_connection()
                cur_temp = conn_temp.cursor()
                cur_temp.execute("SELECT * FROM movies WHERE id = ?", (m_id,))
                row_temp = cur_temp.fetchone()
                conn_temp.close()
                if row_temp:
                    m_dict = dict(row_temp)
            except Exception:
                pass
                
            p_path = m_dict.get('physical_path') or m_dict.get('physical_path_mac') or ""
            is_ignore, ignore_reason = classify_ignore_candidate(m_title, p_path)
            
            proposal = {
                "id": m_id,
                "title": m_title,
                "year": m_year,
                "physical_path": p_path,
                "category": "failed",
                "ignore_reason": ignore_reason,
                "matched_title": "",
                "matched_year": "",
                "score": 0,
                "details_en": None,
                "details_zh": None,
                "best_match": None,
                "web_desc": "",
                "proposed_fields": {},
                "poster_path": None
            }
            
            if is_ignore:
                proposal["category"] = "ignore"
            else:
                best = None
                if key:
                    zh_t, en_t = split_chinese_english(m_title)
                    search_queries = [m_title]
                    
                    # Add aka splits
                    if " aka " in m_title.lower():
                        for part in re.split(r'\s+aka\s+', m_title, flags=re.IGNORECASE):
                            search_queries.append(part.strip())
                            
                    if zh_t and zh_t != m_title:
                        search_queries.append(zh_t)
                        if " aka " in zh_t.lower():
                            for part in re.split(r'\s+aka\s+', zh_t, flags=re.IGNORECASE):
                                search_queries.append(part.strip())
                    if en_t and en_t != m_title:
                        search_queries.append(en_t)
                        if " aka " in en_t.lower():
                            for part in re.split(r'\s+aka\s+', en_t, flags=re.IGNORECASE):
                                search_queries.append(part.strip())
                                
                    for query in search_queries:
                        best = get_best_tmdb_match(query, key, m_dict)
                        if best:
                            break
                            
                    if not best:
                        fuzzy_queries = []
                        for q in search_queries:
                            fuzzy_queries.extend(generate_fuzzy_queries(q))
                        fuzzy_queries = list(dict.fromkeys(fuzzy_queries))
                        for q in fuzzy_queries:
                            best = get_best_tmdb_match(q, key, m_dict)
                            if best:
                                break
                                
                if best:
                    score = 0
                    r_title = best.get('title', '')
                    r_orig_title = best.get('original_title', '')
                    rd = best.get('release_date', '')
                    r_year = int(rd.split('-')[0]) if rd else None
                    
                    title_lower = m_title.lower().strip()
                    r_title_lower = r_title.lower().strip()
                    r_orig_title_lower = r_orig_title.lower().strip()
                    
                    if title_lower == r_title_lower or title_lower == r_orig_title_lower:
                        score += 100
                    elif title_lower in r_title_lower or title_lower in r_orig_title_lower:
                        score += 40
                        
                    db_year = m_dict.get('year')
                    if db_year:
                        try:
                            db_year_int = int(db_year)
                            if r_year == db_year_int:
                                score += 100
                            elif r_year and abs(r_year - db_year_int) == 1:
                                score += 50
                        except ValueError:
                            pass
                            
                    proposal["score"] = score
                    proposal["best_match"] = best
                    proposal["matched_title"] = r_title
                    proposal["matched_year"] = r_year
                    
                    if score >= 100:
                        proposal["category"] = "high_confidence"
                    else:
                        proposal["category"] = "low_confidence"
                        
                    # Fetch details
                    try:
                        tmdb_id = best['id']
                        proposal["details_en"] = get_tmdb_movie_details(tmdb_id, key, lang='en-US')
                        proposal["details_zh"] = get_tmdb_movie_details(tmdb_id, key, lang='zh-CN')
                    except Exception:
                        pass
                else:
                    imdb_cands = []
                    if key:
                        imdb_cands = search_imdb_suggestion(m_title)
                        if not imdb_cands:
                            for q in search_queries:
                                imdb_cands = search_imdb_suggestion(q)
                                if imdb_cands:
                                    break
                                    
                    if imdb_cands:
                        for cand in imdb_cands:
                            tmdb_movie = find_tmdb_movie_by_imdb_id(cand['id'], key)
                            if tmdb_movie:
                                best = tmdb_movie
                                try:
                                    tmdb_id = best['id']
                                    proposal["details_en"] = get_tmdb_movie_details(tmdb_id, key, lang='en-US')
                                    proposal["details_zh"] = get_tmdb_movie_details(tmdb_id, key, lang='zh-CN')
                                except Exception:
                                    pass
                                proposal["best_match"] = best
                                proposal["matched_title"] = best.get('title', '')
                                rd = best.get('release_date', '')
                                proposal["matched_year"] = int(rd.split('-')[0]) if rd else None
                                proposal["score"] = 90
                                proposal["category"] = "low_confidence"
                                break
                                
                    if not best:
                        if imdb_cands:
                            cand = imdb_cands[0]
                            proposal["category"] = "imdb_only"
                            proposal["matched_title"] = cand["title"]
                            proposal["matched_year"] = cand["year"]
                            proposal["imdb_id"] = cand["id"]
                            proposal["imdb_actors"] = cand["actors"]
                            proposal["imdb_cover"] = cand["cover_url"]
                        else:
                            desc, guessed_year = search_duckduckgo_fallback(m_title)
                            proposal["category"] = "failed"
                            if desc:
                                proposal["web_desc"] = desc
                                proposal["matched_year"] = guessed_year
                        
            # Populate proposed fields
            details_en = proposal.get("details_en")
            details_zh = proposal.get("details_zh")
            
            if details_en or details_zh:
                details = details_en if details_en else details_zh
                tmdb_id_str = str(details.get('id', ''))
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
                if country:
                    country = re.sub(r'(?<!中国)台湾', '中国台湾', country)
                    country = re.sub(r'(?<!China )Taiwan', 'China Taiwan Province', country)
                orig_lang = details.get('original_language', '')
                
                spoken = details.get('spoken_languages', [])
                languages = ", ".join([l.get('english_name', '') for l in spoken if l.get('english_name')]) if spoken else ""
                
                external_ids = details.get('external_ids', {})
                imdb_id = external_ids.get('imdb_id')
                
                wmdb_data = fetch_wmdb_ratings(imdb_id if imdb_id else m_title)
                douban_id = None
                douban_rating = None
                imdb_rating = details.get('vote_average')
                
                if wmdb_data:
                    douban_id = wmdb_data.get('doubanId')
                    douban_rating = wmdb_data.get('doubanRating')
                    if wmdb_data.get('imdbRating'):
                        imdb_rating = wmdb_data.get('imdbRating')
                        
                proposal["poster_path"] = details.get('poster_path')
                
                existing = get_movie_details(m_id)
                def use_new_if_empty(k, new_val):
                    return existing[k] if existing[k] else new_val
                    
                if batch_mode == 'basic':
                    proposal["proposed_fields"] = {
                        'original_title': use_new_if_empty('original_title', original_title),
                        'genres': use_new_if_empty('genres', genres),
                        'year': use_new_if_empty('year', year),
                        'runtime': use_new_if_empty('runtime', runtime),
                        'country': use_new_if_empty('country', country),
                        'original_language': use_new_if_empty('original_language', orig_lang),
                        'languages': use_new_if_empty('languages', languages),
                        'imdb_id': use_new_if_empty('imdb_id', imdb_id),
                        'tmdb_id': use_new_if_empty('tmdb_id', tmdb_id_str),
                        'imdb_rating': use_new_if_empty('imdb_rating', imdb_rating),
                    }
                else: # extra / all
                    proposal["proposed_fields"] = {
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
            elif proposal["category"] == "imdb_only":
                existing = get_movie_details(m_id)
                def use_new_if_empty(k, new_val):
                    return existing[k] if existing[k] else new_val
                    
                proposal["proposed_fields"] = {
                    'original_title': use_new_if_empty('original_title', proposal["matched_title"]),
                    'year': use_new_if_empty('year', proposal["matched_year"]),
                    'actors': use_new_if_empty('actors', proposal["imdb_actors"]),
                    'imdb_id': use_new_if_empty('imdb_id', proposal["imdb_id"]),
                }
            elif proposal["web_desc"]:
                existing = get_movie_details(m_id)
                def use_new_if_empty(k, new_val):
                    return existing[k] if existing[k] else new_val
                    
                proposal["proposed_fields"] = {
                    'plot': use_new_if_empty('plot', proposal["web_desc"]),
                    'plot_zh': use_new_if_empty('plot_zh', proposal["web_desc"]),
                    'year': use_new_if_empty('year', proposal["matched_year"])
                }
                
            if "batch_analysis_proposals" not in st.session_state:
                st.session_state.batch_analysis_proposals = []
            st.session_state.batch_analysis_proposals.append(proposal)
            
            st.session_state.batch_index += 1
            st.rerun()
            
        # Phase 2: Selection & Commit UI
        else:
            proposals = st.session_state.batch_analysis_proposals
            
            # Split proposals into groups
            high_conf = [p for p in proposals if p['category'] == 'high_confidence']
            low_conf = [p for p in proposals if p['category'] == 'low_confidence']
            imdb_only = [p for p in proposals if p['category'] == 'imdb_only']
            not_found = [p for p in proposals if p['category'] in ('failed', 'not_found')]
            ignored = [p for p in proposals if p['category'] == 'ignore']
            
            # Show summary
            summary_msg = f"📊 分析完毕：共 {len(proposals)} 部 | 置信高 {len(high_conf)} | 模糊 {len(low_conf)} | 仅 IMDb {len(imdb_only)} | 忽略 {len(ignored)} | 未找到 {len(not_found)}"
            if st.session_state.lang != 'zh':
                summary_msg = f"📊 Analysis complete: {len(proposals)} total | High-conf {len(high_conf)} | Fuzzy {len(low_conf)} | IMDb Only {len(imdb_only)} | Ignored {len(ignored)} | Not Found {len(not_found)}"
            st.info(summary_msg)
            
            selected_actions = {}
            
            # Render groups
            if high_conf:
                with st.expander(f"✅ 匹配有把握 ({len(high_conf)} 部)" if st.session_state.lang == 'zh' else f"✅ High Confidence Matches ({len(high_conf)})", expanded=True):
                    sel_all = st.checkbox("全选高置信度" if st.session_state.lang == 'zh' else "Select All High Conf", value=True, key="sel_all_high")
                    for p in high_conf:
                        lbl = f"{p['title']} ➡️ {p['matched_title']} ({p['matched_year']})"
                        selected_actions[p['id']] = st.checkbox(lbl, value=sel_all, key=f"proposal_cb_{p['id']}")
            
            if low_conf:
                with st.expander(f"⚠️ 匹配无把握 / 模糊 ({len(low_conf)} 部)" if st.session_state.lang == 'zh' else f"⚠️ Low Confidence Matches ({len(low_conf)})", expanded=True):
                    sel_all = st.checkbox("全选模糊匹配" if st.session_state.lang == 'zh' else "Select All Fuzzy", value=True, key="sel_all_low")
                    for p in low_conf:
                        lbl = f"{p['title']} ➡️ {p['matched_title']} ({p['matched_year']}) [评分: {p['score']}]"
                        selected_actions[p['id']] = st.checkbox(lbl, value=sel_all, key=f"proposal_cb_{p['id']}")
                        
            if imdb_only:
                with st.expander(f"🎬 仅 IMDb 有匹配 (TMDB 未收录) ({len(imdb_only)} 部)" if st.session_state.lang == 'zh' else f"🎬 IMDb Only Matches ({len(imdb_only)})", expanded=True):
                    sel_all = st.checkbox("全选 IMDb 匹配" if st.session_state.lang == 'zh' else "Select All IMDb Only", value=True, key="sel_all_imdb")
                    for p in imdb_only:
                        actor_preview = f" (主演: {p['imdb_actors']})" if p['imdb_actors'] else ""
                        lbl = f"{p['title']} ➡️ [IMDb] {p['matched_title']} ({p['matched_year']}){actor_preview}"
                        selected_actions[p['id']] = st.checkbox(lbl, value=sel_all, key=f"proposal_cb_{p['id']}")
                        
            if ignored:
                with st.expander(f"🚫 建议忽略 (TV剧集/网页视频/测试数据) ({len(ignored)} 部)" if st.session_state.lang == 'zh' else f"🚫 Ignored Candidates ({len(ignored)})", expanded=False):
                    sel_all = st.checkbox("全选忽略项" if st.session_state.lang == 'zh' else "Select All Ignored", value=False, key="sel_all_ignore")
                    for p in ignored:
                        lbl = f"{p['title']} ({p['ignore_reason']})"
                        selected_actions[p['id']] = st.checkbox(lbl, value=sel_all, key=f"proposal_cb_{p['id']}")
                        
            if not_found:
                with st.expander(f"❌ 均未找到 (TMDB & IMDb 均无匹配) ({len(not_found)} 部)" if st.session_state.lang == 'zh' else f"❌ Not Found ({len(not_found)})", expanded=False):
                    sel_all = st.checkbox("全选未找到项 (使用网页搜索结果填充)" if st.session_state.lang == 'zh' else "Select All Not Found (fill with web snippet)", value=False, key="sel_all_failed")
                    for p in not_found:
                        web_preview = p.get('web_desc', '')
                        web_preview = web_preview[:50] + "..." if web_preview else ("无搜索结果" if st.session_state.lang == 'zh' else "No results")
                        lbl = f"{p['title']} ({web_preview})"
                        selected_actions[p['id']] = st.checkbox(lbl, value=sel_all, key=f"proposal_cb_{p['id']}")
                        
            # Apply / Cancel buttons
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🚀 应用选中的填充", use_container_width=True, key="batch_apply_btn"):
                    # Phase 3: Bulk commit
                    success_count = 0
                    skip_count = 0
                    
                    status_placeholder = st.empty()
                    status_placeholder.info("⏳ 正在落库并下载海报，请稍候...")
                    
                    for i, p in enumerate(proposals):
                        m_id = p["id"]
                        m_title = p["title"]
                        
                        if selected_actions.get(m_id, False):
                            local_cover = os.path.join(covers_dir, f"{m_id}.jpg")
                            poster_url = None
                            if p.get("poster_path"):
                                poster_url = f"https://image.tmdb.org/t/p/w500{p['poster_path']}"
                            elif p.get("category") == "imdb_only" and p.get("imdb_cover"):
                                poster_url = p["imdb_cover"]
                                
                            if poster_url:
                                if not (os.path.exists(local_cover) and os.path.getsize(local_cover) > 0):
                                    try:
                                        img_r = requests.get(poster_url, timeout=10)
                                        if img_r.status_code == 200:
                                            with open(local_cover, 'wb') as img_f:
                                                img_f.write(img_r.content)
                                    except Exception:
                                        pass
                                
                            # Always ensure it is uploaded to GDrive if the local cover exists
                            if os.path.exists(local_cover) and os.path.getsize(local_cover) > 0:
                                upload_poster_to_gdrive(m_id, local_cover)
                            
                            # Update DB
                            if p["proposed_fields"]:
                                update_movie_fields(m_id, p["proposed_fields"])
                            success_count += 1
                        else:
                            skip_count += 1
                            
                    st.session_state.batch_running = False
                    st.session_state.batch_analysis_done = False
                    st.session_state.show_batch_dialog = False
                    st.toast(f"✅ 批量填充成功！已填充 {success_count} 部，忽略/跳过 {skip_count} 部")
                    st.rerun()
                    
            with btn_col2:
                if st.button("❌ 取消并关闭", use_container_width=True, key="batch_cancel_btn"):
                    st.session_state.batch_running = False
                    st.session_state.batch_analysis_done = False
                    st.session_state.show_batch_dialog = False
                    st.rerun()

    else:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Count basic info missing
        cur.execute("""
            SELECT COUNT(*) FROM movies
            WHERE (original_title IS NULL OR original_title = ''
               OR year IS NULL OR year = 0
               OR genres IS NULL OR genres = ''
               OR imdb_rating IS NULL OR imdb_rating = 0
               OR runtime IS NULL OR runtime = 0
               OR country IS NULL OR country = '')
              AND (tmdb_id IS NULL OR tmdb_id = '')
              AND (imdb_id IS NULL OR imdb_id = '')
        """)
        basic_count = cur.fetchone()[0]
        
        # Count supplementary info missing individually
        cur.execute("SELECT COUNT(*) FROM movies WHERE title_zh IS NULL OR title_zh = ''")
        cnt_title_zh = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM movies WHERE plot IS NULL OR plot = ''")
        cnt_plot = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM movies WHERE plot_zh IS NULL OR plot_zh = ''")
        cnt_plot_zh = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM movies WHERE director_zh IS NULL OR director_zh = ''")
        cnt_dir_zh = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM movies WHERE actors_zh IS NULL OR actors_zh = ''")
        cnt_act_zh = cur.fetchone()[0]
        conn.close()
        
        key = load_tmdb_key()
        if not key:
            st.warning(t("batch_key_warning"))
            if st.button("关闭" if st.session_state.lang == 'zh' else "Close", use_container_width=True, key="batch_close_nokey"):
                st.session_state.show_batch_dialog = False
                st.rerun()
            return
        
        batch_limit = st.slider(t("batch_limit_label"), min_value=10, max_value=500, value=50, step=10, key="dialog_batch_limit")
        
        tab_basic, tab_extra = st.tabs([t("batch_mode_basic"), t("batch_mode_extra")])
        
        with tab_basic:
            st.caption(t("batch_mode_basic_help"))
            st.markdown(f"**{basic_count}** 部 {t('batch_mode_basic_count')}" if st.session_state.lang == 'zh' else f"**{basic_count}** movies {t('batch_mode_basic_count')}")
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button(t("batch_start_btn"), use_container_width=True, key="batch_start_basic", disabled=basic_count == 0):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id, title, year FROM movies
                        WHERE (original_title IS NULL OR original_title = ''
                           OR year IS NULL OR year = 0
                           OR genres IS NULL OR genres = ''
                           OR imdb_rating IS NULL OR imdb_rating = 0
                           OR runtime IS NULL OR runtime = 0
                           OR country IS NULL OR country = '')
                          AND (tmdb_id IS NULL OR tmdb_id = '')
                          AND (imdb_id IS NULL OR imdb_id = '')
                        LIMIT ?
                    """, (batch_limit,))
                    targets = cur.fetchall()
                    conn.close()
                    if targets:
                        st.session_state.batch_targets = targets
                        st.session_state.batch_index = 0
                        st.session_state.batch_success = 0
                        st.session_state.batch_skip = 0
                        st.session_state.batch_analysis_proposals = []
                        st.session_state.batch_analysis_done = False
                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.session_state.batch_logs = []
                        st.session_state.batch_mode = 'basic'
                        st.rerun()
            with bc2:
                if st.button("关闭" if st.session_state.lang == 'zh' else "Close", use_container_width=True, key="batch_close_basic"):
                    st.session_state.show_batch_dialog = False
                    st.rerun()
        
        with tab_extra:
            st.caption(t("batch_mode_extra_help"))
            
            st.markdown("##### " + ("选择需要补全的项：" if st.session_state.lang == 'zh' else "Select fields to fill:"))
            fill_title_zh = st.checkbox(f"🎬 中文片名 (缺少 {cnt_title_zh} 条)" if st.session_state.lang == 'zh' else f"🎬 Chinese Title (missing {cnt_title_zh})", value=(cnt_title_zh > 0))
            fill_plot_zh = st.checkbox(f"📝 中文简介 (缺少 {cnt_plot_zh} 条)" if st.session_state.lang == 'zh' else f"📝 Chinese Plot (missing {cnt_plot_zh})", value=(cnt_plot_zh > 0))
            fill_plot = st.checkbox(f"📄 英文简介 (缺少 {cnt_plot} 条)" if st.session_state.lang == 'zh' else f"📄 English Plot (missing {cnt_plot})", value=(cnt_plot > 0))
            fill_dir_zh = st.checkbox(f"🎥 中文导演名 (缺少 {cnt_dir_zh} 条)" if st.session_state.lang == 'zh' else f"🎥 Chinese Director (missing {cnt_dir_zh})", value=(cnt_dir_zh > 0))
            fill_act_zh = st.checkbox(f"🎭 中文演员名 (缺少 {cnt_act_zh} 条)" if st.session_state.lang == 'zh' else f"🎭 Chinese Actors (missing {cnt_act_zh})", value=(cnt_act_zh > 0))
            
            conditions = []
            if fill_plot: conditions.append("(plot IS NULL OR plot = '')")
            if fill_plot_zh: conditions.append("(plot_zh IS NULL OR plot_zh = '')")
            if fill_title_zh: conditions.append("(title_zh IS NULL OR title_zh = '')")
            if fill_dir_zh: conditions.append("(director_zh IS NULL OR director_zh = '')")
            if fill_act_zh: conditions.append("(actors_zh IS NULL OR actors_zh = '')")
            
            where_clause = " OR ".join(conditions) if conditions else "1=0"
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM movies WHERE {where_clause}")
            extra_count = cur.fetchone()[0]
            conn.close()
            
            st.markdown(f"**{extra_count}** 部 {t('batch_mode_extra_count')}" if st.session_state.lang == 'zh' else f"**{extra_count}** movies {t('batch_mode_extra_count')}")
            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button(t("batch_start_btn"), use_container_width=True, key="batch_start_extra", disabled=extra_count == 0):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(f"""
                        SELECT id, title, year FROM movies
                        WHERE {where_clause}
                        LIMIT ?
                    """, (batch_limit,))
                    targets = cur.fetchall()
                    conn.close()
                    if targets:
                        st.session_state.batch_targets = targets
                        st.session_state.batch_index = 0
                        st.session_state.batch_success = 0
                        st.session_state.batch_skip = 0
                        st.session_state.batch_analysis_proposals = []
                        st.session_state.batch_analysis_done = False
                        st.session_state.batch_running = True
                        st.session_state.batch_paused = False
                        st.session_state.batch_logs = []
                        st.session_state.batch_mode = 'extra'
                        st.rerun()
            with ec2:
                if st.button("关闭" if st.session_state.lang == 'zh' else "Close", use_container_width=True, key="batch_close_extra"):
                    st.session_state.show_batch_dialog = False
                    st.rerun()

def select_directory_native():
    import subprocess
    try:
        prompt = t("select_dir_prompt")
        cmd = ["osascript", "-e", f'POSIX path of (choose folder with prompt "{prompt}")']
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def select_file_native():
    import sys
    if sys.platform == 'darwin':
        import subprocess
        try:
            prompt = "选择电影文件" if st.session_state.lang == 'zh' else "Choose Movie File"
            cmd = ["osascript", "-e", f'POSIX path of (choose file with prompt "{prompt}")']
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return res.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    else:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            file_path = filedialog.askopenfilename(parent=root, title="选择电影文件")
            root.destroy()
            return file_path
        except Exception:
            return ""

def render_settings_popover(total_count, seen_count, text_color, sub_text_color, covers_dir):
    with st.popover(t("settings_stats"), use_container_width=True):
        st.markdown(f"<h3 style='color:{text_color};margin-top:0;'>{t('settings_stats')}</h3>", unsafe_allow_html=True)
        
        # Compact Stats
        st.markdown(f"<div style='font-size:0.9rem; margin-bottom: 0.8rem;'>📊 {t('total_movies')}: <strong>{total_count}</strong> &nbsp;&nbsp;|&nbsp;&nbsp; 👁️ {t('watched')}: <strong>{seen_count}</strong> ({int(seen_count/total_count*100) if total_count > 0 else 0}%)</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # TMDB API Key config
        st.markdown(f"**{t('tmdb_key_label')}**")
        loaded_key = load_tmdb_key()
        st.markdown("""
        <style>
        input[aria-label="TMDB API 密钥"], input[aria-label="TMDB API Key"] {
            -webkit-text-security: disc;
        }
        </style>
        """, unsafe_allow_html=True)
        tmdb_key = st.text_input(t("tmdb_key_label"),
                                 value=loaded_key,
                                 help=t("tmdb_key_help"),
                                 key="header_tmdb_key",
                                 label_visibility="collapsed")
        
        if st.button(t("save_key_btn"), use_container_width=True, key="header_save_key_btn"):
            if save_tmdb_key_permanently(tmdb_key):
                st.success(t("save_key_success"))
                st.rerun()
                    
        # Path Mapping Manager
        st.markdown("---")
        st.markdown(f"**{t('path_mapping_section')}**")
        st.markdown(f"<div style='font-size:0.82rem;color:{sub_text_color};margin-bottom:0.8rem;'>{t('path_mapping_help')}</div>", unsafe_allow_html=True)
        
        rules = load_path_mappings()
        
        # Display existing rules
        if rules:
            st.markdown(f"<div style='font-size:0.85rem;font-weight:bold;margin-bottom:0.3rem;'>{t('path_mapping_current')}:</div>", unsafe_allow_html=True)
            for idx, r in enumerate(rules):
                col_r1, col_r2 = st.columns([7, 1])
                with col_r1:
                    st.markdown(f"<div style='font-size:0.82rem;background:rgba(0,0,0,0.15);padding:0.3rem 0.5rem;border-radius:0.25rem;word-break:break-all;'><code>{r['win']}</code> ➡️ <code>{r['mac']}</code></div>", unsafe_allow_html=True)
                with col_r2:
                    if st.button("🗑️", key=f"del_rule_{idx}", use_container_width=True):
                        rules.pop(idx)
                        save_path_mappings(rules)
                        st.session_state.show_movie_edit_dialog = False
                        st.session_state.show_batch_dialog = False
                        st.rerun()
            st.markdown("---")
        else:
            st.markdown(f"<div style='font-size:0.82rem;color:#94a3b8;margin-bottom:0.8rem;'>{t('path_mapping_none')}.</div>", unsafe_allow_html=True)
        
        # Add new rule
        st.markdown(f"<div style='font-size:0.85rem;font-weight:bold;'>{t('path_mapping_add')}:</div>", unsafe_allow_html=True)
        
        if "new_mac_prefix" not in st.session_state:
            st.session_state.new_mac_prefix = ""
            
        col_add_win, col_add_mac, col_add_btn = st.columns([1.5, 1.8, 1], vertical_alignment="bottom")
        with col_add_win:
            new_win = st.text_input(t("path_mapping_win_lbl") + ":", placeholder="e:\\movies", key="new_win_prefix")
        with col_add_mac:
            def on_add_browse_click():
                st.session_state.show_movie_edit_dialog = False
                st.session_state.show_batch_dialog = False
                chosen_path = select_directory_native()
                if chosen_path:
                    st.session_state.new_mac_prefix = chosen_path
            col_mac_in, col_mac_br = st.columns([2.2, 1], vertical_alignment="bottom")
            with col_mac_in:
                new_mac = st.text_input(t("path_mapping_mac_lbl") + ":", key="new_mac_prefix", placeholder="/Volumes/Seagate")
            with col_mac_br:
                st.button("📂", key="add_browse_btn", use_container_width=True, on_click=on_add_browse_click)
        def on_add_rule_click():
            win_val = st.session_state.get("new_win_prefix", "").strip()
            mac_val = st.session_state.get("new_mac_prefix", "").strip()
            if win_val and mac_val:
                current_rules = load_path_mappings()
                current_rules.append({"win": win_val, "mac": mac_val})
                save_path_mappings(current_rules)
                st.session_state.new_mac_prefix = ""
                st.session_state.new_win_prefix = ""
                st.session_state.show_movie_edit_dialog = False
                st.session_state.show_batch_dialog = False
            else:
                st.session_state.rule_input_error = True
                
        with col_add_btn:
            st.button(t("path_mapping_add_btn"), key="add_rule_btn", use_container_width=True, on_click=on_add_rule_click)
            if st.session_state.get("rule_input_error"):
                st.error(t("path_mapping_input_err"))
                st.session_state.rule_input_error = False

        # Duplicate check section
        st.markdown("---")
        st.markdown(f"**{t('duplicate_check_section')}**")
        if st.button(t("run_duplicate_check_btn"), use_container_width=True, key="header_dup_check_btn"):
            st.session_state.show_duplicate_dialog = True
            st.session_state.show_movie_edit_dialog = False
            st.session_state.show_batch_dialog = False
            st.rerun()
                    

# Shared dialog for Add and Edit Movie
def render_manual_edit_form(movie=None):
    if movie is None:
        movie = {
            'id': None, 'title': '', 'original_title': '', 'year': 0, 'runtime': 0,
            'original_language': '', 'languages': '', 'genres': '', 'director': '',
            'actors': '', 'plot': '', 'title_zh': '', 'director_zh': '', 'actors_zh': '',
            'plot_zh': '', 'imdb_id': '', 'imdb_rating': 0.0, 'douban_id': '',
            'douban_rating': 0.0, 'country': '', 'tmdb_id': '', 'physical_path': '',
            'physical_path_mac': '', 'watch_status': 'Unseen'
        }
    else:
        movie = dict(movie)

    # Initialize session state for paths if target movie changed or not initialized
    movie_id = movie.get('id')
    if "edit_movie_id" not in st.session_state or st.session_state.edit_movie_id != movie_id:
        st.session_state.edit_movie_id = movie_id
        win_p = movie.get('physical_path') or ""
        mac_p = movie.get('physical_path_mac') or ""
        rules = load_path_mappings()
        if win_p and not mac_p:
            mac_p = to_mac_path(win_p, rules)
        elif mac_p and not win_p:
            win_p = to_win_path(mac_p, rules)
        st.session_state.edit_win_path = win_p
        st.session_state.edit_mac_path = mac_p

    e_title = st.text_input(t("form_title") + " *", value=movie['title'])
    e_orig_title = st.text_input(t("form_orig_title"), value=(movie['original_title'] if movie['original_title'] else ""))
    
    col_y, col_r = st.columns(2)
    with col_y:
        e_year = st.number_input(t("form_year"), value=int(movie['year']) if movie['year'] else 0, step=1)
    with col_r:
        e_runtime = st.number_input(t("form_runtime"), value=int(movie['runtime']) if movie['runtime'] else 0, step=1)
            
    e_orig_lang = st.text_input(t("form_orig_lang"), value=dict(movie).get('original_language', ''))
    e_languages = st.text_input(t("form_audio_lang"), value=dict(movie).get('languages', ''))
    
    e_genres = st.text_input(t("form_genres"), value=(movie['genres'] if movie['genres'] else ""))
    e_director = st.text_input(t("form_director"), value=(movie['director'] if movie['director'] else ""))
    e_actors = st.text_area(t("form_actors"), value=(movie['actors'] if movie['actors'] else ""))
    e_plot = st.text_area(t("form_plot"), value=(movie['plot'] if movie['plot'] else ""))
    
    st.markdown(f"**{t('manual_loc_zh_header')}**")
    e_title_zh = st.text_input(t("manual_zh_title"), value=(dict(movie).get('title_zh', '') if dict(movie).get('title_zh') else ""))
    e_director_zh = st.text_input(t("manual_zh_director"), value=(dict(movie).get('director_zh', '') if dict(movie).get('director_zh') else ""))
    e_actors_zh = st.text_area(t("manual_zh_actors"), value=(dict(movie).get('actors_zh', '') if dict(movie).get('actors_zh') else ""))
    e_plot_zh = st.text_area(t("manual_zh_plot"), value=(dict(movie).get('plot_zh', '') if dict(movie).get('plot_zh') else ""))
    
    col_id1, col_id2 = st.columns(2)
    with col_id1:
        e_imdb_id = st.text_input(t("form_imdb_id"), value=(movie['imdb_id'] if movie['imdb_id'] else ""))
        e_imdb_rating = st.number_input(t("form_imdb_rating"), value=float(movie['imdb_rating']) if movie['imdb_rating'] else 0.0, step=0.1)
    with col_id2:
        e_douban_id = st.text_input(t("form_douban_id"), value=(movie['douban_id'] if movie['douban_id'] else ""))
        e_douban_rating = st.number_input(t("form_douban_rating"), value=float(movie['douban_rating']) if movie['douban_rating'] else 0.0, step=0.1)
    
    e_country = st.text_input(t("form_country"), value=(movie['country'] if movie['country'] else ""))
    if e_country:
        e_country = re.sub(r'(?<!中国)台湾', '中国台湾', e_country)
        e_country = re.sub(r'(?<!China )Taiwan', 'China Taiwan Province', e_country)
    e_tmdb_id = st.text_input(t("form_tmdb_id"), value=(movie['tmdb_id'] if movie['tmdb_id'] else ""))
    
    # Path mapping rules for live validation
    rules = load_path_mappings()
    is_curr_mac = sys.platform == 'darwin'
    
    win_exists = False
    win_path_val = st.session_state.get("edit_win_path", "").strip()
    if win_path_val:
        paths = [p.strip() for p in win_path_val.split(';') if p.strip()]
        exists_list = []
        for p in paths:
            if is_curr_mac:
                mapped = to_mac_path(p, rules)
                exists_list.append(exists_case_insensitive(mapped))
            else:
                exists_list.append(exists_case_insensitive(p))
        win_exists = all(exists_list) if exists_list else False
            
    mac_exists = False
    mac_path_val = st.session_state.get("edit_mac_path", "").strip()
    if mac_path_val:
        paths = [p.strip() for p in mac_path_val.split(';') if p.strip()]
        exists_list = []
        for p in paths:
            if is_curr_mac:
                exists_list.append(exists_case_insensitive(p))
            else:
                mapped = to_win_path(p, rules)
                exists_list.append(exists_case_insensitive(mapped))
        mac_exists = all(exists_list) if exists_list else False

    # Unified status: found if either is found
    if win_exists or mac_exists:
        unified_status = "🟢 " + ("文件已找到" if st.session_state.lang == 'zh' else "File found")
    else:
        unified_status = "🔴 " + ("文件未找到" if st.session_state.lang == 'zh' else "File not found")

    st.markdown("---")
    
    hdr_col1, hdr_col2 = st.columns([2.5, 1], vertical_alignment="center")
    with hdr_col1:
        st.markdown(f"**{t('manual_file_watch_header')}**")
    with hdr_col2:
        st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 0.95rem;'>{unified_status}</div>", unsafe_allow_html=True)
    
    col_path_edit, col_seen_edit = st.columns([2.5, 1], vertical_alignment="top")
    with col_path_edit:
        win_input_val = st.session_state.get("edit_win_path", "")
        mac_input_val = st.session_state.get("edit_mac_path", "")
        
        e_win_p = st.text_input("Win 路径" if st.session_state.lang == 'zh' else "Win Path", value=win_input_val)
        st.session_state.edit_win_path = e_win_p
            
        e_mac_p = st.text_input("Mac 路径" if st.session_state.lang == 'zh' else "Mac Path", value=mac_input_val)
        st.session_state.edit_mac_path = e_mac_p
            
    with col_seen_edit:
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        e_seen = st.checkbox(t("manual_watched"), value=(dict(movie).get('watch_status') == 'Seen'))
        st.markdown("<div style='height: 1.0rem;'></div>", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            refresh_help = "根据映射规则自动转换并刷新对应的 Win/Mac 路径" if st.session_state.lang == 'zh' else "Convert and refresh Win/Mac paths based on mapping rules"
            if st.button("🔄", use_container_width=True, key="btn_refresh_paths", help=refresh_help):
                win_p = st.session_state.get("edit_win_path", "").strip()
                mac_p = st.session_state.get("edit_mac_path", "").strip()
                if win_p and not mac_p:
                    st.session_state.edit_mac_path = to_mac_path(win_p, rules)
                elif mac_p and not win_p:
                    st.session_state.edit_win_path = to_win_path(mac_p, rules)
                elif win_p and mac_p:
                    st.session_state.edit_mac_path = to_mac_path(win_p, rules)
                    st.session_state.edit_win_path = to_win_path(mac_p, rules)
                st.rerun()
        with btn_col2:
            find_help = "查找文件" if st.session_state.lang == 'zh' else "Find File"
            if st.button("🔍", use_container_width=True, key="btn_find_file_edit", help=find_help):
                chosen_file = select_file_native()
                if chosen_file:
                    st.session_state.edit_win_path = to_win_path(chosen_file, rules)
                    st.session_state.edit_mac_path = to_mac_path(chosen_file, rules)
                    st.rerun()
    
    bc1, bc2 = st.columns(2)
    with bc1:
        submit_edit = st.button(t("form_submit"), use_container_width=True, type="primary")
    with bc2:
        close_btn = st.button("关闭" if st.session_state.lang == 'zh' else "Close", use_container_width=True)
        
    if close_btn:
        st.session_state.show_movie_edit_dialog = False
        st.rerun()

    if submit_edit:
        if not e_title.strip():
            st.error(t("title_required_err"))
        else:
            win_p = st.session_state.get("edit_win_path", "").strip()
            mac_p = st.session_state.get("edit_mac_path", "").strip()
            update_fields = {
                'title': e_title,
                'original_title': e_orig_title if e_orig_title else None,
                'year': e_year if e_year > 0 else None,
                'runtime': e_runtime if e_runtime > 0 else None,
                'original_language': e_orig_lang if e_orig_lang else None,
                'languages': e_languages if e_languages else None,
                'genres': e_genres if e_genres else None,
                'director': e_director if e_director else None,
                'actors': e_actors if e_actors else None,
                'plot': e_plot if e_plot else None,
                'title_zh': e_title_zh if e_title_zh else None,
                'director_zh': e_director_zh if e_director_zh else None,
                'actors_zh': e_actors_zh if e_actors_zh else None,
                'plot_zh': e_plot_zh if e_plot_zh else None,
                'imdb_id': e_imdb_id if e_imdb_id else None,
                'imdb_rating': e_imdb_rating if e_imdb_rating > 0 else None,
                'douban_id': e_douban_id if e_douban_id else None,
                'douban_rating': e_douban_rating if e_douban_rating > 0 else None,
                'country': e_country if e_country else None,
                'tmdb_id': e_tmdb_id if e_tmdb_id else None,
                'watch_status': 'Seen' if e_seen else 'Unseen',
                'physical_path': win_p if win_p else None,
                'physical_path_mac': mac_p if mac_p else None
            }
            if movie['id'] is None:
                new_id = insert_new_movie(e_title.strip())
                update_movie_fields(new_id, update_fields)
                st.session_state.selected_movie_id = new_id
                st.query_params["movie_id"] = str(new_id)
            else:
                update_movie_fields(movie['id'], update_fields)
            st.session_state.show_movie_edit_dialog = False
            st.success(t("form_success"))
            st.rerun()

def render_scan_drive_in_dialog():
    st.markdown(f"**{t('scan_drive_title')}**")
    if "scan_dir_input" not in st.session_state:
        st.session_state.scan_dir_input = ""
    
    def on_browse_click():
        chosen_path = select_directory_native()
        if chosen_path:
            st.session_state.scan_dir_input = chosen_path

    col_dir_input, col_dir_btn = st.columns([3.2, 1], vertical_alignment="bottom")
    with col_dir_input:
        scan_dir = st.text_input(t("scan_dir_label"), key="scan_dir_input", placeholder="/Volumes/Seagate/movies")
    with col_dir_btn:
        st.button("📂 " + t("browse_btn"), key="choose_folder_btn", use_container_width=True, on_click=on_browse_click)
    scan_sub = st.checkbox(t("scan_subdirs_checkbox"), value=True, key="scan_subdirs_check")
    scan_add = st.checkbox(t("scan_add_new_checkbox"), value=True, key="scan_add_new_check")
    scan_link = st.checkbox(t("scan_link_existing_checkbox"), value=True, key="scan_link_check")
    
    if st.button(t("start_scan_btn"), use_container_width=True, key="start_scan_btn"):
        if not scan_dir.strip():
            st.error(t("scan_dir_missing"))
        elif not os.path.isdir(scan_dir.strip()):
            st.error(t("scan_dir_not_found"))
        else:
            with st.spinner("Scanning..."):
                logs, stats = scan_local_directory(scan_dir.strip(), scan_sub, scan_add, scan_link)
                st.session_state.scan_logs = logs
                st.session_state.scan_stats = stats
                
                # Close the edit dialog so the approvals dialog can open on top
                # (When there are no pending approvals we leave the scan dialog open to show results)
                if st.session_state.get('pending_scan_approvals'):
                    st.session_state.show_movie_edit_dialog = False
                st.rerun()
                
    # Render scan results if present in session_state
    if 'scan_stats' in st.session_state:
        st.markdown("---")
        st.markdown(t("scan_report_header"))
        s = st.session_state.scan_stats
        st.write(t("scan_report_stats", total=s['total_files'], added=s['added'], linked=s['linked'], skipped=s['skipped']))
        if st.session_state.scan_logs:
            with st.expander(t("detailed_log"), expanded=False):
                st.code("\n".join(st.session_state.scan_logs))

def render_batch_import_in_dialog():
    st.markdown(f"**{t('import_title')}**")
    uploaded_file = st.file_uploader(t("import_file_label"), type=["csv", "xls", "xlsx"], key="import_file_uploader")
    import_mode_sel = st.selectbox(
        t("import_mode_label"),
        options=["Fill Empty", "Overwrite", "Skip"],
        format_func=lambda x: t(f"import_mode_{x.lower().replace(' ', '_')}"),
        key="import_mode_select"
    )
    
    if st.button(t("import_start_btn"), use_container_width=True, key="import_start_btn"):
        if not uploaded_file:
            st.error(t("import_no_file"))
        else:
            with st.spinner("Importing..."):
                logs, stats = import_metadata_file(uploaded_file, import_mode_sel)
                st.session_state.import_logs = logs
                st.session_state.import_stats = stats
                st.session_state.show_movie_edit_dialog = True
                st.rerun()
                
    # Render import results if present in session_state
    if 'import_stats' in st.session_state:
        st.markdown("---")
        st.markdown(t("import_report_header"))
        s = st.session_state.import_stats
        st.write(t("import_report_stats", total=s['total_rows'], added=s['added'], updated=s['updated'], skipped=s['skipped']))
        if st.session_state.import_logs:
            with st.expander(t("detailed_log"), expanded=False):
                st.code("\n".join(st.session_state.import_logs))

@st.dialog("🎬", width="large")
def movie_edit_dialog(movie=None):
    st.markdown("<style>button[aria-label='Close'] { display: none; }</style>", unsafe_allow_html=True)
    
    if movie is not None:
        st.markdown(f"<h3 style='margin-top:0;'>{t('manual_edit_title')}</h3>", unsafe_allow_html=True)
        render_manual_edit_form(movie)
    else:
        add_method = st.session_state.get("add_method")
        
        if add_method is None:
            st.markdown(f"<h3 style='margin-top:0;'>{t('add_entry_title')}</h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center; margin-bottom: 1.5rem; font-size: 0.95rem;'>{t('add_choose_method')}</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                with st.container(border=True):
                    st.markdown(
                        "<div style='text-align: center; margin-bottom: 1rem;'>"
                        "  <div style='font-size: 2.2rem; margin-bottom: 0.5rem;'>✍️</div>"
                        f"  <div style='font-size: 1.1rem; font-weight: bold;'>{t('manual_add_card')}</div>"
                        "</div>", 
                        unsafe_allow_html=True
                    )
                    if st.button(t("select_btn"), key="btn_choose_manual", use_container_width=True):
                        st.session_state.add_method = "manual"
                        st.rerun()
                
            with col2:
                with st.container(border=True):
                    st.markdown(
                        "<div style='text-align: center; margin-bottom: 1rem;'>"
                        "  <div style='font-size: 2.2rem; margin-bottom: 0.5rem;'>🚀</div>"
                        f"  <div style='font-size: 1.1rem; font-weight: bold;'>{t('scan_drive_card')}</div>"
                        "</div>", 
                        unsafe_allow_html=True
                    )
                    if st.button(t("select_btn"), key="btn_choose_scan", use_container_width=True):
                        st.session_state.add_method = "scan"
                        st.rerun()
                
            with col3:
                with st.container(border=True):
                    st.markdown(
                        "<div style='text-align: center; margin-bottom: 1rem;'>"
                        "  <div style='font-size: 2.2rem; margin-bottom: 0.5rem;'>📥</div>"
                        f"  <div style='font-size: 1.1rem; font-weight: bold;'>{t('batch_import_card')}</div>"
                        "</div>", 
                        unsafe_allow_html=True
                    )
                    if st.button(t("select_btn"), key="btn_choose_import", use_container_width=True):
                        st.session_state.add_method = "import"
                        st.rerun()
                        
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("close_btn"), use_container_width=True, key="btn_close_lvl1"):
                st.session_state.show_movie_edit_dialog = False
                st.rerun()
        else:
            col_back, col_title = st.columns([1, 4.5], vertical_alignment="center")
            with col_back:
                if st.button(t("back_btn"), use_container_width=True, key="btn_back_lvl1"):
                    st.session_state.add_method = None
                    st.rerun()
            with col_title:
                sub_title_text = ""
                if add_method == "manual":
                    sub_title_text = t("manual_add_title")
                elif add_method == "scan":
                    sub_title_text = t("scan_drive_title_simple")
                elif add_method == "import":
                    sub_title_text = t("batch_import_title_simple")
                st.markdown(f"<h3 style='margin:0;'>{sub_title_text}</h3>", unsafe_allow_html=True)
                
            st.markdown("---")
            
            if add_method == "manual":
                render_manual_edit_form(None)
            elif add_method == "scan":
                render_scan_drive_in_dialog()
            elif add_method == "import":
                render_batch_import_in_dialog()

@st.dialog("重复影片检查 (Duplicate Check)", width="large")
def duplicate_check_dialog():
    st.markdown("<style>button[aria-label='Close'] { display: none; }</style>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top:0;'>{t('duplicate_check_dialog_title')}</h3>", unsafe_allow_html=True)
    
    # Run the duplicate check
    dup_imdb, dup_douban, dup_tmdb, dup_ty, dup_path, dup_mismatches = check_duplicates()
    
    # Total count of unique duplicate groups (without double-counting overlapping categories)
    unique_groups = set()
    for d in [dup_imdb, dup_douban, dup_tmdb, dup_ty, dup_path, dup_mismatches]:
        for key, row_list in d.items():
            ids = frozenset(row['id'] for row in row_list)
            if ids:
                unique_groups.add(ids)
    total_groups = len(unique_groups)
    
    if total_groups == 0:
        st.success(t("no_duplicates_found"))
        if st.button(t("close_btn"), use_container_width=True, key="dup_no_close_btn"):
            st.session_state.show_duplicate_dialog = False
            st.rerun()
        return

    st.warning(t("duplicates_warning", count=total_groups))
    
    # We can use tabs for the different duplicate types
    tab_titles = []
    tabs_to_create = []
    
    if dup_imdb:
        tab_titles.append(f"IMDb ID ({len(dup_imdb)})")
        tabs_to_create.append(('imdb', dup_imdb))
    if dup_douban:
        tab_titles.append(f"豆瓣 ID ({len(dup_douban)})" if st.session_state.lang == 'zh' else f"Douban ID ({len(dup_douban)})")
        tabs_to_create.append(('douban', dup_douban))
    if dup_tmdb:
        tab_titles.append(f"TMDb ID ({len(dup_tmdb)})")
        tabs_to_create.append(('tmdb', dup_tmdb))
    if dup_ty:
        tab_titles.append(f"标题与年份 ({len(dup_ty)})" if st.session_state.lang == 'zh' else f"Title & Year ({len(dup_ty)})")
        tabs_to_create.append(('title_year', dup_ty))
    if dup_path:
        tab_titles.append(f"物理路径 ({len(dup_path)})" if st.session_state.lang == 'zh' else f"Physical Path ({len(dup_path)})")
        tabs_to_create.append(('path', dup_path))
    if dup_mismatches:
        tab_titles.append(f"元数据错配 ({len(dup_mismatches)})" if st.session_state.lang == 'zh' else f"Metadata Mismatches ({len(dup_mismatches)})")
        tabs_to_create.append(('mismatch', dup_mismatches))
        
    st_tabs = st.tabs(tab_titles)
    
    for i, (dup_type, dup_dict) in enumerate(tabs_to_create):
        with st_tabs[i]:
            if dup_type == 'mismatch':
                st.info(t("mismatch_help"))
            for key, dup_list in dup_dict.items():
                if dup_type == 'title_year':
                    key_str = f"\"{key[0]}\" ({key[1]})"
                    key_str_clean = f"{key[0]}_{key[1]}"
                else:
                    key_str = key
                    key_str_clean = str(key)
                unit_label = t("mismatch_movies_unit") if dup_type == 'mismatch' else t("duplicate_movies_unit")
                st.markdown(f"##### 🔑 `{key_str}` ({len(dup_list)} {unit_label})")
                for m in dup_list:
                    # Convert sqlite3.Row to dict
                    movie_dict = dict(m)
                    col_m1, col_m2, col_m3 = st.columns([7.6, 1.2, 1.2])
                    with col_m1:
                        m_title = movie_dict.get('title', '')
                        m_orig = movie_dict.get('original_title', '')
                        m_year = movie_dict.get('year', '')
                        m_path = movie_dict.get('physical_path', '')
                        info_text = f"**ID {movie_dict['id']}**: **{m_title}** ({m_year})"
                        if m_orig:
                            info_text += f" | *{m_orig}*"
                        if m_path:
                            info_text += f" | `{m_path}`"
                        st.markdown(info_text)
                    with col_m2:
                        edit_btn_label = "✏️ 编辑" if st.session_state.lang == 'zh' else "✏️ Edit"
                        btn_key = f"dup_edit_{dup_type}_{key_str_clean}_{movie_dict['id']}"
                        if st.button(edit_btn_label, key=btn_key, use_container_width=True):
                            st.session_state.edit_target_movie = movie_dict
                            st.session_state.show_movie_edit_dialog = True
                            st.session_state.show_duplicate_dialog = False
                            st.session_state.edit_came_from_duplicate = True
                            st.rerun()
                    with col_m3:
                        del_btn_key = f"dup_del_{dup_type}_{key_str_clean}_{movie_dict['id']}"
                        if st.button("🗑️", key=del_btn_key, use_container_width=True):
                            st.session_state.dup_delete_confirm = movie_dict['id']
                            st.rerun()
                            
                    # Inline delete confirmation
                    if st.session_state.get('dup_delete_confirm') == movie_dict['id']:
                        st.markdown(f"<div style='background:rgba(239,68,68,0.15);padding:0.6rem;border-radius:0.3rem;margin-bottom:0.5rem;'>⚠️ {t('delete_confirm_msg')}</div>", unsafe_allow_html=True)
                        dc1, dc2 = st.columns(2)
                        with dc1:
                            if st.button(t("confirm_btn"), key=f"conf_del_btn_{del_btn_key}", use_container_width=True, type="primary"):
                                delete_movie(movie_dict['id'])
                                st.session_state.dup_delete_confirm = None
                                st.rerun()
                        with dc2:
                            if st.button(t("cancel_btn"), key=f"canc_del_btn_{del_btn_key}", use_container_width=True):
                                st.session_state.dup_delete_confirm = None
                                st.rerun()
                st.markdown("---")

    if st.button(t("close_btn"), use_container_width=True, key="dup_close_btn"):
        st.session_state.show_duplicate_dialog = False
        st.rerun()

if 'loaded_count' not in st.session_state:
    st.session_state.loaded_count = 36

if 'poster_cols_per_row' not in st.session_state:
    st.session_state.poster_cols_per_row = 6

lang_suffix = f"_{st.session_state.lang}"

# Explicit state init (done early so we can query database early)
for k in ["filter_search_input", f"filter_genre_sel{lang_suffix}", f"filter_status_sel{lang_suffix}", f"filter_country_sel{lang_suffix}", f"filter_lang_sel{lang_suffix}", f"filter_year_sel{lang_suffix}", f"filter_sort_sel{lang_suffix}"]:
    if k not in st.session_state:
        st.session_state[k] = "" if k == "filter_search_input" else "All" if "sort" not in k else "Added"
        
imdb_key = f"filter_imdb_slider{lang_suffix}"
if imdb_key not in st.session_state:
    st.session_state[imdb_key] = (0.0, 10.0)

# Early query execution to get the count of filtered movies
q_val = st.session_state.get("filter_search_input", "")
y_val = st.session_state.get(f"filter_year_sel{lang_suffix}", "All")
g_val = st.session_state.get(f"filter_genre_sel{lang_suffix}", "All")
c_val = st.session_state.get(f"filter_country_sel{lang_suffix}", "All")
l_val = st.session_state.get(f"filter_lang_sel{lang_suffix}", "All")
s_val = st.session_state.get(f"filter_status_sel{lang_suffix}", "All")
i_val = st.session_state.get(f"filter_imdb_slider{lang_suffix}", (0.0, 10.0))

movies_list_raw = search_movies(q_val, g_val, s_val, c_val, y_val, l_val, i_val)

# Sticky Top Header and Search/Filters Bar Container
with st.container():
    st.markdown('<div class="sticky-header-marker"></div>', unsafe_allow_html=True)
    
    # Horizontally Aligned Header containing icon, title, mode toggle, language select, add movie, and settings/stats
    col_logo, col_ctrls = st.columns([1.6, 4.4])
    with col_logo:
        st.markdown(
            f'<div style="display: flex; align-items: center; gap: 0.75rem; padding-top: 0.3rem;">'
            f'  <svg class="app-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="36" height="36" style="vertical-align: middle;">'
            f'    <defs>'
            f'      <linearGradient id="glowGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'        <stop offset="0%" stop-color="#38BDF8" />'
            f'        <stop offset="100%" stop-color="#818CF8" />'
            f'      </linearGradient>'
            f'      <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">'
            f'        <feGaussianBlur stdDeviation="2" result="blur" />'
            f'        <feComposite in="SourceGraphic" in2="blur" operator="over" />'
            f'      </filter>'
            f'    </defs>'
            f'    <rect x="8" y="8" width="84" height="84" rx="22" fill="url(#glowGrad)" opacity="0.12" stroke="url(#glowGrad)" stroke-width="2"/>'
            f'    <path d="M 28,34 L 72,24 L 70,33 L 26,43 Z" fill="#F8FAFC" filter="url(#neonGlow)" />'
            f'    <path d="M 33,33 L 37,32 M 43,30 L 47,29 M 53,28 L 57,27 M 63,26 L 67,25" stroke="#0F172A" stroke-width="2.5" stroke-linecap="round" />'
            f'    <rect x="25" y="44" width="50" height="32" rx="6" fill="#151726" stroke="url(#glowGrad)" stroke-width="2" />'
            f'    <rect x="32" y="52" width="36" height="3" rx="1.5" fill="#818CF8" opacity="0.5" />'
            f'    <rect x="32" y="60" width="22" height="3" rx="1.5" fill="#38BDF8" opacity="0.5" />'
            f'    <polygon points="48,51 58,56 48,61" fill="#38BDF8" />'
            f'  </svg>'
            f'  <div>'
            f'    <div style="color: {header_title_color}; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1.1;">Movie Label <span class="title-highlight">Revived</span></div>'
            f'    <div style="font-size: 0.85rem; color: {sub_text_color}; margin-top: 0.2rem; font-weight: 500; display: flex; align-items: center; gap: 0.3rem;">'
            f'      <span>{"共" if st.session_state.lang == "zh" else "Total:"}</span>'
            f'      <span class="stat-number">{total_count}</span>'
            f'      <span>部</span>'
            f'      <span style="opacity: 0.4; margin: 0 0.2rem;">|</span>'
            f'      <span>{"已看" if st.session_state.lang == "zh" else "Watched:"}</span>'
            f'      <span class="stat-number">{seen_count}</span>'
            f'      <span>部</span>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
    with col_ctrls:
        # Define localized labels
        is_en = (st.session_state.lang == 'en')
        is_dark = (st.session_state.theme == 'dark')

        lang_left = "中" if st.session_state.lang == "zh" else "ZH"
        lang_right = "英" if st.session_state.lang == "zh" else "EN"
        theme_left = "浅" if st.session_state.lang == "zh" else "Light"
        theme_right = "深" if st.session_state.lang == "zh" else "Dark"

        # Mini controls columns: lang, theme, slider, settings, add (settings & add hidden in cloud)
        if is_cloud:
            col_lang, col_theme, col_slider = st.columns(
                [0.55, 0.65, 3.0], vertical_alignment="center"
            )
        else:
            col_lang, col_theme, col_slider, col_add, col_batch, col_settings = st.columns(
                [0.55, 0.65, 3.0, 0.9, 1.0, 1.0], vertical_alignment="center"
            )
        
        with col_lang:
            st.markdown(f"<span class='toggle-label-left'>{lang_left}</span>", unsafe_allow_html=True)
            
            if "lang_toggle_val" not in st.session_state:
                st.session_state.lang_toggle_val = is_en
            else:
                st.session_state.lang_toggle_val = is_en
            
            def on_lang_toggle():
                new_l = 'en' if st.session_state.lang_toggle_val else 'zh'
                st.session_state.lang = new_l
                st.query_params["lang"] = new_l
                save_env_vars({'UI_LANG': new_l})
            
            st.toggle("EN", value=is_en, key="lang_toggle_val", on_change=on_lang_toggle, label_visibility="collapsed")
            
            st.markdown(f"<span class='toggle-label-right'>{lang_right}</span>", unsafe_allow_html=True)
            
        with col_theme:
            st.markdown(f"<span class='toggle-label-left'>{theme_left}</span>", unsafe_allow_html=True)
            
            def toggle_theme_cb():
                st.session_state.theme = 'dark' if st.session_state.theme_toggle_btn else 'light'
            
            st.toggle("", value=is_dark, key="theme_toggle_btn", on_change=toggle_theme_cb, label_visibility="collapsed")

            st.markdown(f"<span class='toggle-label-right'>{theme_right}</span>", unsafe_allow_html=True)
            
        with col_slider:
            lang_suffix = f"_{st.session_state.lang}"
            col_p_sld, col_i_sld = st.columns([1.0, 1.5], vertical_alignment="center")
            
            with col_p_sld:
                c_lbl, c_minus, c_val, c_plus = st.columns([1.0, 0.45, 0.4, 0.45], vertical_alignment="center")
                with c_lbl:
                    st.markdown(f"<div class='header-label'>{t('columns_slider_label')}</div>", unsafe_allow_html=True)
                with c_minus:
                    if st.button("➖", key="dec_cols_btn", use_container_width=True):
                        st.session_state.poster_cols_per_row = max(2, st.session_state.poster_cols_per_row - 1)
                        st.rerun()
                with c_val:
                    st.markdown(f"<div style='text-align:center; font-weight: 700; font-size:0.95rem; color:{text_color}; padding-top: 0.15rem;'>{st.session_state.poster_cols_per_row}</div>", unsafe_allow_html=True)
                with c_plus:
                    if st.button("➕", key="inc_cols_btn", use_container_width=True):
                        st.session_state.poster_cols_per_row = min(8, st.session_state.poster_cols_per_row + 1)
                        st.rerun()
                    
            with col_i_sld:
                c_imdb_lbl, c_imdb_sld = st.columns([1.3, 2.2], vertical_alignment="center")
                with c_imdb_lbl:
                    st.markdown(f"<div class='header-label'>{t('filter_imdb')}</div>", unsafe_allow_html=True)
                with c_imdb_sld:
                    imdb_filter = st.slider(
                        t("filter_imdb"),
                        min_value=0.0,
                        max_value=10.0,
                        value=(0.0, 10.0),
                        step=0.1,
                        key=f"filter_imdb_slider{lang_suffix}",
                        label_visibility="collapsed"
                    )
                
        if not is_cloud:
            with col_settings:
                render_settings_popover(total_count, seen_count, text_color, sub_text_color, covers_dir)
                
            with col_add:
                if st.button("➕ " + t("add_entry_title"), use_container_width=True):
                    st.session_state.edit_target_movie = None
                    st.session_state.add_method = None
                    if 'scan_stats' in st.session_state:
                        del st.session_state.scan_stats
                    if 'scan_logs' in st.session_state:
                        del st.session_state.scan_logs
                    if 'import_stats' in st.session_state:
                        del st.session_state.import_stats
                    if 'import_logs' in st.session_state:
                        del st.session_state.import_logs
                    st.session_state.show_movie_edit_dialog = True
                    st.rerun()
            with col_batch:
                if st.button(t("batch_meta_title"), use_container_width=True):
                    st.session_state.show_batch_dialog = True
    
    # (Explicit state init was moved to the top of the file to execute queries early)

    
    @st.dialog("📋", width="large")
    def render_scan_approvals_dialog():
        st.markdown(f"<h3 style='margin-top:0;'>{t('duplicate_approval_title')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='margin-top:0;'>{t('duplicate_approval_help')}</h4>", unsafe_allow_html=True)
        approvals = st.session_state.pending_scan_approvals
        
        # Suggest mapping rules globally
        suggested_rules = []
        seen_suggestions = set()
        for item in approvals:
            db_path = item["db_movie"]["physical_path"]
            local_path = item["filepath"]
            if db_path and local_path:
                db_pref, mac_pref = suggest_mapping_rule(db_path, local_path)
                if db_pref and mac_pref:
                    suggestion = (db_pref, mac_pref)
                    if suggestion not in seen_suggestions:
                        seen_suggestions.add(suggestion)
                        suggested_rules.append({"win": db_pref, "mac": mac_pref})
                        
        if suggested_rules:
            st.markdown(f"**{t('suggested_mappings_title')}**")
            st.markdown(f"<div style='font-size:0.82rem;color:#94a3b8;margin-bottom:0.8rem;'>{t('suggested_mappings_help')}</div>", unsafe_allow_html=True)
            
            if "checked_suggested_mappings" not in st.session_state or len(st.session_state.checked_suggested_mappings) != len(suggested_rules):
                st.session_state.checked_suggested_mappings = [True] * len(suggested_rules)
                
            for r_idx, rule in enumerate(suggested_rules):
                st.session_state.checked_suggested_mappings[r_idx] = st.checkbox(
                    f"Win: `{rule['win']}` ➡️ Mac: `{rule['mac']}`",
                    value=st.session_state.checked_suggested_mappings[r_idx],
                    key=f"chk_suggested_mapping_{r_idx}"
                )
            st.markdown("<div style='border-bottom:1px solid rgba(255,255,255,0.1);margin:0.8rem 0;'></div>", unsafe_allow_html=True)

        # Store user decisions in session state
        if "approval_decisions" not in st.session_state or len(st.session_state.approval_decisions) != len(approvals):
            decisions = []
            for item in approvals:
                # Auto-detect multi-part files (CD1/CD2, Part1/Part2)
                f_lower = item["filename"].lower()
                db_path_str = (item["db_movie"].get("physical_path") or "") or (item["db_movie"].get("physical_path_mac") or "")
                db_f_lower = os.path.basename(db_path_str).lower()
                
                is_multi = False
                for pattern in [r'cd\s*\d', r'part\s*\d', r'dvd\s*\d', r'disc\s*\d', r'pt\s*\d']:
                    if re.search(pattern, f_lower) or re.search(pattern, db_f_lower):
                        is_multi = True
                        break
                
                if is_multi:
                    decisions.append("link")
                else:
                    scen = item.get("scenario")
                    if scen == "ii":
                        decisions.append("mapping")
                    else:
                        decisions.append("update")
            st.session_state.approval_decisions = decisions
            
        decisions = st.session_state.approval_decisions
        
        # Batch Action Buttons
        bc1, bc2, bc3, bc4, bc5 = st.columns(5)
        with bc1:
            if st.button(t("btn_all_update"), key="btn_all_update", use_container_width=True):
                st.session_state.approval_decisions = ["update"] * len(approvals)
                st.rerun()
        with bc2:
            if st.button(t("btn_all_mapping"), key="btn_all_mapping", use_container_width=True):
                st.session_state.approval_decisions = ["mapping"] * len(approvals)
                st.rerun()
        with bc3:
            if st.button(t("btn_all_link"), key="btn_all_link", use_container_width=True):
                st.session_state.approval_decisions = ["link"] * len(approvals)
                st.rerun()
        with bc4:
            if st.button(t("btn_all_add"), key="btn_all_add", use_container_width=True):
                st.session_state.approval_decisions = ["add"] * len(approvals)
                st.rerun()
        with bc5:
            if st.button(t("btn_all_skip"), key="btn_all_skip", use_container_width=True):
                st.session_state.approval_decisions = ["skip"] * len(approvals)
                st.rerun()

        st.markdown("---")
        
        # Table Header
        col_h1, col_h2, col_h3, col_h4 = st.columns([1.8, 3.3, 3.3, 1.6], vertical_alignment="center")
        with col_h1:
            st.markdown(f"**{t('table_hdr_movie')}**")
        with col_h2:
            st.markdown(f"**{t('table_hdr_orig_path')}**")
        with col_h3:
            st.markdown(f"**{t('table_hdr_curr_path')}**")
        with col_h4:
            st.markdown(f"**{t('table_hdr_action')}**")
        st.markdown("<hr style='margin:0.2rem 0 0.5rem 0;'>", unsafe_allow_html=True)
        
        # Table Rows
        for idx, item in enumerate(approvals):
            col_r1, col_r2, col_r3, col_r4 = st.columns([1.8, 3.3, 3.3, 1.6], vertical_alignment="center")
            with col_r1:
                db_movie_title = item['db_movie']['title_zh'] if st.session_state.lang == 'zh' and item['db_movie'].get('title_zh') else item['db_movie']['title']
                st.markdown(f"**{db_movie_title}** ({item['db_movie']['year'] or t('unknown_val')})")
                scen = item.get("scenario")
                if scen == "i":
                    prompt_label = "提示: 修改Win路径" if st.session_state.lang == 'zh' else "Prompt: Update Windows Path"
                    st.markdown(f"<span style='font-size:0.72rem;background:rgba(234,179,8,0.12);color:#facc15;padding:0.1rem 0.35rem;border-radius:0.25rem;'>{prompt_label}</span>", unsafe_allow_html=True)
                elif scen == "ii":
                    prompt_label = "提示: 增加挂载路径" if st.session_state.lang == 'zh' else "Prompt: Add Mount Path"
                    st.markdown(f"<span style='font-size:0.72rem;background:rgba(56,189,248,0.12);color:#38bdf8;padding:0.1rem 0.35rem;border-radius:0.25rem;'>{prompt_label}</span>", unsafe_allow_html=True)
                elif scen == "iii":
                    prompt_label = "提示: 填充Win路径" if st.session_state.lang == 'zh' else "Prompt: Fill Windows Path"
                    st.markdown(f"<span style='font-size:0.72rem;background:rgba(234,179,8,0.12);color:#facc15;padding:0.1rem 0.35rem;border-radius:0.25rem;'>{prompt_label}</span>", unsafe_allow_html=True)
                elif scen == "iv":
                    prompt_label = "提示: 更新OS路径" if st.session_state.lang == 'zh' else "Prompt: Update OS Path"
                    st.markdown(f"<span style='font-size:0.72rem;background:rgba(234,179,8,0.12);color:#facc15;padding:0.1rem 0.35rem;border-radius:0.25rem;'>{prompt_label}</span>", unsafe_allow_html=True)
                elif item.get("old_file_exists", True):
                    st.markdown(f"<span style='font-size:0.72rem;background:rgba(239,68,68,0.12);color:#f87171;padding:0.1rem 0.35rem;border-radius:0.25rem;'>{t('status_duplicate')}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='font-size:0.72rem;background:rgba(234,179,8,0.12);color:#facc15;padding:0.1rem 0.35rem;border-radius:0.25rem;'>{t('status_moved')}</span>", unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"<div style='word-break:break-all;font-size:0.75rem;color:#94a3b8;background:rgba(255,255,255,0.03);padding:0.35rem 0.5rem;border-radius:0.25rem;font-family:monospace;border:1px solid rgba(255,255,255,0.05);'>{item['db_movie']['physical_path']}</div>", unsafe_allow_html=True)
            with col_r3:
                st.markdown(f"<div style='word-break:break-all;font-size:0.75rem;color:#38bdf8;background:rgba(56,189,248,0.03);padding:0.35rem 0.5rem;border-radius:0.25rem;font-family:monospace;border:1px solid rgba(56,189,248,0.08);'>{item['filepath']}</div>", unsafe_allow_html=True)
            with col_r4:
                options = {
                    "update": t("action_update"),
                    "mapping": t("action_mapping"),
                    "link": t("action_link"),
                    "add": t("action_add"),
                    "skip": t("action_skip")
                }
                decision_val = st.selectbox(
                    f"Action {idx}",
                    options=list(options.keys()),
                    format_func=lambda x: options[x],
                    index=list(options.keys()).index(decisions[idx]) if decisions[idx] in options else 0,
                    key=f"sel_decision_{idx}",
                    label_visibility="collapsed"
                )
                decisions[idx] = decision_val
            st.markdown("<div style='border-bottom:1px solid rgba(255,255,255,0.06);margin:0.3rem 0;'></div>", unsafe_allow_html=True)
            
        # Bottom Actions
        st.markdown("<br>", unsafe_allow_html=True)
        sub1, sub2 = st.columns([3, 1])
        with sub1:
            if st.button(t("btn_submit_decisions"), key="btn_submit_approvals", use_container_width=True, type="primary"):
                # Load current path mappings
                current_rules = load_path_mappings()
                new_rules_added = []
                
                # Check suggested mapping rules
                if "checked_suggested_mappings" in st.session_state:
                    for r_idx, is_checked in enumerate(st.session_state.checked_suggested_mappings):
                        if is_checked and r_idx < len(suggested_rules):
                            rule = suggested_rules[r_idx]
                            if not any(r["win"].lower() == rule["win"].lower() and r["mac"].lower() == rule["mac"].lower() for r in current_rules):
                                current_rules.append(rule)
                                new_rules_added.append(rule)
                                
                # Check individual mapping decisions
                for idx, item in enumerate(approvals):
                    decision = decisions[idx]
                    if decision == "mapping":
                        db_path = item["db_movie"]["physical_path"]
                        local_path = item["filepath"]
                        db_pref, mac_pref = suggest_mapping_rule(db_path, local_path)
                        if db_pref and mac_pref:
                            rule = {"win": db_pref, "mac": mac_pref}
                            if not any(r["win"].lower() == rule["win"].lower() and r["mac"].lower() == rule["mac"].lower() for r in current_rules):
                                current_rules.append(rule)
                                new_rules_added.append(rule)
                                
                if new_rules_added:
                    save_path_mappings(current_rules)
                    st.toast(t("toast_mapping_saved"))
                    
                conn = get_db_connection()
                cur = conn.cursor()
                added_cnt = 0
                linked_cnt = 0
                skipped_cnt = 0
                
                for idx, item in enumerate(approvals):
                    decision = decisions[idx]
                    db_format_path = item["db_format_path"]
                    db_movie = item["db_movie"]
                    
                    if decision in ["update", "mapping"]:
                        cur.execute("""
                            UPDATE movies 
                            SET physical_path = ?, physical_path_mac = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (item["scanned_win"], item["scanned_mac"], db_movie["id"]))
                        linked_cnt += 1
                    elif decision == "link":
                        old_win = db_movie.get("physical_path") or ""
                        old_mac = db_movie.get("physical_path_mac") or ""
                        new_win = old_win
                        new_mac = old_mac
                        
                        db_win_paths = [p.strip().lower() for p in old_win.split(';') if p.strip()]
                        if item["scanned_win"].lower() not in db_win_paths:
                            new_win = (old_win + "; " + item["scanned_win"]) if old_win else item["scanned_win"]
                            
                        db_mac_paths = [p.strip().lower() for p in old_mac.split(';') if p.strip()]
                        if item["scanned_mac"].lower() not in db_mac_paths:
                            new_mac = (old_mac + "; " + item["scanned_mac"]) if old_mac else item["scanned_mac"]
                            
                        cur.execute("""
                            UPDATE movies 
                            SET physical_path = ?, physical_path_mac = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (new_win, new_mac, db_movie["id"]))
                        linked_cnt += 1
                    elif decision == "add":
                        cur.execute("""
                            INSERT INTO movies (title, year, physical_path, physical_path_mac, watch_status)
                            VALUES (?, ?, ?, ?, 'Unseen')
                        """, (item["guessed_title"], item["guessed_year"], item["scanned_win"], item["scanned_mac"]))
                        added_cnt += 1
                    elif decision == "skip":
                        is_mapped = False
                        db_path = db_movie.get("physical_path") or ""
                        local_path = item["filepath"]
                        db_pref, mac_pref = suggest_mapping_rule(db_path, local_path)
                        if db_pref and mac_pref:
                            if any(r["win"].lower() == db_pref.lower() and r["mac"].lower() == mac_pref.lower() for r in current_rules):
                                is_mapped = True
                        if is_mapped:
                            linked_cnt += 1
                        else:
                            skipped_cnt += 1
                            
                    # Auto-fill missing Chinese/English names in database if matched
                    if decision in ["update", "link", "mapping"]:
                        db_title = db_movie.get("title")
                        db_title_zh = db_movie.get("title_zh")
                        guessed_zh = item.get("guessed_zh_title")
                        guessed_en = item.get("guessed_en_title")
                        
                        if not db_title_zh and guessed_zh:
                            cur.execute("UPDATE movies SET title_zh = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (guessed_zh, db_movie["id"]))
                        if not db_title and guessed_en:
                            cur.execute("UPDATE movies SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (guessed_en, db_movie["id"]))
                            
                conn.commit()
                conn.close()
                
                # Fetch missing metadata and ratings for updated/linked/mapped movies
                for idx, item in enumerate(approvals):
                    decision = decisions[idx]
                    db_movie = item["db_movie"]
                    if decision in ["update", "link", "mapping"]:
                        try:
                            conn_temp = get_db_connection()
                            cur_temp = conn_temp.cursor()
                            cur_temp.execute("SELECT * FROM movies WHERE id = ?", (db_movie["id"],))
                            updated_db_movie = cur_temp.fetchone()
                            conn_temp.close()
                            
                            if updated_db_movie:
                                autocomplete_movie_metadata_if_needed(db_movie["id"], updated_db_movie)
                        except Exception:
                            pass
                
                # Clear state approvals list
                st.session_state.pending_scan_approvals = []
                if "approval_decisions" in st.session_state:
                    del st.session_state.approval_decisions
                if "checked_suggested_mappings" in st.session_state:
                    del st.session_state.checked_suggested_mappings
                    
                st.success(t("approval_success", added=added_cnt, linked=linked_cnt, skipped=skipped_cnt))
                st.rerun()
                
        with sub2:
            if st.button(t("cancel_btn"), key="btn_cancel_approvals", use_container_width=True):
                st.session_state.pending_scan_approvals = []
                if "approval_decisions" in st.session_state:
                    del st.session_state.approval_decisions
                if "checked_suggested_mappings" in st.session_state:
                    del st.session_state.checked_suggested_mappings
                st.rerun()

    if not st.session_state.get('show_movie_edit_dialog', False) and st.session_state.get('edit_came_from_duplicate', False):
        st.session_state.show_duplicate_dialog = True
        st.session_state.edit_came_from_duplicate = False
        st.rerun()

    if st.session_state.get('show_batch_dialog', False):
        batch_metadata_dialog(covers_dir)
    elif st.session_state.get('show_movie_edit_dialog', False):
        movie_edit_dialog(st.session_state.get('edit_target_movie', None))
    elif st.session_state.get('show_duplicate_dialog', False):
        duplicate_check_dialog()
    elif st.session_state.get('pending_scan_approvals'):
        render_scan_approvals_dialog()

    # 1. Main Search and Filters Bar
    col_left_filter, col_right_sort = st.columns([8.4, 1.2], vertical_alignment="bottom")

    with col_left_filter:
        with st.container(border=True):
            col_q, col_reset_btn, col_y, col_g, col_c, col_l, col_s, col_count = st.columns([1.8, 0.28, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1])
            with col_q:
                search_query = st.text_input(" ", placeholder=t("search_placeholder"), key="filter_search_input", label_visibility="hidden")
            with col_reset_btn:
                reset_help = "重置筛选" if st.session_state.lang == 'zh' else "Reset Filters"
                st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
                if st.button("↺", help=reset_help, key=f"reset_filters_btn{lang_suffix}", use_container_width=True):
                    for k in ["filter_search_input", f"filter_year_sel{lang_suffix}", f"filter_genre_sel{lang_suffix}", f"filter_country_sel{lang_suffix}", f"filter_lang_sel{lang_suffix}", f"filter_status_sel{lang_suffix}", f"filter_sort_sel{lang_suffix}", f"filter_sort_dir{lang_suffix}", f"filter_sort_prev_dim{lang_suffix}", f"filter_imdb_slider{lang_suffix}"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
            with col_y:
                year_list = ["All"] + load_years()
                def format_year(y):
                    return t("status_all") if y == "All" else y
                year_filter = st.selectbox(t("filter_year"), year_list, format_func=format_year, key=f"filter_year_sel{lang_suffix}")
            with col_g:
                raw_genres = load_genres()
                # Deduplicate genres via format_genre representation
                def format_genre(g):
                    if g == "All": return t("status_all")
                    if st.session_state.lang == 'zh':
                        return GENRE_MAP_ZH.get(g, g)
                    return g
                
                # Deduplicate and sort
                genre_map_temp = {}
                for g in raw_genres:
                    fmt = format_genre(g)
                    if fmt not in genre_map_temp:
                        genre_map_temp[fmt] = g
                
                if st.session_state.lang == 'zh':
                    def genre_sort_key(s):
                        if s == "成人":
                            return ['z' * 20]
                        return pinyin_sort_key(s)
                    sorted_formatted_genres = sorted(list(genre_map_temp.keys()), key=genre_sort_key)
                else:
                    sorted_formatted_genres = sorted(list(genre_map_temp.keys()))
                sorted_genres = ["All"] + [genre_map_temp[f] for f in sorted_formatted_genres]
                genre_filter = st.selectbox(t("filter_genre"), sorted_genres, format_func=format_genre, key=f"filter_genre_sel{lang_suffix}")
            with col_c:
                raw_countries = load_countries()
                def format_country(c):
                    if c == "All": return t("status_all")
                    if st.session_state.lang == 'zh':
                        return get_country_zh(c)
                    return c
                
                # Deduplicate and sort
                country_map_temp = {}
                for c in raw_countries:
                    fmt = format_country(c)
                    if fmt not in country_map_temp:
                        country_map_temp[fmt] = c
                        
                if st.session_state.lang == 'zh':
                    sorted_formatted_countries = sorted(list(country_map_temp.keys()), key=pinyin_sort_key)
                else:
                    sorted_formatted_countries = sorted(list(country_map_temp.keys()))
                sorted_countries = ["All"] + [country_map_temp[f] for f in sorted_formatted_countries]
                country_filter = st.selectbox(t("filter_country"), sorted_countries, format_func=format_country, key=f"filter_country_sel{lang_suffix}")
            with col_l:
                raw_langs = load_languages()
                def format_lang(l):
                    if l == "All": return t("status_all")
                    if st.session_state.lang == 'zh':
                        return get_language_zh(l)
                    return l
                
                # Deduplicate and sort
                lang_map_temp = {}
                for l in raw_langs:
                    fmt = format_lang(l)
                    if fmt not in lang_map_temp:
                        lang_map_temp[fmt] = l
                        
                if st.session_state.lang == 'zh':
                    sorted_formatted_langs = sorted(list(lang_map_temp.keys()), key=pinyin_sort_key)
                else:
                    sorted_formatted_langs = sorted(list(lang_map_temp.keys()))
                sorted_langs = ["All"] + [lang_map_temp[f] for f in sorted_formatted_langs]
                lang_filter = st.selectbox(t("filter_language") if "filter_language" in I18N[st.session_state.lang] else "🗣️ Language", sorted_langs, format_func=format_lang, key=f"filter_lang_sel{lang_suffix}")
            with col_s:
                status_filter_options = ["All", "Seen", "Unseen"]
                def format_status(s):
                    if s == "All": return t("status_all")
                    if s == "Seen": return t("status_seen")
                    if s == "Unseen": return t("status_unseen")
                    return s
                status_selected = st.selectbox(t("filter_status"), status_filter_options, format_func=format_status, key=f"filter_status_sel{lang_suffix}")
                status_filter = status_selected
                
            with col_count:
                count_lbl = "🎬 " + ("结果" if st.session_state.lang == 'zh' else "Results")
                st.markdown(
                    f"<div style='text-align: right; padding-top: 1.6rem;'>"
                    f"  <span style='font-size: 0.82rem; font-weight: 600; color: {sub_text_color};'>{count_lbl}: </span>"
                    f"  <span style='font-size: 1.15rem; font-weight: 800; color: #38BDF8;'>{len(movies_list_raw)}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    with col_right_sort:
        with st.container(border=True):
            sort_options = ["Year", "IMDb", "Douban", "Alpha", "Added"]
            def format_sort(s):
                t_key = f"sort_{s.lower()}"
                return t(t_key) if t_key in I18N[st.session_state.lang] else s
                
            col_sort_dim, col_sort_dir = st.columns([2.8, 1.2], vertical_alignment="bottom")
            with col_sort_dim:
                sort_selected = st.selectbox(t("sort_label"), sort_options, format_func=format_sort, key=f"filter_sort_sel{lang_suffix}")
                
            # Manage direction state
            dir_key = f"filter_sort_dir{lang_suffix}"
            prev_dim_key = f"filter_sort_prev_dim{lang_suffix}"
            
            def get_default_dir(dim):
                return "asc" if dim == "Alpha" else "desc"
                
            if prev_dim_key not in st.session_state or st.session_state[prev_dim_key] != sort_selected:
                st.session_state[dir_key] = get_default_dir(sort_selected)
                st.session_state[prev_dim_key] = sort_selected
                
            current_dir = st.session_state.get(dir_key, "desc")
            
            with col_sort_dir:
                dir_icon = "⬇️" if current_dir == "desc" else "⬆️"
                dir_help = "倒序 (Desc)" if current_dir == "desc" else "正序 (Asc)"
                if st.button(dir_icon, help=dir_help, key=f"sort_dir_btn{lang_suffix}", use_container_width=True):
                    st.session_state[dir_key] = "asc" if current_dir == "desc" else "desc"
                    st.rerun()

    # (reset button is rendered inside col_left_filter next to search box)

# Add a spacer to prevent content from sliding under the fixed header
st.markdown('<div class="sticky-spacer" style="height: 155px;"></div>', unsafe_allow_html=True)

# Query execution
# (movies_list_raw was already queried early at the top of the file to show the count inside the filters panel)
imdb_filter = st.session_state.get(f"filter_imdb_slider{lang_suffix}", (0.0, 10.0))

# Custom sort based on user selection and cover availability tier
# Custom sort based on user selection and cover availability tier
def get_movie_sort_key(m, query=""):
    m_id = m['id']
    year = m['year'] if m['year'] is not None else 0
    imdb = float(m['imdb_rating']) if m['imdb_rating'] is not None else 0.0
    douban = float(m['douban_rating']) if m['douban_rating'] is not None else 0.0
    if st.session_state.lang == 'zh' and dict(m).get('title_zh'):
        title = str(m['title_zh']).lower()
    else:
        title = str(m['title']).lower()
    
    covers_dir = os.path.join(APP_DIR, 'covers')
    has_cover = os.path.exists(os.path.join(covers_dir, f"{m_id}.jpg"))
    has_year = year > 0
    
    if has_cover and has_year:
        tier = 0
    elif has_cover and not has_year:
        tier = 1
    elif not has_cover and has_year:
        tier = 2
    else:
        tier = 3
        
    # Get current direction from session state
    lang_suffix = f"_{st.session_state.lang}"
    dir_key = f"filter_sort_dir{lang_suffix}"
    is_desc = (st.session_state.get(dir_key, "desc") == "desc")
    
    # 1. Year
    if sort_selected == "Year":
        val = -year if is_desc else year
        return (tier, val, -m_id)
    # 2. IMDb
    elif sort_selected == "IMDb":
        val = -imdb if is_desc else imdb
        return (tier, val, -year, -m_id)
    # 3. Douban
    elif sort_selected == "Douban":
        val = -douban if is_desc else douban
        return (tier, val, -year, -m_id)
    # 4. Alpha
    elif sort_selected == "Alpha":
        val = [-ord(c) for c in title] if is_desc else title
        return (tier, val, -year, -m_id)
    # 5. Added (using m_id as proxy for insertion time)
    # Do NOT apply tier here — tier would cause movies with local covers to
    # float above newly-added movies that haven't been downloaded yet, making
    # the "recently added" sort meaningless.
    elif sort_selected == "Added":
        val = -m_id if is_desc else m_id
        return (0, val)
        
    # Fallback/Default
    if query:
        # Default: preserve relevance order from search_movies, use id as tiebreak
        return (0, -m_id)
    return (tier, -year, -m_id)

lang_suffix = f"_{st.session_state.lang}"
current_dir = st.session_state.get(f"filter_sort_dir{lang_suffix}", "desc")
filter_key = f"{search_query}_{genre_filter}_{status_filter}_{country_filter}_{year_filter}_{sort_selected}_{current_dir}_{lang_filter}_{imdb_filter[0]}_{imdb_filter[1]}"

if st.session_state.get('last_filter_key') != filter_key or st.session_state.get('last_total_movies') != len(movies_list_raw):
    st.session_state.last_filter_key = filter_key
    st.session_state.last_total_movies = len(movies_list_raw)
    st.session_state.loaded_count = 36
    st.query_params["loaded_count"] = "36"
    
    # When searching with default sort (Year), preserve relevance order from search_movies.
    # For explicit sort dimensions (IMDb, Douban, Alpha, Added) apply them even in search mode.
    if search_query and sort_selected == "Year":
        # search_movies already returned results sorted by relevance score
        st.session_state.frozen_movie_ids = [m['id'] for m in movies_list_raw]
    else:
        sorted_raw = sorted(movies_list_raw, key=lambda m: get_movie_sort_key(m, search_query))
        st.session_state.frozen_movie_ids = [m['id'] for m in sorted_raw]

# Reconstruct movies_list based on frozen_movie_ids to prevent grid jumping on metadata updates
movies_dict = {m['id']: m for m in movies_list_raw}
movies_list = []
for mid in st.session_state.get('frozen_movie_ids', []):
    if mid in movies_dict:
        movies_list.append(movies_dict[mid])

# Selection logic initial sync
if 'selected_movie_id' not in st.session_state and movies_list:
    st.session_state.selected_movie_id = movies_list[0]['id']

# Split view layout: Left column is the Movie Poster Wall (Grid), Right column is selected Movie Details
details_ratio = st.session_state.get("details_width_ratio", 40)
col_wall, col_details = st.columns([100 - details_ratio, details_ratio])

# Draggable Splitter Client Component
st.components.v1.html(f"""
<script>
    const parentDoc = window.parent.document;
    
    function initSplitter() {{
        const markerWall = parentDoc.querySelector('.poster-wall-marker');
        const markerDetails = parentDoc.querySelector('.details-panel-marker');
        
        if (!markerWall || !markerDetails) {{
            setTimeout(initSplitter, 100);
            return;
        }}
        
        const colWall = markerWall.closest('[data-testid="stColumn"]');
        const colDetails = markerDetails.closest('[data-testid="stColumn"]');
        if (!colWall || !colDetails) return;
        
        const parent = colWall.parentElement;
        if (!parent) return;
        
        // Ensure flexbox container styling on parent
        parent.style.setProperty('display', 'flex', 'important');
        parent.style.setProperty('flex-direction', 'row', 'important');
        parent.style.setProperty('align-items', 'stretch', 'important');
        parent.style.setProperty('gap', '0px', 'important');
        parent.style.setProperty('width', '100%', 'important');
        parent.style.setProperty('max-width', '100%', 'important');
        
        // Walk up ancestors and force full width to eliminate right blank space
        let ancestor = parent.parentElement;
        while (ancestor && ancestor !== parentDoc.body) {{
            ancestor.style.setProperty('max-width', '100%', 'important');
            ancestor.style.setProperty('width', '100%', 'important');
            ancestor.style.setProperty('padding-right', '0', 'important');
            ancestor = ancestor.parentElement;
        }}
        
        let splitter = parent.querySelector('.custom-splitter-bar');
        if (!splitter) {{
            splitter = parentDoc.createElement('div');
            splitter.className = 'custom-splitter-bar';
            splitter.style.width = '10px';
            splitter.style.cursor = 'col-resize';
            splitter.style.backgroundColor = 'transparent';
            splitter.style.borderLeft = '1px solid rgba(255, 255, 255, 0.05)';
            splitter.style.borderRight = '1px solid rgba(255, 255, 255, 0.05)';
            splitter.style.zIndex = '99';
            splitter.style.margin = '0 -5px';
            splitter.style.alignSelf = 'stretch';
            splitter.style.flexShrink = '0';
            splitter.style.transition = 'background-color 0.2s';
            
            // Hover effect
            splitter.addEventListener('mouseenter', () => {{
                splitter.style.backgroundColor = 'rgba(56, 189, 248, 0.25)';
                splitter.style.borderColor = 'rgba(56, 189, 248, 0.4)';
            }});
            splitter.addEventListener('mouseleave', () => {{
                if (!isDragging) {{
                    splitter.style.backgroundColor = 'transparent';
                    splitter.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                }}
            }});
            
            parent.insertBefore(splitter, colDetails);
        }}
        
        const defaultRatio = 40;
        const minRatio = 20; // 40 - (40 * 0.5)
        const maxRatio = 60; // 40 + (40 * 0.5)
        let currentRatio = {details_ratio};
        
        function applyWidths(ratio) {{
            const wallPct = 100 - ratio;
            colWall.style.setProperty('flex', `1 1 ${{wallPct}}%`, 'important');
            colWall.style.setProperty('width', `${{wallPct}}%`, 'important');
            colWall.style.setProperty('max-width', `${{wallPct}}%`, 'important');
            colWall.style.setProperty('min-width', '0px', 'important');
            
            colDetails.style.setProperty('flex', `1 1 ${{ratio}}%`, 'important');
            colDetails.style.setProperty('width', `${{ratio}}%`, 'important');
            colDetails.style.setProperty('max-width', `${{ratio}}%`, 'important');
            colDetails.style.setProperty('min-width', '0px', 'important');
        }}
        
        applyWidths(currentRatio);
        
        let isDragging = false;
        let startX = 0;
        let startRatio = 0;
        
        splitter.addEventListener('mousedown', (e) => {{
            isDragging = true;
            splitter.style.backgroundColor = 'rgba(56, 189, 248, 0.5)';
            parentDoc.body.style.cursor = 'col-resize';
            parentDoc.body.style.userSelect = 'none';
            startX = e.clientX;
            startRatio = currentRatio;
            e.preventDefault();
        }});
        
        parentDoc.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const parentWidth = parent.getBoundingClientRect().width;
            const dRatio = (dx / parentWidth) * 100;
            
            // Dragging left (negative dx) -> details width ratio increases.
            let ratio = startRatio - dRatio;
            
            if (ratio < minRatio) ratio = minRatio;
            if (ratio > maxRatio) ratio = maxRatio;
            
            currentRatio = ratio;
            applyWidths(currentRatio);
        }});
        
        parentDoc.addEventListener('mouseup', () => {{
            if (isDragging) {{
                isDragging = false;
                splitter.style.backgroundColor = 'transparent';
                parentDoc.body.style.cursor = '';
                parentDoc.body.style.userSelect = '';
                
                // Save to URL query parameters silently
                const url = new URL(window.parent.location.href);
                url.searchParams.set('d_width', currentRatio.toFixed(0));
                window.parent.history.replaceState({{}}, '', url.toString());
            }}
        }});
    }}
    
    initSplitter();
</script>
""", height=0, width=0)

# Left Column - Netflix style Poster Wall
with col_wall:
    # Slice list using loaded_count for waterfall flow
    page_movies = movies_list[:st.session_state.loaded_count]
    
    # Render the custom poster wall grid inside a native scrollable container using st.columns and overlay buttons
    if True:
        st.markdown('<div class="poster-wall-marker"></div>', unsafe_allow_html=True)
        
        # Callback to update selection state prior to rerun
        def select_movie_cb(movie_id):
            st.session_state.selected_movie_id = movie_id
            st.query_params["movie_id"] = str(movie_id)
            st.session_state.show_movie_edit_dialog = False
            st.session_state.show_batch_dialog = False
            if "auto_match_result" in st.session_state:
                del st.session_state.auto_match_result
                
        def toggle_watch_cb(movie_id, current_status):
            new_status = 'Seen' if current_status == 'Unseen' else 'Unseen'
            update_movie_fields(movie_id, {'watch_status': new_status})
            
        cols_per_row = st.session_state.get("poster_cols_per_row", 6)
        for i in range(0, len(page_movies), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(page_movies):
                    m = page_movies[i + j]
                    m_id = m['id']
                    title = m['title_zh'] if st.session_state.lang == 'zh' and m['title_zh'] else m['title']
                    year = m['year'] if m['year'] else 'N/A'
                    rating = f"⭐️ {m['douban_rating']:.1f}" if m['douban_rating'] else (f"⭐️ {m['imdb_rating']:.1f}" if m['imdb_rating'] else "N/A")
                    
                    is_selected = (m_id == st.session_state.get('selected_movie_id'))
                    card_class = "poster-card poster-card-selected" if is_selected else "poster-card"
                    
                    cover_b64 = get_cover_base64(m_id)
                    
                    # Build card HTML. Click interception is handled purely via CSS absolute overlay of Streamlit native button!
                    is_seen = (m['watch_status'] == 'Seen')
                    if is_seen:
                        badge_text = "👁️ 已看" if st.session_state.lang == 'zh' else "👁️ Watched"
                        badge_class = "poster-status-badge poster-status-seen"
                    else:
                        badge_text = "未看" if st.session_state.lang == 'zh' else "Not Watched"
                        badge_class = "poster-status-badge poster-status-unseen"
                    
                    card_html = f'<div class="{card_class}" style="cursor: pointer; width: 100%;">'
                    card_html += '<div class="poster-img-container">'
                    card_html += f'<div class="{badge_class}">{badge_text}</div>'
                    if cover_b64:
                        card_html += f'<img src="{cover_b64}" class="poster-img" alt="{title}" />'
                    else:
                        initials = title[:2] if len(title) >= 2 else title
                        card_html += f'<div class="poster-placeholder">{initials}<div class="poster-placeholder-text">{title}</div></div>'
                    card_html += '</div>'
                    card_html += '<div class="poster-info">'
                    card_html += f'<div class="poster-title" title="{title}">{title}</div>'
                    card_html += f'<div class="poster-meta"><span>📅 {year}</span><span>{rating}</span></div>'
                    card_html += '</div>'
                    card_html += '</div>'
                    
                    with cols[j]:
                        st.markdown(card_html, unsafe_allow_html=True)
                        # Bulletproof overlay using responsive percentage-based negative margins and aspect-ratio matching the 2:3 card
                        st.markdown(f"""
                        <div id="btn_marker_{m_id}" style="display:none;"></div>
                        <style>
                        div.element-container:has(#btn_marker_{m_id}) {{
                            display: none;
                        }}
                        div.element-container:has(#btn_marker_{m_id}) + div.element-container {{
                            margin-top: calc(-150% - 68px) !important;
                            width: 100% !important;
                            aspect-ratio: 2/3 !important;
                            padding-bottom: 68px !important;
                            box-sizing: content-box !important;
                            position: relative !important;
                            z-index: 10 !important;
                            opacity: 0 !important;
                        }}
                        div.element-container:has(#btn_marker_{m_id}) + div.element-container div.stButton {{
                            height: 100% !important;
                        }}
                        div.element-container:has(#btn_marker_{m_id}) + div.element-container button {{
                            width: 100% !important;
                            height: 100% !important;
                            cursor: pointer !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Render a fully transparent button that covers the entire card
                        st.button(" ", key=f"poster_btn_{m_id}", on_click=select_movie_cb, args=(m_id,), use_container_width=True)
                        
                        st.markdown(f"""
                        <div id="badge_marker_{m_id}" style="display:none;"></div>
                        <style>
                        div.element-container:has(#badge_marker_{m_id}) {{
                            display: none;
                        }}
                        div.element-container:has(#badge_marker_{m_id}) + div.element-container {{
                            margin-top: calc(-150% - 68px) !important;
                            width: 100% !important;
                            aspect-ratio: 2/3 !important;
                            padding-bottom: 68px !important;
                            box-sizing: content-box !important;
                            position: relative !important;
                            z-index: 20 !important;
                            pointer-events: none !important;
                        }}
                        div.element-container:has(#badge_marker_{m_id}) + div.element-container div.stButton {{
                            height: 100% !important;
                            width: 100% !important;
                            pointer-events: none !important;
                        }}
                        div.element-container:has(#badge_marker_{m_id}) + div.element-container button {{
                            position: absolute !important;
                            top: 8px !important;
                            right: 8px !important;
                            width: 55px !important;
                            height: 26px !important;
                            cursor: pointer !important;
                            pointer-events: auto !important;
                            opacity: 0 !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Render a transparent button strictly over the top-right badge to toggle watch status
                        st.button(" ", key=f"badge_btn_{m_id}", on_click=toggle_watch_cb, args=(m_id, m['watch_status']))
                            
        # Bottom Waterfall (Load More) button inside the scrollable container
        has_more = len(movies_list) > st.session_state.loaded_count
        if has_more:
            if st.button("🔽 " + t("load_more"), use_container_width=True, key="load_more_btn"):
                st.session_state.loaded_count += 36
                st.query_params["loaded_count"] = str(st.session_state.loaded_count)
                st.rerun()

# Right Column - Movie Details & Editor Pane
movie = None
if 'selected_movie_id' in st.session_state:
    movie_db = get_movie_details(st.session_state.selected_movie_id)
    movie = dict(movie_db) if movie_db else None

with col_details:
    # Render fallback web preview if st.dialog is not supported and a preview URL is active
    if not hasattr(st, "dialog") and st.session_state.get("web_preview_url"):
        with st.container(border=True):
            col_web_t, col_web_c = st.columns([8, 2])
            with col_web_t:
                st.markdown(f"🌐 **{st.session_state.web_preview_title}**")
            with col_web_c:
                if st.button("❌ 关闭", key="close_web_preview_fallback", use_container_width=True):
                    st.session_state.web_preview_url = None
                    st.rerun()
            st.components.v1.iframe(st.session_state.web_preview_url, height=500, scrolling=True)
            st.markdown(f'<div style="font-size:0.8rem;opacity:0.8;">💡 如果加载空白，可<a href="{st.session_state.web_preview_url}" target="_blank" style="color:#38BDF8;">点击此处在新窗口打开</a></div>', unsafe_allow_html=True)
            st.divider()

    if not movie:
        st.info(t("select_prompt"))
    else:
        if True:
            st.markdown('<div class="details-panel-marker"></div>', unsafe_allow_html=True)
            if 'auto_match_result' in st.session_state:
                res_status, res_mid = st.session_state.auto_match_result
                if res_mid == movie['id']:
                    if res_status == 'success':
                        st.success("✨ " + ("智能补全影片信息成功！" if st.session_state.lang == 'zh' else "Metadata autocompleted successfully!"))
                    else:
                        st.error("❌ " + ("智能补全影片信息失败，请检查 TMDB Key 或影片名称。" if st.session_state.lang == 'zh' else "Failed to autocomplete metadata. Please check TMDB Key or movie title."))
        
            # Load Cover JPG if exists
            covers_dir = os.path.join(APP_DIR, 'covers')
            cover_file = os.path.join(covers_dir, f"{movie['id']}.jpg")
        
            # Display Movie details in Split view
            col_img, col_info = st.columns([1, 1.8])
        
            with col_img:
                st.markdown('<div class="movie-poster-container">', unsafe_allow_html=True)
                
                # Check local first
                has_shown_img = False
                if os.path.exists(cover_file) and os.path.getsize(cover_file) > 0:
                    try:
                        img = Image.open(cover_file)
                        st.image(img, use_container_width=True)
                        has_shown_img = True
                    except Exception:
                        pass
                
                if not has_shown_img:
                    # Check Google Drive mapping
                    json_path = os.path.join(APP_DIR, 'covers_gdrive.json')
                    file_id = None
                    if os.path.exists(json_path):
                        try:
                            import json
                            with open(json_path, 'r', encoding='utf-8') as f:
                                mapping = json.load(f)
                                file_id = mapping.get(str(movie['id']))
                        except Exception:
                            pass
                    
                    if file_id:
                        # Use super-stable public Drive CDN proxy to enable proxy-free loading inside China
                        gdrive_url = f"https://wsrv.nl/?url=https://drive.google.com/thumbnail?id={file_id}%26sz=w500"
                        st.image(gdrive_url, use_container_width=True)
                    else:
                        st.markdown('<div class="movie-poster-placeholder">🎥</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
                # IMDb & Douban & TMDB ratings as clickable buttons
                imdb_rating_val = f"{movie['imdb_rating']:.1f}" if movie['imdb_rating'] else "N/A"
                douban_rating_val = f"{movie['douban_rating']:.1f}" if movie['douban_rating'] else "N/A"
                
                import urllib.parse
                imdb_url = f"https://www.imdb.com/title/{movie['imdb_id']}/" if movie['imdb_id'] else f"https://www.imdb.com/find?q={urllib.parse.quote(movie['title'])}"
                douban_url = f"https://movie.douban.com/subject/{movie['douban_id']}/" if movie['douban_id'] else f"https://www.douban.com/search?cat=1002&q={urllib.parse.quote(movie['title'])}"
                tmdb_id_val = dict(movie).get('tmdb_id')
                tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id_val}" if tmdb_id_val else f"https://www.themoviedb.org/search?query={urllib.parse.quote(movie['title'])}"
                
                # Render HTML rating buttons side-by-side using flexbox (prevents wrapping and ensures identical design)
                st.markdown(f"""
                <div style="display: flex; gap: 0.35rem; justify-content: space-between; margin-top: 0.6rem; width: 100%;">
                    <a href="{imdb_url}" target="_blank" class="custom-badge badge-imdb" style="text-decoration: none; color: #000000; flex: 1; justify-content: center; white-space: nowrap; font-size: 0.7rem; padding: 0.35rem 0.3rem;">⭐ IMDb {imdb_rating_val}</a>
                    <a href="{douban_url}" target="_blank" class="custom-badge badge-douban" style="text-decoration: none; color: #FFFFFF; flex: 1; justify-content: center; white-space: nowrap; font-size: 0.7rem; padding: 0.35rem 0.3rem;">🟢 豆瓣 {douban_rating_val}</a>
                    <a href="{tmdb_url}" target="_blank" class="custom-badge badge-tmdb" style="text-decoration: none; color: #FFFFFF; flex: 1; justify-content: center; white-space: nowrap; font-size: 0.7rem; padding: 0.35rem 0.3rem;">🎬 {"TMDB" if tmdb_id_val else "TMDB 🔍"}</a>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info:
                # Custom styled title & original title
                orig_title = movie['original_title'] if movie['original_title'] else ""
                title_zh = dict(movie).get('title_zh', '')
                
                if st.session_state.lang == 'zh':
                    # Swap positions in Chinese mode
                    main_display = title_zh if title_zh else "尚未更新中文片名"
                    st.markdown(f'<h2 class="movie-title-header">{main_display}</h2>', unsafe_allow_html=True)
                    st.markdown(f'<p class="movie-orig-title" style="color:#818CF8;">{movie["title"]}</p>', unsafe_allow_html=True)
                    
                    if orig_title and orig_title != movie['title'] and orig_title != title_zh:
                        st.markdown(f'<p class="movie-orig-title">{orig_title}</p>', unsafe_allow_html=True)
                else:
                    # Original logic for English mode
                    st.markdown(f'<h2 class="movie-title-header">{movie["title"]}</h2>', unsafe_allow_html=True)
                    
                    if orig_title and orig_title != movie['title'] and orig_title != title_zh:
                        st.markdown(f'<p class="movie-orig-title">{orig_title}</p>', unsafe_allow_html=True)
                        
                    if not orig_title and not title_zh:
                        st.markdown(f'<p class="movie-orig-title">{t("no_alt_title")}</p>', unsafe_allow_html=True)
                
                # Render Meta Badges
                year_val = movie['year'] if movie['year'] else t("unknown_year")
                runtime_val = f"{movie['runtime']} Mins" if movie['runtime'] else t("unknown_runtime")
                
                # Dynamic translation of multiple countries/regions (comma-separated)
                raw_country = movie['country'] if movie['country'] else ""
                if st.session_state.lang == 'zh' and raw_country:
                    import re
                    parts = [c.strip() for c in re.split(r'[,/]', raw_country) if c.strip()]
                    translated_countries = [get_country_zh(c) for c in parts]
                    country_val = " / ".join(translated_countries)
                else:
                    country_val = raw_country if raw_country else t("unknown_country")
                    
                lang_data = dict(movie).get('original_language', '')
                audio_data = dict(movie).get('languages', '')
                final_lang = lang_data if lang_data else audio_data
                
                if st.session_state.lang == 'zh' and final_lang:
                    import re
                    lang_parts = [l.strip() for l in re.split(r'[,/]', final_lang) if l.strip()]
                    translated_langs = [get_language_zh(l) for l in lang_parts]
                    language_val = " / ".join(translated_langs)
                else:
                    language_val = final_lang if final_lang else t("unknown_language")
                
                st.markdown(f"""
                <div class="badge-container">
                    <span class="custom-badge badge-year">📅 {year_val}</span>
                    <span class="custom-badge badge-runtime">⏱️ {runtime_val}</span>
                    <span class="custom-badge badge-country">🌍 {country_val}</span>
                    <span class="custom-badge badge-language">🗣️ {language_val}</span>
                </div>
                """, unsafe_allow_html=True)
            
                # Director
                st.markdown(f'<p class="movie-metadata-label">{t("director_label")}</p>', unsafe_allow_html=True)
                
                dir_display = movie["director"] if movie["director"] else t("unknown_director")
                if st.session_state.lang == 'zh' and dict(movie).get("director_zh"):
                    dir_display = movie["director_zh"]
                
                st.markdown(f'<p class="movie-metadata-value" style="margin-bottom:0.6rem;">{dir_display}</p>', unsafe_allow_html=True)
            
                # Genres
                st.markdown(f'<p class="movie-metadata-label">{t("genres_label")}</p>', unsafe_allow_html=True)
                # Dynamic translation of genres (comma-separated)
                raw_genres = movie['genres'] if movie['genres'] else ""
                if st.session_state.lang == 'zh' and raw_genres:
                    translated_genres = [GENRE_MAP_ZH.get(g.strip(), g.strip()) for g in raw_genres.split(',')]
                    genres_val = ", ".join(translated_genres)
                else:
                    genres_val = raw_genres if raw_genres else t("unknown_genres")
                st.markdown(f'<p class="movie-metadata-value">{genres_val}</p>', unsafe_allow_html=True)
            
            # Full details down
            st.markdown(f'<p class="movie-metadata-label">{t("plot_label")}</p>', unsafe_allow_html=True)
            plot_display = movie["plot"] if movie["plot"] else t("plot_missing")
            if st.session_state.lang == 'zh' and dict(movie).get("plot_zh"):
                plot_display = movie["plot_zh"]
            st.markdown(f'<p style="color:{text_color};opacity:0.85;font-size:0.92rem;line-height:1.5;margin-bottom:1rem;">{plot_display}</p>', unsafe_allow_html=True)
        
            st.markdown(f'<p class="movie-metadata-label">{t("actors_label")}</p>', unsafe_allow_html=True)
            actors_display = movie["actors"] if movie["actors"] else t("unknown_actors")
            if st.session_state.lang == 'zh' and dict(movie).get("actors_zh"):
                actors_display = movie["actors_zh"]
            st.markdown(f'<p class="movie-metadata-value" style="font-size:0.9rem;margin-bottom:1rem;">{actors_display}</p>', unsafe_allow_html=True)
        
            if not is_cloud:
                st.markdown("---")
                
                # Watch status & Play Button Layout (inline side-by-side)
                is_seen = (movie['watch_status'] == 'Seen')
                status_text = t("status_seen") if is_seen else t("status_unseen")
                status_class = "badge-status-seen" if is_seen else "badge-status-unseen"
                
                col_status, col_play = st.columns([1.2, 2.0], vertical_alignment="bottom")
                with col_status:
                    st.markdown(f"""
                    <p class="movie-metadata-label" style="margin-bottom:0.4rem;">👁️ {t('filter_status')}</p>
                    <div style="margin-bottom:0.1rem;">
                        <span class="custom-badge {status_class}" style="font-size:0.85rem;padding:0.25rem 0.6rem;border-radius:0.25rem;display:inline-block;">{status_text}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_play:
                    is_curr_mac = sys.platform == 'darwin'
                    db_win = movie.get('physical_path') or ""
                    db_mac = movie.get('physical_path_mac') or ""
                    rules = load_path_mappings()
                    
                    active_path = ""
                    if is_curr_mac:
                        # Prioritize db_mac if it exists on disk
                        mac_paths_exist = False
                        if db_mac:
                            mac_paths = [p.strip() for p in db_mac.split(';') if p.strip()]
                            mac_paths_exist = all(exists_case_insensitive(p) for p in mac_paths) if mac_paths else False
                            
                        win_mapped_exist = False
                        win_mapped_mac = ""
                        if db_win:
                            win_mapped_mac = to_mac_path(db_win, rules)
                            win_mapped_paths = [p.strip() for p in win_mapped_mac.split(';') if p.strip()]
                            win_mapped_exist = all(exists_case_insensitive(p) for p in win_mapped_paths) if win_mapped_paths else False
                            
                        if mac_paths_exist:
                            active_path = db_mac
                        elif win_mapped_exist:
                            active_path = win_mapped_mac
                        else:
                            active_path = db_mac if db_mac else win_mapped_mac
                    else:
                        # On Windows
                        win_paths_exist = False
                        if db_win:
                            win_paths = [p.strip() for p in db_win.split(';') if p.strip()]
                            win_paths_exist = all(exists_case_insensitive(p) for p in win_paths) if win_paths else False
                            
                        mac_mapped_exist = False
                        mac_mapped_win = ""
                        if db_mac:
                            mac_mapped_win = to_win_path(db_mac, rules)
                            mac_mapped_paths = [p.strip() for p in mac_mapped_win.split(';') if p.strip()]
                            mac_mapped_exist = all(exists_case_insensitive(p) for p in mac_mapped_paths) if mac_mapped_paths else False
                            
                        if win_paths_exist:
                            active_path = db_win
                        elif mac_mapped_exist:
                            active_path = mac_mapped_win
                        else:
                            active_path = db_win if db_win else mac_mapped_win
                            
                    raw_path = active_path
                    # We render small play buttons inline
                    if raw_path:
                        raw_paths = [p.strip() for p in raw_path.split(';') if p.strip()]
                        # To keep it small, we can put them side by side if there are multiple parts
                        sub_cols = st.columns(len(raw_paths))
                        for p_idx, r_path in enumerate(raw_paths):
                            accessible_path = find_accessible_path(r_path)
                            exists = bool(accessible_path)
                            
                            btn_label = "▶️ 播放影片" if st.session_state.lang == 'zh' else "▶️ Play Movie"
                            if len(raw_paths) > 1:
                                btn_label = f"▶️ 播放 ({p_idx + 1})" if st.session_state.lang == 'zh' else f"▶️ Play ({p_idx + 1})"
                                
                            btn_key = f"play_{movie['id']}_{p_idx}"
                            with sub_cols[p_idx]:
                                if st.button(btn_label, key=btn_key, use_container_width=True, disabled=not exists):
                                    try:
                                        if sys.platform.startswith('win'):
                                            os.startfile(accessible_path)
                                        else:
                                            import subprocess
                                            subprocess.Popen(["open", accessible_path])
                                        st.toast(t("toast_playing", filename=os.path.basename(accessible_path)))
                                    except Exception as e:
                                        st.error(t("error_playback_failed", err=e))
                    else:
                        no_path_lbl = "▶️ 无播放路径" if st.session_state.lang == 'zh' else "▶️ No Path"
                        st.button(no_path_lbl, key=f"play_disabled_{movie['id']}", use_container_width=True, disabled=True)
                
                st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)
                
                # Physical Path (read-only)
                st.markdown(f'<p class="movie-metadata-label">Win 路径</p>' if st.session_state.lang == 'zh' else '<p class="movie-metadata-label">Win Path</p>', unsafe_allow_html=True)
                if db_win:
                    st.code(db_win, language=None)
                else:
                    st.markdown(f'<p class="movie-metadata-value" style="font-style:italic;opacity:0.65;">{t("path_missing")}</p>', unsafe_allow_html=True)
                    
                st.markdown(f'<p class="movie-metadata-label">Mac 路径</p>' if st.session_state.lang == 'zh' else '<p class="movie-metadata-label">Mac Path</p>', unsafe_allow_html=True)
                if db_mac:
                    st.code(db_mac, language=None)
                else:
                    st.markdown(f'<p class="movie-metadata-value" style="font-style:italic;opacity:0.65;">{t("path_missing")}</p>', unsafe_allow_html=True)
                    
                if active_path:
                    mapped_paths = []
                    for r_path in [p.strip() for p in active_path.split(';') if p.strip()]:
                        acc_path = find_accessible_path(r_path)
                        if acc_path and acc_path.lower() != r_path.lower():
                            mapped_paths.append(acc_path)
                    if mapped_paths:
                        mapped_label = "🗺️ 实际挂载路径" if st.session_state.lang == 'zh' else "🗺️ Actual Mount Path"
                        st.markdown(f'<p class="movie-metadata-label" style="margin-top:0.4rem;">{mapped_label}</p>', unsafe_allow_html=True)
                        st.code("; ".join(mapped_paths), language=None)

            # Tabs for operations (Completely hidden in cloud version to enforce read-only status)
            if not is_cloud:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
                col_btn1, col_btn2, col_btn3 = st.columns([1,1,0.5])
                with col_btn1:
                    auto_label = "智能补全" if st.session_state.lang == 'zh' else "Auto Match"
                    if st.button("✨ " + auto_label, use_container_width=True):
                        with st.spinner("正在智能补全影片信息..."):
                            success = autocomplete_movie_metadata_if_needed(movie['id'], movie, force=True)
                        if success:
                            st.session_state.auto_match_result = ('success', movie['id'])
                        else:
                            st.session_state.auto_match_result = ('fail', movie['id'])
                        st.rerun()
                with col_btn2:
                    edit_label = "编辑" if st.session_state.lang == 'zh' else "Edit"
                    if st.button("✏️ " + edit_label, use_container_width=True):
                        st.session_state.edit_target_movie = movie
                        st.session_state.show_movie_edit_dialog = True
                        st.rerun()
                with col_btn3:
                    if st.button("🗑️", use_container_width=True):
                        st.session_state.delete_confirm = movie['id']
                        st.rerun()
                if st.session_state.get('delete_confirm') == movie['id']:
                    st.error(t("delete_confirm_msg"))
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button(t("confirm_btn"), use_container_width=True, type="primary"):
                            delete_movie(movie['id'])
                            st.session_state.selected_movie_id = None
                            if "movie_id" in st.query_params:
                                del st.query_params["movie_id"]
                            del st.session_state['delete_confirm']
                            st.rerun()
                    with cc2:
                        if st.button(t("cancel_btn"), use_container_width=True):
                            del st.session_state['delete_confirm']
                            st.rerun()
                    

