"""Shared field rules for the batch metadata completion dialog."""

import re

BATCH_BASIC_FIELDS = (
    "original_title",
    "genres",
    "year",
    "runtime",
    "country",
    "original_language",
    "languages",
    "imdb_id",
    "tmdb_id",
    "imdb_rating",
)

BATCH_BASIC_MISSING_SQL = """
    original_title IS NULL OR original_title = ''
    OR year IS NULL OR year = 0
    OR genres IS NULL OR genres = ''
    OR imdb_rating IS NULL OR imdb_rating = 0
    OR runtime IS NULL OR runtime = 0
    OR country IS NULL OR country = ''
"""

BASIC_FIELD_CONDITIONS = (
    ("original_title", "(original_title IS NULL OR original_title = '')"),
    ("year", "(year IS NULL OR year = 0)"),
    ("genres", "(genres IS NULL OR genres = '')"),
    ("imdb_rating", "(imdb_rating IS NULL OR imdb_rating = 0)"),
    ("runtime", "(runtime IS NULL OR runtime = 0)"),
    ("country", "(country IS NULL OR country = '')"),
)

EXTRA_FIELD_CONDITIONS = (
    ("title_zh", "(title_zh IS NULL OR title_zh NOT GLOB '*[㐀-鿿]*')"),
    ("plot_zh", "(plot_zh IS NULL OR plot_zh NOT GLOB '*[㐀-鿿]*')"),
    ("plot", "(plot IS NULL OR plot = '')"),
    ("director_zh", "(director_zh IS NULL OR director_zh NOT GLOB '*[㐀-鿿]*')"),
    ("actors_zh", "(actors_zh IS NULL OR actors_zh NOT GLOB '*[㐀-鿿]*')"),
    ("douban_rating", "(douban_rating IS NULL OR douban_rating = 0)"),
)

METADATA_FIELD_CONDITIONS = {
    "original_title": "(original_title IS NULL OR original_title = '')",
    "year": "(year IS NULL OR year = 0)",
    "genres": "(genres IS NULL OR genres = '')",
    "imdb_rating": "(imdb_rating IS NULL OR imdb_rating = 0)",
    "runtime": "(runtime IS NULL OR runtime = 0)",
    "country": "(country IS NULL OR country = '')",
    "director": "(director IS NULL OR director = '')",
    "actors": "(actors IS NULL OR actors = '')",
    "plot": "(plot IS NULL OR plot = '')",
    "title_zh": "(title_zh IS NULL OR title_zh NOT GLOB '*[㐀-鿿]*')",
    "director_zh": "(director_zh IS NULL OR director_zh NOT GLOB '*[㐀-鿿]*')",
    "actors_zh": "(actors_zh IS NULL OR actors_zh NOT GLOB '*[㐀-鿿]*')",
    "plot_zh": "(plot_zh IS NULL OR plot_zh NOT GLOB '*[㐀-鿿]*')",
    "douban_rating": "(douban_rating IS NULL OR douban_rating = 0)",
    "imdb_id": "(imdb_id IS NULL OR imdb_id = '')",
    "tmdb_id": "(tmdb_id IS NULL OR tmdb_id = '')",
}

CHINESE_TEXT_FIELDS = ("title_zh", "director_zh", "actors_zh", "plot_zh")


def is_missing_value(field, value):
    """Chinese fields count as missing unless the value actually contains Chinese."""
    if field in CHINESE_TEXT_FIELDS:
        return not contains_chinese(value)
    return is_empty_value(value)


def contains_chinese(text):
    return bool(re.search(r"[一-鿿]", text or ""))


def is_empty_value(value):
    return value is None or value == "" or value == 0


def missing_field_cond(field, empty_cond):
    """Missing AND not already recorded as a source-less attempt for this field."""
    return (
        f"({empty_cond} AND NOT EXISTS (SELECT 1 FROM batch_field_attempts a "
        f"WHERE a.movie_id = movies.id AND a.field = '{field}'))"
    )


def compose_missing_where(field_conditions):
    return " OR ".join(missing_field_cond(f, c) for f, c in field_conditions)


def build_extra_fill_fields(
    fill_title_zh=False,
    fill_plot_zh=False,
    fill_plot=False,
    fill_dir_zh=False,
    fill_act_zh=False,
    fill_douban_rating=False,
):
    """Return the database fields selected in the supplementary batch tab."""
    fields = []
    if fill_title_zh:
        fields.append("title_zh")
    if fill_plot_zh:
        fields.append("plot_zh")
    if fill_plot:
        fields.append("plot")
    if fill_dir_zh:
        fields.append("director_zh")
    if fill_act_zh:
        fields.append("actors_zh")
    if fill_douban_rating:
        fields.append("douban_rating")
    return tuple(fields)


def filter_batch_fields(fields, allowed_fields):
    """Restrict a proposal to selected fields and discard empty replacement values."""
    allowed = set(allowed_fields or ())
    return {
        key: value
        for key, value in (fields or {}).items()
        if key in allowed and value is not None and value != "" and value != 0
    }
