import os
from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
    concatenate_audioclips, CompositeAudioClip
)
from .. import config

def create_final_video(topic: str, background_video_path: str, audio_clips_info: list[dict]) -> str | None:
    """
    Assembles the final video by combining the background, audio, and text subtitles.

    Args:
        topic: The topic of the video, used for naming the final file.
        background_video_path: Path to the downloaded background video.
        audio_clips_info: A list of dictionaries with audio paths, durations, and text.

    Returns:
        The file path of the final rendered video, or None if an error occurs.
    """
    print("--- Assembling Final Video ---")
    if not audio_clips_info:
        print("Error: No audio clips provided to create video.")
        return None

    try:
        # 1. Load background video and audio clips
        background_clip = VideoFileClip(background_video_path)
        sentence_audio_clips = [AudioFileClip(info['audio_path']) for info in audio_clips_info]

        # 2. Concatenate audio clips to get a single voiceover track
        voiceover_track = concatenate_audioclips(sentence_audio_clips)
        total_duration = voiceover_track.duration

        # 3. Prepare background video to match voiceover duration
        # Crop to 9:16 aspect ratio (e.g., for YouTube Shorts)
        (w, h) = background_clip.size
        target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

        # Crop the center of the clip to the target aspect ratio
        crop_width = h * (target_w / target_h)
        x_center = w / 2
        y_center = h / 2

        cropped_clip = background_clip.crop(x_center=x_center, width=crop_width)
        # Resize to the final output resolution
        resized_clip = cropped_clip.resize(height=target_h)

        # Trim or loop the background to match the audio duration
        if resized_clip.duration > total_duration:
            video_adjusted = resized_clip.subclip(0, total_duration)
        else:
            video_adjusted = resized_clip.loop(duration=total_duration)

        # 4. Create timed text clips (subtitles)
        subtitle_clips = []
        current_time = 0
        for info in audio_clips_info:
            text = info['text']
            duration = info['duration']

            text_clip = TextClip(
                txt=text,
                fontsize=config.TEXT_FONT_SIZE,
                color=config.TEXT_COLOR,
                font=config.TEXT_FONT,
                stroke_color=config.TEXT_STROKE_COLOR,
                stroke_width=config.TEXT_STROKE_WIDTH,
                size=(video_adjusted.w*0.8, None), # 80% of video width
                method='caption' # Wraps text automatically
            )

            text_clip = text_clip.set_position(config.TEXT_POSITION)
            text_clip = text_clip.set_start(current_time)
            text_clip = text_clip.set_duration(duration)

            subtitle_clips.append(text_clip)
            current_time += duration
            print(f"Created subtitle: '{text}' from {current_time-duration:.2f}s to {current_time:.2f}s")

        # 5. Composite everything together
        final_clip = CompositeVideoClip([video_adjusted] + subtitle_clips)
        final_clip.audio = voiceover_track

        # 6. Write the final video file
        sanitized_topic = topic.replace(' ', '_')
        output_filename = f"final_video_{sanitized_topic}.mp4"
        output_path = os.path.join(config.ASSETS_DIR, output_filename)

        print(f"--- Rendering final video to {output_path} ---")
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=config.VIDEO_FPS
        )
        print("--- Video rendering complete! ---")

        # Close clips to release memory
        background_clip.close()
        for clip in sentence_audio_clips:
            clip.close()
        voiceover_track.close()
        final_clip.close()

        return output_path

    except Exception as e:
        print(f"An error occurred during video editing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # This is a complex module, direct testing is tricky without assets.
    # It's better to test this via the production_agent.
    print("This module is intended to be called from production_agent.py")
    print("It requires pre-existing video and audio assets to function.")
