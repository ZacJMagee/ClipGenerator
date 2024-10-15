import moviepy.editor as mp
import os
import logging
from moviepy.video.fx.all import crop, resize
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_fps(clip, default_fps=30.0):
    """Ensure the clip has a valid FPS value."""
    if clip.fps is None or not isinstance(clip.fps, (int, float)):
        logging.warning(f"Invalid FPS detected: {clip.fps}. Setting to default: {default_fps}")
        clip.fps = default_fps
    return clip

def smart_crop_for_instagram_reels(clip):
    """Smart crop video clip for Instagram Reels (9:16 aspect ratio, max 1080x1920)"""
    target_aspect_ratio = 9 / 16
    current_aspect_ratio = clip.w / clip.h

    if current_aspect_ratio > target_aspect_ratio:
        # Video is too wide, need to crop width
        new_width = int(clip.h * target_aspect_ratio)
        crop_width = (clip.w - new_width) // 2
        
        # Perform edge detection to find the most interesting part of the frame
        def detect_edges(image):
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
            edges = np.abs(np.diff(gray, axis=1)).sum(axis=0)
            return edges
        
        sample_frame = clip.get_frame(0)
        edges = detect_edges(sample_frame)
        left_crop = min(crop_width, max(0, edges.argmax() - new_width // 2))
        
        clip = crop(clip, x1=left_crop, y1=0, x2=left_crop+new_width, y2=clip.h)
    elif current_aspect_ratio < target_aspect_ratio:
        # Video is too tall, need to crop height
        new_height = int(clip.w / target_aspect_ratio)
        clip = crop(clip, x1=0, y1=(clip.h - new_height) // 2, x2=clip.w, y2=(clip.h + new_height) // 2)

    # Resize to Instagram Reels max dimensions (1080x1920) if larger
    if clip.w > 1080 or clip.h > 1920:
        clip = clip.resize(height=1920) if clip.h > clip.w else clip.resize(width=1080)

    return ensure_fps(clip)

def create_clips(video, min_duration=3, max_duration=15):
    clips = []
    current_time = 0
    while current_time < video.duration:
        remaining_time = video.duration - current_time
        if remaining_time > max_duration:
            clip_duration = max_duration
        elif remaining_time < min_duration:
            if clips:
                clips[-1] = (clips[-1][0], video.duration)
            else:
                clips.append((current_time, video.duration))
            break
        else:
            clip_duration = remaining_time
        
        clips.append((current_time, current_time + clip_duration))
        current_time += clip_duration
    return clips

def process_video(video_path, output_folder):
    logging.info(f"Starting to process video: {video_path}")
    try:
        video = mp.VideoFileClip(video_path)
        video = ensure_fps(video)
        logging.debug(f"Video loaded successfully. Duration: {video.duration} seconds, FPS: {video.fps}")

        # Format video for Instagram Reels
        video = smart_crop_for_instagram_reels(video)
        logging.debug(f"Video formatted for Instagram Reels. New size: {video.size}, FPS: {video.fps}")

        if not os.path.exists(output_folder):
            logging.debug(f"Creating output folder: {output_folder}")
            os.makedirs(output_folder)

        clips = create_clips(video)

        for i, (start, end) in enumerate(clips, 1):
            logging.debug(f"Clip {i}: Start time: {start:.2f}, Duration: {end-start:.2f}")

            clip = video.subclip(start, end)
            clip = ensure_fps(clip, video.fps)

            logging.debug(f"Clip attributes: Duration: {clip.duration}, Size: {clip.size}, FPS: {clip.fps}")
            output_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_clip_{i}.mp4"
            output_path = os.path.join(output_folder, output_filename)
            logging.info(f"Writing clip {i} to {output_path}")

            try:
                logging.debug(f"Attempting to write video with FPS: {clip.fps}")
                clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=clip.fps, preset="slow", 
                                     bitrate="8000k", audio_bitrate="192k", 
                                     threads=4, logger=None, temp_audiofile=None,
                                     ffmpeg_params=["-crf", "18", "-maxrate", "10M", "-bufsize", "15M"])
            except TypeError as e:
                logging.error(f"TypeError when writing clip: {str(e)}")
                try:
                    logging.warning("Attempting to write video without audio...")
                    clip.without_audio().write_videofile(output_path, codec="libx264", fps=clip.fps, preset="slow",
                                                         bitrate="8000k", threads=4, logger=None, temp_audiofile=None,
                                                         ffmpeg_params=["-crf", "18", "-maxrate", "10M", "-bufsize", "15M"])
                except Exception as e:
                    logging.error(f"Failed to write clip even without audio: {str(e)}")
                    raise

        video.close()
        logging.info(f"Finished processing video: {video_path}")
    except Exception as e:
        logging.error(f"Error processing video {video_path}: {str(e)}", exc_info=True)

def process_videos():
    unedited_folder = 'Unedited'  # Path to folder with .MOV files
    edited_folder = 'Edited'  # Path to output folder
    logging.info(f"Looking for videos in folder: {os.path.abspath(unedited_folder)}")

    if not os.path.exists(unedited_folder):
        logging.error(f"The folder '{unedited_folder}' does not exist.")
        return

    video_files = [f for f in os.listdir(unedited_folder) if f.lower().endswith(('.mov', '.mp4'))]

    if not video_files:
        logging.warning(f"No video files found in '{unedited_folder}'.")
        return

    logging.info(f"Found {len(video_files)} video files:")
    for file in video_files:
        logging.info(f" - {file}")

    for filename in video_files:
        video_path = os.path.join(unedited_folder, filename)
        process_video(video_path, edited_folder)

if __name__ == "__main__":
    logging.info("Starting video processing script...")
    logging.info(f"Current working directory: {os.getcwd()}")
    process_videos()
    logging.info("Script execution completed.")
