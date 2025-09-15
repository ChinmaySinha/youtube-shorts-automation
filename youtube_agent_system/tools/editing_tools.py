# youtube_agent_system/tools/editing_tools.py
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
    (Existing Function - Unchanged)
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

    if background_color:
        final_image = Image.new("RGBA", (img_width, img_height), background_color)
    else:
        final_image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))

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
    story_audio_path: str, # <-- Changed from a list of clips to a single path
    word_timestamps: list[dict], # <-- NEW: Pass the word timestamps
    title_audio_clip_info: dict
) -> str | None:
    """
    (REWRITTEN FUNCTION)
    Assembles the final video with a title card and karaoke-style, word-by-word subtitles.
    """
    print("--- Assembling Final Video (Karaoke Style) ---")
    if not story_audio_path or not title_audio_clip_info:
        print("Error: Missing audio clips to create video.")
        return None

    try:
        # 1. Load audio clips
        title_audio_clip = AudioFileClip(title_audio_clip_info['audio_path'])
        story_audio_clip = AudioFileClip(story_audio_path)
        full_voiceover_track = concatenate_audioclips([title_audio_clip, story_audio_clip])
        
        # 2. Prepare background video
        background_clip = VideoFileClip(background_video_path)
        video_adjusted = background_clip.loop(duration=full_voiceover_track.duration).set_duration(full_voiceover_track.duration)

        (w, h) = video_adjusted.size
        target_w, target_h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
        crop_width = h * (target_w / target_h)
        cropped_clip = video_adjusted.crop(x_center=w/2, width=crop_width)
        final_background = cropped_clip.resize(height=target_h)

        all_text_clips = []
        clip_size = (final_background.w, final_background.h)

        # 3. Create the title reveal (as before)
        title_img = create_stroked_text_image(
            text=title, 
            clip_size=clip_size, 
            font_filename=config.TEXT_FONT, 
            font_size=config.TEXT_FONT_SIZE,
            text_color="white",
            stroke_width=2,
            stroke_color="black",
            text_max_width_ratio=0.95,
            background_color=(0, 0, 0, 255) # Solid black background
        )
        title_text_clip = ImageClip(title_img).set_duration(title_audio_clip.duration)
        all_text_clips.append(title_text_clip)

        # 4. NEW: Create Karaoke-style word clips
        title_duration = title_audio_clip.duration
        for word_info in word_timestamps:
            word = word_info['word']
            start_time = word_info['start'] + title_duration # Offset by title duration
            duration = word_info['duration']

            word_img = create_stroked_text_image(
                text=word, 
                clip_size=clip_size, 
                font_filename=config.TEXT_FONT, 
                font_size=config.TEXT_FONT_SIZE + 20, # Make single words larger
                text_color=config.TEXT_COLOR,
                stroke_width=config.TEXT_STROKE_WIDTH + 1, # Thicker stroke for visibility
                stroke_color=config.TEXT_STROKE_COLOR,
            )
            text_clip = ImageClip(word_img).set_start(start_time).set_duration(duration)
            all_text_clips.append(text_clip)

        # 5. Composite everything together
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