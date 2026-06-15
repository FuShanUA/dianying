import sys
import os
sys.path.append(os.getcwd())
from app import update_movie_fields, get_movie_details, get_db_connection
movie_id = 480
existing = get_movie_details(movie_id)
print(f"Before: title_zh='{existing['title_zh']}'")
update_movie_fields(movie_id, {'title_zh': " "})
after = get_movie_details(movie_id)
print(f"After : title_zh='{after['title_zh']}'")
