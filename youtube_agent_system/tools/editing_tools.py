import os
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
    concatenate_audioclips
)
from moviepy.video.fx.all import crop, resize, loop
from .. import config

def create_final_video(topic: str, background_video_path: str, audio_clips_info: list[dict]) -> str | None:
    """
    Assembles the final video by combining the background, audio, and text subtitles.
    """
    print("--- Assembling Final Video ---")
    if not audio_clips_info:
        return None

    try:
        # 1. Load assets
        background_clip = VideoFileClip(background_video_path)
        sentence_audio_clips = [AudioFileClip(info['audio_path']) for info in audio_clips_info]

        # 2. Concatenate audio
        voiceover_track = concatenate_audioclips(sentence_audio_clips)
        total_duration = voiceover_track.duration

        # 3. Prepare background video with robust cropping and resizing
        source_w, source_h = background_clip.size
        source_ratio = float(source_w) / source_h

        target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
        target_ratio = float(target_w) / target_h

        # This logic correctly handles both portrait and landscape source videos
        if source_ratio > target_ratio:
            # Source video is wider than target (e.g., landscape source for portrait target)
            # We crop the width to match the target aspect ratio
            new_width = int(source_h * target_ratio)
            cropped_clip = crop(background_clip, width=new_width, x_center=source_w/2)
        else:
            # Source video is taller than target (e.g., portrait source for portrait target)
            # We crop the height to match the target aspect ratio
            new_height = int(source_w / target_ratio)
            cropped_clip = crop(background_clip, height=new_height, y_center=source_h/2)
        
        # Resize the now correctly-proportioned clip to the final target dimensions
        resized_clip = resize(cropped_clip, newsize=(target_w, target_h))


        if resized_clip.duration > total_duration:
            video_adjusted = resized_clip.subclip(0, total_duration)
        else:
            video_adjusted = loop(resized_clip, duration=total_duration)

        # 4. Create subtitles
        subtitle_clips = []
        current_time = 0
        for info in audio_clips_info:
            text = info['text']
            duration = info['duration']
            
            text_clip = TextClip(
                text,
                fontsize=config.TEXT_FONT_SIZE,
                color=config.TEXT_COLOR,
                font=config.TEXT_FONT,
                stroke_color=config.TEXT_STROKE_COLOR,
                stroke_width=config.TEXT_STROKE_WIDTH,
                size=(int(video_adjusted.w * 0.9), None), # Use 90% of width for text
                method='caption'
            )
            text_clip = text_clip.set_pos(config.TEXT_POSITION).set_start(current_time).set_duration(duration)
            
            subtitle_clips.append(text_clip)
            current_time += duration
            print(f"Created subtitle: '{text}' from {current_time-duration:.2f}s to {current_time:.2f}s")

        # 5. Composite final video
        final_clip = CompositeVideoClip([video_adjusted] + subtitle_clips)
        final_clip.audio = voiceover_track

        # 6. Write to file
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

        # 7. Close clips
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
    print("This module is intended to be called from production_agent.py")
    print("It requires pre-existing video and audio assets to function.")
