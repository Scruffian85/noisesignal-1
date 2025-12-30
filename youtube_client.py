# --- START OF FILE youtube_client.py (Reverted to Stable Baseline) ---

import os
import pickle
import time
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config import SCOPES, CLIENT_SECRETS_FILE, TOKEN_FILE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def search_videos(youtube, query, max_results, published_after, region_code=None):
    try:
        request_body = {
            'part': "snippet", 'q': query, 'type': "video", 'videoCategoryId': "10",
            'order': "date", 'maxResults': max_results, 'publishedAfter': published_after
        }
        if region_code:
            request_body['regionCode'] = region_code
        response = youtube.search().list(**request_body).execute()
        return response.get("items", [])
    except HttpError as e:
        logging.error(f"An HTTP error occurred during search: {e.content}")
        return []

def fetch_video_and_channel_details(youtube, search_results):
    video_ids = [item['id']['videoId'] for item in search_results if 'videoId' in item.get('id', {})]
    channel_ids = [item['snippet']['channelId'] for item in search_results if 'videoId' in item.get('id', {})]

    videos_by_id = {}
    channels_by_id = {}
    if not video_ids: return videos_by_id, channels_by_id

    try:
        video_response = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(video_ids)).execute()
        videos_by_id = {item['id']: item for item in video_response.get('items', [])}
        channel_response = youtube.channels().list(part="snippet,statistics", id=",".join(list(set(channel_ids)))).execute()
        channels_by_id = {item['id']: item for item in channel_response.get('items', [])}
    except HttpError as e:
        logging.error(f"An HTTP error occurred during batch fetch: {e.content}")
    return videos_by_id, channels_by_id

def get_or_create_playlist(youtube, playlist_id_file, title, description):
    playlist_id = None
    if os.path.exists(playlist_id_file):
        with open(playlist_id_file, "r") as f:
            playlist_id = f.read().strip()
        try:
            youtube.playlists().list(part="id", id=playlist_id).execute()
            logging.info(f"Using existing playlist: {playlist_id}")
        except HttpError:
            playlist_id = None
    if not playlist_id:
        try:
            request = youtube.playlists().insert(part="snippet,status", body={"snippet": {"title": title, "description": description}, "status": {"privacyStatus": "public"}})
            response = request.execute()
            playlist_id = response["id"]
            with open(playlist_id_file, "w") as f: f.write(playlist_id)
            logging.info(f"Created new playlist: {playlist_id}")
        except HttpError as e:
            logging.error(f"Could not create playlist: {e}")
            return None
    return playlist_id

def get_existing_playlist_video_ids(youtube, playlist_id):
    video_ids = set()
    try:
        next_page_token = None
        while True:
            res = youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50, pageToken=next_page_token).execute()
            for item in res.get('items', []):
                video_ids.add(item['snippet']['resourceId']['videoId'])
            next_page_token = res.get('nextPageToken')
            if not next_page_token: break
    except HttpError as e:
        logging.error(f"Error fetching existing playlist items: {e}")
    logging.info(f"Found {len(video_ids)} existing videos in the playlist.")
    return video_ids

def add_videos_to_playlist(youtube, playlist_id, video_ids_to_add):
    if not video_ids_to_add:
        logging.info("No new videos to add to the playlist.")
        return
    logging.info(f"Adding {len(video_ids_to_add)} new videos to the top of playlist {playlist_id}...")
    for video_id in reversed(video_ids_to_add):
        try:
            youtube.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": playlist_id, "position": 0, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
            logging.info(f"Added video {video_id} to playlist.")
            time.sleep(0.5)
        except HttpError as e:
            if "videoNotFound" in str(e.content):
                logging.warning(f"Could not add video {video_id} as it was not found.")
            elif "manualSortRequired" in str(e.content):
                logging.error(f"Playlist sorting is not 'Manual'. Please change sort order on YouTube for playlist {playlist_id} and run again.")
                break
            else:
                logging.error(f"Error adding video {video_id} to playlist: {e}")