import os
from moviepy import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip,
    concatenate_audioclips,
)
# Correct imports for all class-based effects
from moviepy.video.fx.Crop import Crop
from moviepy.video.fx.Resize import Resize
from moviepy.video.fx.Loop import Loop
from .. import config

def create_final_video(topic: str, background_video_path: str, audio_clips_info: list[dict]) -> str | None:
    """
    Assembles the final video by combining the background, audio, and text subtitles.
    """
    print("--- Assembling Final Video ---")
    if not audio_clips_info:
        print("Error: No audio clips provided to create video.")
        return None

    try:
        # 1. Load assets
        background_clip = VideoFileClip(background_video_path)
        sentence_audio_clips = [AudioFileClip(info['audio_path']) for info in audio_clips_info]

        # 2. Concatenate audio
        voiceover_track = concatenate_audioclips(sentence_audio_clips)
        total_duration = voiceover_track.duration

        # 3. Prepare background video
        (w, h) = background_clip.size
        target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
        
        crop_width = h * (target_w / target_h)
        x_center = w / 2

        # Apply Crop effect
        crop_effect = Crop(x_center=x_center, width=crop_width)
        cropped_clip = crop_effect.apply(background_clip)
        
        # Apply Resize effect
        resize_effect = Resize(height=target_h)
        resized_clip = resize_effect.apply(cropped_clip)

        # Trim or loop the background
        if resized_clip.duration > total_duration:
            video_adjusted = resized_clip.subclip(0, total_duration)
        else:
            # Apply Loop effect
            loop_effect = Loop(duration=total_duration)
            video_adjusted = loop_effect.apply(resized_clip)

        # 4. Create subtitles
        subtitle_clips = []
        current_time = 0
        for info in audio_clips_info:
            text = info['text']
            duration = info['duration']
            
            text_clip = TextClip(
                text=text,
                font_size=config.TEXT_FONT_SIZE,
                color=config.TEXT_COLOR,
                font=config.TEXT_FONT,
                stroke_color=config.TEXT_STROKE_COLOR,
                stroke_width=config.TEXT_STROKE_WIDTH,
                size=(int(video_adjusted.w * 0.8), None),
                method='caption'
            )
            # Renamed all 'set_' methods to 'with_'
            text_clip = text_clip.with_position(config.TEXT_POSITION)
            text_clip = text_clip.with_start(current_time)
            text_clip = text_clip.with_duration(duration)
            
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
