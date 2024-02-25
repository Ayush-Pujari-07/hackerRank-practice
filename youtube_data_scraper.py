import json
import requests
import argparse
import concurrent.futures

from pathlib import Path
from pytube import Playlist, Search
from youtube_transcript_api import YouTubeTranscriptApi


def check_dependencies():
    try:
        import pytube
        import youtube_transcript_api
    except ImportError:
        print("Please install 'pytube' and 'youtube-transcript-api' before running this script.")
        print("You can install them using:")
        print("pip install pytube youtube-transcript-api")
        exit()


def get_transcript(video_id: str) -> str:
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([transcript['text']for transcript in transcript_list])
    except Exception as e:
        print(f"Error: {e}")


def download_video(data: dict):
    try:
        file_name = f"{data['title']}_{data['video_id']}.mp4"
        print(f"File name: {file_name}")
        output_folder = Path("./output")

        # Check if the output folder exists, create it if not
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)

        full_path = output_folder / file_name
        print(f"Full path: {full_path}")
        
        # if full_path.exists():
        #     print(f"Skipping download for {full_path}. File already exists.")
        #     return

        print(f"Downloading file: {file_name}")

        r = requests.get(data['url'][0], stream=True)
        r.raise_for_status()

        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        print(f"{file_name} downloaded!\n")

    except requests.exceptions.RequestException as req_ex:
        print(f"Error in requests: {req_ex}")
    except Exception as e:
        print(f"Error: {e}")


def get_video_metadata(search_data=None, playlist_data=None) -> list:
    metadata = []
    try:
        data_source = search_data if search_data else playlist_data

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for index, result in enumerate(data_source.results if search_data else data_source.videos):
                print(
                    f"Extracting Metadata for video {result.title} - {index + 1} of {len(data_source.results if search_data else data_source.videos)}")
                video_metadata = {
                    'title': result.title,
                    'video_id': result.video_id,
                    'url': [_['url'] for _ in result.streaming_data['formats'] if _['qualityLabel'] == "360p"],
                    'transcript': get_transcript(result.video_id)
                }
                metadata.append(video_metadata)
                futures.append(executor.submit(download_video, video_metadata))
            
            concurrent.futures.wait(futures)
            # Wait for all downloads to complete
            for future in futures:
                future.result()

        return metadata

    except Exception as e:
        print(f"Error: {e}")
        return []


def save_metadata_to_json(metadata: list):
    # convert list of dict to json
    json_metadata = json.dumps(metadata, indent=4)
    # continue with saving json_metadata to file
    with open('metadata.json', 'w') as f:
        f.write(json_metadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, help="Search term")
    parser.add_argument("-p", "--playlist", type=str, help="Playlist URL")
    args = parser.parse_args()

    check_dependencies()

    if args.search:
        search = Search(args.search)
        video_metadata = get_video_metadata(search_data=search)

    if args.playlist:
        playlist = Playlist(args.playlist)
        video_metadata = get_video_metadata(playlist_data=playlist)

    save_metadata_to_json(video_metadata)
    