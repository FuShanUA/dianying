import re

missing_countries = {
    "Afghanistan": "阿富汗",
    "Albania": "阿尔巴尼亚",
    "Algeria": "阿尔及利亚",
    "Azerbaijan": "阿塞拜疆",
    "Bahamas": "巴哈马",
    "Bosnia And Herzegovina": "波黑",
    "Bosnia and Herzegovina": "波黑",
    "Cambodia": "柬埔寨",
    "Cayman Islands": "开曼群岛",
    "Cuba": "古巴",
    "Cyprus": "塞浦路斯",
    "Czechoslovakia": "捷克斯洛伐克",
    "Dominican Republic": "多米尼加",
    "East Germany": "东德",
    "Ecuador": "厄瓜多尔",
    "Egypt": "埃及",
    "Federal Republic Of Yugoslavia": "南斯拉夫",
    "Fin": "芬兰",
    "Ghana": "加纳",
    "Guatemala": "危地马拉",
    "Isle Of Man": "马恩岛",
    "It": "意大利",
    "Jordan": "约旦",
    "Kazakhstan": "哈萨克斯坦",
    "Kuwait": "科威特",
    "Laos": "老挝",
    "Lebanon": "黎巴嫩",
    "Libya": "利比亚",
    "Liechtenstein": "列支敦士登",
    "Macao SAR China": "中国澳门",
    "Malawi": "马拉维",
    "Malta": "马耳他",
    "Mauritania": "毛里塔尼亚",
    "Monaco": "摩纳哥",
    "Mongolia": "蒙古",
    "Montenegro": "黑山",
    "Nepal": "尼泊尔",
    "Papua New Guinea": "巴布亚新几内亚",
    "Paraguay": "巴拉圭",
    "Philippines": "菲律宾",
    "Puerto Rico": "波多黎各",
    "Republic Of North Macedonia": "北马其顿",
    "Slovenia": "斯洛文尼亚",
    "Sudan": "苏丹",
    "Sw": "瑞典",
    "Tajikistan": "塔吉克斯坦"
}

with open('app.py', 'r') as f:
    content = f.read()

start = content.find('COUNTRY_MAP_ZH = {')
end = content.find('}', start) + 1

# extract existing
existing_str = content[start:end]
import ast
# We can't easily ast.literal_eval because it's an assignment. 
dict_str_only = existing_str.split('=', 1)[1].strip()
old_dict = ast.literal_eval(dict_str_only)

old_dict.update(missing_countries)

dict_str = "COUNTRY_MAP_ZH = {\n"
for k, v in sorted(old_dict.items()):
    dict_str += f'    "{k}": "{v}",\n'
dict_str = dict_str.rstrip(',\n') + "\n}"

new_content = content[:start] + dict_str + content[end:]

with open('app.py', 'w') as f:
    f.write(new_content)
