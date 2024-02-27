import os
import json
import shutil
import logging
import requests
import argparse
import concurrent.futures

from pytube import Playlist, Search, YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from video_to_image_converter import VideoToImageConverter

# console log
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(lineno)d - %(filename)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
)


def check_dependencies():
    """
    Check if all the dependencies are installed
    """
    try:
        import pytube
        import youtube_transcript_api
    except ImportError:
        print("Please install 'pytube' and 'youtube-transcript-api' before running this script.")
        print("You can install them using:")
        print("pip install pytube youtube-transcript-api")
        exit()


def get_youtube_transcript(video_id: str) -> str:
    """
    Get the transcript of the video
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([transcript['text']for transcript in transcript_list])
    except Exception as e:
        logging.error(f"Error: {e}")


def extract_images(folder_path: str):
    """
    Extract images from the video
    """
    try:
        if not os.path.exists("./Image_dir"):
            os.makedirs("./Image_dir", exist_ok=True)

        if os.listdir(folder_path):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(VideoToImageConverter, video_filepath=os.path.join(
                    folder_path, file), folder_name=os.path.splitext(file)[0], out_dir="./Image_dir", capture_rate=1, save_format=".jpg") for file in os.listdir(folder_path)]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        logging.info(f"File processed: {result}")
                    except Exception as e:
                        logging.info(f"Error processing file: {e}")
    except Exception as e:
        logging.info(f"Error: {e}")


def download_video(folder_path: str, data: dict):
    """
    Download the video
    """
    try:
        logging.info(data['title'])
        file_name = f"{data['video_file_name']}.mp4"
        output_folder = folder_path

        # Check if the output folder exists, create it if not
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)

        full_path = os.path.join(output_folder, file_name)

        logging.info(f"full_path: {full_path}")
        if os.path.exists(full_path):
            logging.info(
                f"Skipping download for {full_path}. File already exists.")
            return

        logging.info(f"Downloading file: {file_name}")
        # logging.info(f"URL: {data['url'][0]}")

        r = requests.get(data['url'][0], stream=True)
        r.raise_for_status()

        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        logging.info(f"{file_name} downloaded!\n")

        # logging.info("Extracting images from the video")
        # extract_images(folder_path)
        # logging.info("Images extracted successfully!")

    except requests.exceptions.RequestException as req_ex:
        logging.error(f"Error in requests: {req_ex}")
    except Exception as e:
        logging.error(f"Error: {e}")


def get_video_metadata(folder_path: str, search_data=None, playlist_data=None, youtube_data=None) -> list:
    """
    Get the metadata of the video
    """
    metadata = []
    try:
        data_source = search_data if search_data else playlist_data

        if youtube_data:
            video_metadata = {
                'title': youtube_data.title,
                'video_id': youtube_data.video_id,
                'video_file_name': f"{youtube_data.title.replace(' ', '_')}_{youtube_data.video_id}",
                'url': [_['url'] for _ in youtube_data.streaming_data['formats'] if _['qualityLabel'] == "360p"],
                'transcript': get_youtube_transcript(youtube_data.video_id)
            }
            download_video(folder_path, video_metadata)
            return [video_metadata]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for index, result in enumerate(data_source.results if search_data else data_source.videos):
                logging.info(
                    f"Extracting Metadata for video {result.title} - {index + 1} of {len(data_source.results if search_data else data_source.videos)}")
                video_metadata = {
                    'title': result.title,
                    'video_id': result.video_id,
                    'video_file_name': f"{result.title.replace(' ', '_')}_{result.video_id}",
                    # quality can be increased or decreased
                    'url': [_['url'] for _ in result.streaming_data['formats'] if _['qualityLabel'] == "360p"],
                    'transcript': get_youtube_transcript(result.video_id)
                }
                metadata.append(video_metadata)
                # logging.info(f"Metadata: {video_metadata}")
                futures.append(executor.submit(
                    download_video, folder_path, video_metadata))

            concurrent.futures.wait(futures)
            # Wait for all downloads to complete
            for future in futures:
                future.result()

        return metadata

    except Exception as e:
        logging.error(f"Error: {e}")
        return []


def save_metadata_to_json(file_name: str = "metadata", metadata: list = []):
    """
    Save the metadata to a json file
    """
    # convert list of dict to json
    json_metadata = json.dumps(metadata, indent=4)
    if not os.path.exists("./metadata"):
        os.makedirs("./metadata")
    # continue with saving json_metadata to file
    with open(f"./metadata/{file_name}.json", 'w') as f:
        f.write(json_metadata)


def delete_folder(folder_path: str):
    """
    Delete a folder and all its contents.
    """
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logging.info(f"Successfully deleted the folder: {folder_path}")
        else:
            logging.warning(f"The folder does not exist: {folder_path}")
    except Exception as e:
        logging.error(
            f"Failed to delete the folder: {folder_path}. Error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, help="Search term")
    parser.add_argument("-p", "--playlist", type=str, help="Playlist URL")
    parser.add_argument("-y", "--youtube", type=str, help="Youtube URL")
    parser.add_argument("-o", "--output", type=str, help="Metadata file name")
    # parser.add_argument("-idir", "--image_dir",
    #                     type=str, help="Image directory")
    args = parser.parse_args()

    check_dependencies()

    folder_path = "./output"

    if args.search:
        search = Search(args.search)
        video_metadata = get_video_metadata(folder_path, search_data=search)

    if args.playlist:
        playlist = Playlist(args.playlist)
        video_metadata = get_video_metadata(
            folder_path, playlist_data=playlist)

    if args.youtube:
        youtube = YouTube(args.youtube)
        video_metadata = get_video_metadata(folder_path, youtube_data=youtube)

    save_metadata_to_json(file_name=args.output, metadata=video_metadata)

    extract_images(folder_path)

    delete_folder(folder_path)


#  python youtube_data_scraper.py --playlist 'https://youtube.com/playlist?list=PLJOFJ3Ok_idupqUbYt2fov6bnCdQpQQtA&si=C5_055Clinc-us46' -o nngroup
