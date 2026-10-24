# --- START OF FILE main.py (Reverted to Stable Baseline) ---

import pandas as pd
import logging
import os
from collections import OrderedDict
from datetime import datetime
import random

import youtube_client
import analysis
from config import (
    NUM_RANDOM_REGIONS_TO_SEARCH, BASE_SEARCH_QUERIES, COUNTRY_POPULATIONS,
    RESULTS_PER_SEARCH_TASK, PUBLISHED_AFTER, FINAL_PLAYLIST_SIZE,
    PLAYLIST_ID_FILE, PLAYLIST_TITLE, PLAYLIST_DESCRIPTION,
    LOG_LEVEL, LOG_FILE
)

# Enhanced logging configuration
def setup_logging():
    """Set up logging with file and console output."""
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to run the music discovery and playlist update process."""
    setup_logging()
    start_time = datetime.now()
    logging.info("--- Starting Emerging Music Discovery ---")
    logging.info(f"Execution started at: {start_time}")

    try:
        youtube = youtube_client.get_authenticated_service()
        if not youtube:
            logging.error("Failed to authenticate with YouTube API. Exiting.")
            raise Exception("YouTube authentication failed")
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        raise
        
    # --- Simple Dynamic Search Task Builder ---
    search_tasks = []
    
    # 1. Add the high-quality, non-regional base queries
    for query in BASE_SEARCH_QUERIES:
        search_tasks.append({"query": query, "region": None})

    # 2. Add random regional searches for "music"
    available_regions = list(COUNTRY_POPULATIONS.keys())
    selected_regions = random.sample(available_regions, NUM_RANDOM_REGIONS_TO_SEARCH)
    logging.info(f"Selected random regions for genre search: {selected_regions}")
    for region in selected_regions:
        search_tasks.append({"query": "music", "region": region})

    # --- Main Search Loop ---
    all_candidate_videos = []
    quota_exceeded = False
    for task in search_tasks:
        try:
            query = task["query"]
            region = task.get("region")

            log_msg = f"Searching for query: '{query}'"
            if region:
                log_msg += f" in region: {region}"
            logging.info(log_msg)

            search_results = youtube_client.search_videos(
                youtube, query, RESULTS_PER_SEARCH_TASK, PUBLISHED_AFTER, region_code=region
            )

            if not search_results: continue

            videos_by_id, channels_by_id = youtube_client.fetch_video_and_channel_details(youtube, search_results)
            scored_videos = analysis.process_and_score_videos(search_results, videos_by_id, channels_by_id)
            all_candidate_videos.extend(scored_videos)

        except Exception as e:
            error_content = str(getattr(e, 'content', ''))
            if "quotaExceeded" in str(e) or "quotaExceeded" in error_content:
                logging.warning("!!! Quota exceeded! Stopping search phase. Processing videos found so far. !!!")
                quota_exceeded = True
                break
            else:
                logging.error(f"An unexpected error occurred for task {task}: {e}", exc_info=False)
                continue

    if not all_candidate_videos:
        if quota_exceeded:
            raise RuntimeError("YouTube API quota exceeded before any videos were found")
        logging.info("No new candidate videos found in this run. Exiting.")
        return

    unique_videos = list(OrderedDict((v['video_id'], v) for v in all_candidate_videos).values())
    sorted_videos = sorted(unique_videos, key=lambda x: x['final_score'], reverse=True)
    
    final_list = sorted_videos[:FINAL_PLAYLIST_SIZE]

    if not final_list:
        logging.info("No videos made it to the final list after scoring. Exiting.")
        return

    df = pd.DataFrame(final_list)
    df.to_csv("emerging_playlist_results.csv", index=False)
    logging.info(f"Saved {len(df)} new candidate tracks to emerging_playlist_results.csv")
    print("\n--- Top Emerging Tracks Discovered This Run ---")
    cols_to_print = ['title', 'artist', 'country', 'views', 'likes', 'comments', 'subscribers', 'final_score']
    print(df[[col for col in cols_to_print if col in df.columns]].head(10))
    print("-------------------------------------\n")

    try:
        playlist_id = youtube_client.get_or_create_playlist(
            youtube, PLAYLIST_ID_FILE, PLAYLIST_TITLE, PLAYLIST_DESCRIPTION
        )

        if playlist_id:
            existing_video_ids = youtube_client.get_existing_playlist_video_ids(youtube, playlist_id)
            new_videos_df = df[~df['video_id'].isin(existing_video_ids)]
            new_video_ids_to_add = new_videos_df['video_id'].tolist()
            youtube_client.add_videos_to_playlist(youtube, playlist_id, new_video_ids_to_add)
            logging.info(f"Successfully updated playlist: https://www.youtube.com/playlist?list={playlist_id}")

    except Exception as e:
        logging.error(f"An unexpected error occurred during playlist update: {e}", exc_info=True)

    execution_duration = datetime.now() - start_time
    logging.info(f"--- Process Complete ---")
    logging.info(f"Total execution time: {execution_duration}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Execution interrupted by user")
    except Exception as e:
        logging.error(f"Unhandled exception in main: {e}")
        raise