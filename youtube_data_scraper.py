import os
import requests
import argparse

from pathlib import Path
from pytube import Playlist, Search
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([script['text']for script in transcript])
    except Exception as e:
        print(e)
        pass


def download_video_series(video_metadata: list):
    '''Iterate through all links in video_metadata 
       and download them one by one'''
    try:
        for data in video_metadata:
            # file_name = data['title'] + data['video_id'] + ".mp4"
            file_name = f"{data['title']}_{data['video_id']}.mp4"
            foler_name = "YouTube_videos"

            if os.path.exists(file_name):
                print(
                    f"Skipping download for {file_name}. File already exists.")
                continue

            print(f"Downloading file: {file_name}")

            # create response object
            # Assuming you want the first URL in the list
            r = requests.get(data['url'][0], stream=True)

            # check if the request was successful (status code 200)
            r.raise_for_status()

            # download started
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            print(f"{file_name} downloaded!\n")

    except requests.exceptions.RequestException as req_ex:
        print(f"Error in requests: {req_ex}")
    except Exception as e:
        print(f"Error: {e}")


def get_video_metadata(search_data: object = None, playlist_data: object = None) -> list:
    metadata = []
    try:
        data_source = search_data if search_data else playlist_data

        for index, result in enumerate(data_source.results if search_data else data_source.videos):
            print(
                f"Extracting Metadata for video {index + 1} of {len(data_source.results if search_data else data_source.videos)}")
            video_metadata = {
                'title': result.title,
                'video_id': result.video_id,
                'url': [_['url'] for _ in result.streaming_data['formats'] if _['qualityLabel'] == "360p"],
                'transcript': get_transcript(result.video_id)
            }
            metadata.append(video_metadata)

        return metadata
    except Exception as e:
        print(f"Error: {e}")
        return []
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, help="Search term")
    parser.add_argument("-p", "--playlist", type=str, help="Playlist URL")
    args = parser.parse_args()

    if args.search:
        search = Search(args.search)
    
    if args.playlist:
        playlist = Playlist(args.playlist)

    video_metadata = get_video_metadata(search, playlist)
    download_video_series(video_metadata)