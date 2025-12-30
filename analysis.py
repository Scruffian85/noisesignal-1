# --- START OF FILE analysis.py (Reverted to Stable Baseline) ---

import logging
import isodate
import math
from config import (
    MIN_VIEW_COUNT, MAX_VIEW_COUNT, MIN_SUBSCRIBER_COUNT, MAX_SUBSCRIBER_COUNT,
    COUNTRY_POPULATIONS, DEFAULT_POPULATION, NEGATIVE_KEYWORDS
)

def parse_duration(duration_str):
    if not duration_str:
        return 0
    try:
        return isodate.parse_duration(duration_str).total_seconds()
    except isodate.ISO8601Error:
        return 0

def is_valid_music_track(video_snippet, video_details):
    title = video_snippet.get('title', '').lower()
    description = video_snippet.get('description', '').lower()

    duration_str = video_details.get('contentDetails', {}).get('duration')
    duration_sec = parse_duration(duration_str)
    if not (90 < duration_sec < 600):
        return False

    if any(keyword in title or keyword in description for keyword in NEGATIVE_KEYWORDS):
        return False

    return True

def calculate_traction_score(video_snippet, video_stats, channel_stats):
    views = int(video_stats.get('viewCount', 0))
    likes = int(video_stats.get('likeCount', 0))
    comments = int(video_stats.get('commentCount', 0))
    subscribers = int(channel_stats.get('subscriberCount', 0))

    if not (MIN_VIEW_COUNT <= views < MAX_VIEW_COUNT): return 0
    if not (MIN_SUBSCRIBER_COUNT <= subscribers < MAX_SUBSCRIBER_COUNT): return 0
    if views == 0: return 0

    log_view_to_sub_ratio = math.log1p(views / subscribers if subscribers > 0 else views)
    like_to_view_ratio = likes / views
    comment_to_view_ratio = comments / views

    if subscribers > 0 and (views / subscribers) < 0.05:
        return 0

    title = video_snippet.get('title', '').lower()
    channel_title = video_snippet.get('channelTitle', '')
    artist_name_words = channel_title.split()
    artist_in_title_bonus = 1.5 if any(word.lower() in title for word in artist_name_words if len(word) > 3) else 1.0

    base_score = (log_view_to_sub_ratio * 0.5) + (comment_to_view_ratio * 150) + (like_to_view_ratio * 50)
    traction_score = base_score * artist_in_title_bonus

    return traction_score

def process_and_score_videos(search_results, videos_by_id, channels_by_id):
    candidate_videos = []
    for item in search_results:
        video_id = item["id"]["videoId"]
        channel_id = item["snippet"]["channelId"]

        video_details = videos_by_id.get(video_id)
        channel_details = channels_by_id.get(channel_id)

        if not video_details or not channel_details:
            continue
        
        if not is_valid_music_track(video_details['snippet'], video_details):
            continue

        traction_score = calculate_traction_score(
            video_details.get('snippet', {}),
            video_details.get('statistics', {}),
            channel_details.get('statistics', {})
        )

        if traction_score > 0:
            country = channel_details['snippet'].get('country', 'unknown')
            population = COUNTRY_POPULATIONS.get(country, DEFAULT_POPULATION)
            log_population_boost = 1 / math.log(population + 1.1)
            final_score = traction_score * log_population_boost

            candidate_videos.append({
                "video_id": video_id,
                "title": video_details['snippet']['title'],
                "artist": channel_details['snippet']['title'],
                "views": int(video_details['statistics'].get('viewCount', 0)),
                "likes": int(video_details['statistics'].get('likeCount', 0)),
                "comments": int(video_details.get('statistics', {}).get('commentCount', 0)),
                "subscribers": int(channel_details['statistics'].get('subscriberCount', 0)),
                "final_score": final_score,
                "country": country
            })
    return candidate_videos