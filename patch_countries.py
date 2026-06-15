import re

file_path = "/Users/shanfu/cc/Projects/movie-database-revival/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add "United States of America" to COUNTRY_MAP_ZH
map_old = """    "United States": "美国",
    "Uruguay": "乌拉圭","""
map_new = """    "United States": "美国",
    "United States of America": "美国",
    "Uruguay": "乌拉圭","""
if map_old in content:
    content = content.replace(map_old, map_new)

# 2. Fix load_countries
load_old = """    countries_set = set()
    for row in rows:
        parts = [c.strip() for c in row['country'].split(',')]
        countries_set.update(parts)
    return sorted(list(countries_set))"""
load_new = """    countries_set = set()
    for row in rows:
        import re
        parts = [c.strip() for c in re.split(r'[,/]', row['country']) if c.strip()]
        countries_set.update(parts)
    return sorted(list(countries_set))"""
content = content.replace(load_old, load_new)

# 3. Fix Details rendering
details_old = """                if st.session_state.lang == 'zh' and raw_country:
                    translated_countries = [COUNTRY_MAP_ZH.get(c.strip(), c.strip()) for c in raw_country.split(',')]
                    country_val = ", ".join(translated_countries)
                else:"""
details_new = """                if st.session_state.lang == 'zh' and raw_country:
                    import re
                    parts = [c.strip() for c in re.split(r'[,/]', raw_country) if c.strip()]
                    translated_countries = [COUNTRY_MAP_ZH.get(c, c) for c in parts]
                    country_val = " / ".join(translated_countries)
                else:"""
content = content.replace(details_old, details_new)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Countries patched.")
