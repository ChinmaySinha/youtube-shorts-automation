import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip,
    concatenate_audioclips
)
from .. import config

# Define the standard Windows emoji font file
EMOJI_FONT_FILENAME = "seguiemj.ttf"

def create_stroked_text_image(text, clip_size, font_filename, font_size, text_color, stroke_width, stroke_color, text_max_width_ratio=0.8, background_color=None):
    """
    Creates an image of text with a stroke, now with an optional solid background color.
    """
    img_width, img_height = clip_size
    text_max_width_pixels = int(img_width * text_max_width_ratio)

    primary_font_path = os.path.join(os.path.dirname(config.__file__), "fonts", font_filename)
    emoji_font_path = os.path.join("C:", os.sep, "Windows", "Fonts", EMOJI_FONT_FILENAME)

    try:
        primary_font = ImageFont.truetype(primary_font_path, font_size)
    except IOError:
        print(f"FATAL ERROR: Primary font not found at {primary_font_path}.")
        return np.zeros((img_height, img_width, 4), dtype=np.uint8)
    
    try:
        emoji_font = ImageFont.truetype(emoji_font_path, font_size)
    except IOError:
        print(f"Warning: Windows Emoji Font not found. Emojis will not be rendered.")
        emoji_font = primary_font

    wrapped_lines = []
    current_line_words = []
    
    def get_text_width_for_font(text_to_measure, font_obj):
        return ImageDraw.Draw(Image.new("RGBA", (1,1))).textbbox((0, 0), text_to_measure, font=font_obj)[2]

    words = text.split(' ')
    for word in words:
        test_line = " ".join(current_line_words + [word])
        if get_text_width_for_font(test_line, primary_font) > text_max_width_pixels and current_line_words:
            wrapped_lines.append(" ".join(current_line_words))
            current_line_words = [word]
        else:
            current_line_words.append(word)
    if current_line_words:
        wrapped_lines.append(" ".join(current_line_words))

    # --- UPDATED: Create image with optional background ---
    if background_color:
        final_image = Image.new("RGBA", (img_width, img_height), background_color)
    else:
        final_image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0)) # Transparent

    final_draw = ImageDraw.Draw(final_image)

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251" 
        "]+")

    
    LINE_SPACING_MULTIPLIER = 1.2
    line_height = (primary_font.getbbox("Tg")[3] - primary_font.getbbox("Tg")[1]) * LINE_SPACING_MULTIPLIER
    total_text_block_height = len(wrapped_lines) * line_height
    block_start_y = (img_height - total_text_block_height) / 2

    for i, line in enumerate(wrapped_lines):
        parts = emoji_pattern.split(line)
        emojis = emoji_pattern.findall(line)
        
        total_line_width = 0
        for part in parts:
            total_line_width += get_text_width_for_font(part, primary_font)
        for emoji in emojis:
            total_line_width += get_text_width_for_font(emoji, emoji_font)

        current_x = (img_width - total_line_width) / 2
        current_y = block_start_y + (i * line_height)

        for j, part in enumerate(parts):
            for x_offset in range(-stroke_width, stroke_width + 1):
                for y_offset in range(-stroke_width, stroke_width + 1):
                    if x_offset**2 + y_offset**2 <= stroke_width**2:
                        final_draw.text((current_x + x_offset, current_y + y_offset), part, font=primary_font, fill=stroke_color)
            final_draw.text((current_x, current_y), part, font=primary_font, fill=text_color)
            current_x += get_text_width_for_font(part, primary_font)

            if j < len(emojis):
                emoji = emojis[j]
                final_draw.text((current_x, current_y), emoji, font=emoji_font)
                current_x += get_text_width_for_font(emoji, emoji_font)
    
    return np.array(final_image)

def create_final_video(
    title: str,
    background_video_path: str,
    story_audio_clips_info: list[dict],
    title_audio_clip_info: dict
) -> str | None:
    """
    Assembles the final video with special formatting for the title.
    """
    print("--- Assembling Final Video ---")
    if not story_audio_clips_info or not title_audio_clip_info:
        print("Error: Missing audio clips to create video.")
        return None

    try:
        title_audio_clip = AudioFileClip(title_audio_clip_info['audio_path'])
        story_audio_clips = [AudioFileClip(info['audio_path']) for info in story_audio_clips_info]
        full_voiceover_track = concatenate_audioclips([title_audio_clip] + story_audio_clips)
        
        background_clip = VideoFileClip(background_video_path)
        video_adjusted = background_clip.loop(duration=full_voiceover_track.duration).set_duration(full_voiceover_track.duration)

        (w, h) = video_adjusted.size
        target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
        crop_width = h * (target_w / target_h)
        cropped_clip = video_adjusted.crop(x_center=w/2, width=crop_width)
        final_background = cropped_clip.resize(height=target_h)

        all_text_clips = []
        clip_size = (final_background.w, final_background.h)
        text_max_width_ratio = 0.8

        # --- CREATE THE TITLE WITH A SOLID BLACK BACKGROUND ---
        title_img = create_stroked_text_image(
            text=title, 
            clip_size=clip_size, 
            font_filename=config.TEXT_FONT, 
            font_size=config.TEXT_FONT_SIZE,
            text_color="white",         # Override color to white for title
            stroke_width=2,             # A thinner stroke looks better on a solid background
            stroke_color="black",
            text_max_width_ratio=0.95,
            background_color=(0, 0, 0, 255) # RGBA for solid (100% opaque) black
        )
        title_text_clip = ImageClip(title_img).set_duration(title_audio_clip.duration)
        all_text_clips.append(title_text_clip)

        # --- CREATE SUBTITLES WITH TRANSPARENT BACKGROUND ---
        current_time = title_audio_clip.duration
        for info in story_audio_clips_info:
            text_img = create_stroked_text_image(
                text=info['text'], 
                clip_size=clip_size, 
                font_filename=config.TEXT_FONT, 
                font_size=config.TEXT_FONT_SIZE,
                text_color=config.TEXT_COLOR,         # Use the cyan color from config
                stroke_width=config.TEXT_STROKE_WIDTH, # Use the thick stroke from config
                stroke_color=config.TEXT_STROKE_COLOR,
                text_max_width_ratio=text_max_width_ratio
                # No background_color is passed, so it will be transparent by default
            )
            text_clip = ImageClip(text_img).set_start(current_time).set_duration(info['duration'])
            all_text_clips.append(text_clip)
            current_time += info['duration']

        final_clip = CompositeVideoClip([final_background] + all_text_clips)
        final_clip.audio = full_voiceover_track

        if hasattr(config, 'VIDEO_SPEED') and config.VIDEO_SPEED > 1.0:
            print(f"Speeding up final video to {config.VIDEO_SPEED}x")
            final_clip = final_clip.speedx(config.VIDEO_SPEED)

        safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')[:50]
        output_filename = f"final_video_{safe_title}.mp4"
        output_path = os.path.join(config.ASSETS_DIR, output_filename)

        print(f"--- Rendering final video to {output_path} ---")
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=config.VIDEO_FPS)
        print("--- Video rendering complete! ---")

        return output_path

    except Exception as e:
        print(f"An error occurred during video editing: {e}")
        import traceback
        traceback.print_exc()
        return None