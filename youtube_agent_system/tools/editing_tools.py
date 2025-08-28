import os
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
    concatenate_audioclips
)
from .. import config

def create_final_video(
    title: str,
    background_video_path: str,
    story_audio_clips_info: list[dict],
    title_audio_clip_info: dict
) -> str | None:
    """
    Assembles the final video, now with a title reveal at the start.
    """
    print("--- Assembling Final Video (with Title Reveal) ---")
    if not story_audio_clips_info or not title_audio_clip_info:
        print("Error: Missing audio clips to create video.")
        return None

    try:
        # --- 1. Load all audio assets ---
        title_audio_clip = AudioFileClip(title_audio_clip_info['audio_path'])
        story_audio_clips = [AudioFileClip(info['audio_path']) for info in story_audio_clips_info]

        # --- 2. Create the full voiceover track (Title + Story) ---
        full_voiceover_track = concatenate_audioclips([title_audio_clip] + story_audio_clips)
        total_duration = full_voiceover_track.duration

        # --- 3. Prepare background video ---
        background_clip = VideoFileClip(background_video_path)
        # Trim or loop background to match the total new duration
        if background_clip.duration > total_duration:
            video_adjusted = background_clip.subclip(0, total_duration)
        else:
            video_adjusted = background_clip.loop(duration=total_duration)

        # Crop to 9:16 aspect ratio
        (w, h) = video_adjusted.size
        target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
        crop_width = h * (target_w / target_h)
        cropped_clip = video_adjusted.crop(x_center=w/2, width=crop_width)
        final_background = cropped_clip.resize(height=target_h)

        # --- 4. Create all text clips (Title + Subtitles) ---
        all_text_clips = []

        # Create the title text clip
        title_text_clip = TextClip(
            txt=title,
            fontsize=config.TEXT_FONT_SIZE,
            color=config.TEXT_COLOR,
            font=config.TEXT_FONT,
            stroke_color=config.TEXT_STROKE_COLOR,
            stroke_width=config.TEXT_STROKE_WIDTH,
            size=(final_background.w * 0.9, None), # Title can be wider
            method='caption'
        )
        title_text_clip = title_text_clip.set_position('center').set_start(0).set_duration(title_audio_clip.duration)
        all_text_clips.append(title_text_clip)

        # Create the story subtitle clips
        current_time = title_audio_clip.duration # Start subtitles after the title audio
        for info in story_audio_clips_info:
            text_clip = TextClip(
                txt=info['text'],
                fontsize=config.TEXT_FONT_SIZE,
                color=config.TEXT_COLOR,
                font=config.TEXT_FONT,
                stroke_color=config.TEXT_STROKE_COLOR,
                stroke_width=config.TEXT_STROKE_WIDTH,
                size=(final_background.w * 0.8, None),
                method='caption'
            )
            text_clip = text_clip.set_position('center').set_start(current_time).set_duration(info['duration'])
            all_text_clips.append(text_clip)
            current_time += info['duration']

        # --- 5. Composite everything ---
        final_clip = CompositeVideoClip([final_background] + all_text_clips)
        final_clip.audio = full_voiceover_track

        # --- 6. Write to file ---
        sanitized_topic = title.replace(' ', '_')[:50] # Shorten for file name
        output_filename = f"final_video_{sanitized_topic}.mp4"
        output_path = os.path.join(config.ASSETS_DIR, output_filename)

        print(f"--- Rendering final video to {output_path} ---")
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=config.VIDEO_FPS)
        print("--- Video rendering complete! ---")

        # --- 7. Clean up ---
        title_audio_clip.close()
        for clip in story_audio_clips:
            clip.close()
        full_voiceover_track.close()
        background_clip.close()
        final_clip.close()

        return output_path

    except Exception as e:
        print(f"An error occurred during video editing: {e}")
        import traceback
        traceback.print_exc()
        return None
