from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
import time
from random import randint
import os
import imageio_ffmpeg

# Configure moviepy to use imageio-ffmpeg
os.environ['IMAGEIO_FFMPEG_EXE'] = imageio_ffmpeg.get_ffmpeg_exe()

SECONDS_PER_POSITION = 4
POSITIONS = [
    {"left": 50, "top": 50}, 
    {"left": 50, "top": 50}, 
    {"left": 50, "top": 50}, 
    {"left": 50, "top": 50} 
]



def get_output_filepath(input_filepath, output_dir=None):
    base_name = os.path.basename(input_filepath)
    name, ext = os.path.splitext(base_name)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_name = f"{name}_{timestamp}_marked{ext}" if ext else f"{name}_{timestamp}_marked"
    if output_dir is not None:
        return os.path.join(output_dir, output_name)
    return os.path.join(os.path.dirname(input_filepath), output_name)


def calculate_margins(video_size, logo_size, position="bottom-right"):
    """Calculate logo position based on specified position mode."""
    # Fixed padding of 15 pixels from corners
    PADDING = 15
    
    left = 0
    top = 0
    
    if position == "top-left":
        left = PADDING
        top = PADDING
    elif position == "top-right":
        left = video_size[0] - PADDING - logo_size[0]
        top = PADDING
    elif position == "bottom-left":
        left = PADDING
        top = video_size[1] - PADDING - logo_size[1]
    elif position == "bottom-right":
        left = video_size[0] - PADDING - logo_size[0]
        top = video_size[1] - PADDING - logo_size[1]
    elif position == "full":
        # Full screen mode - logo covers the entire video
        left = 0
        top = 0
    else:
        # Default to bottom-right
        left = video_size[0] - PADDING - logo_size[0]
        top = video_size[1] - PADDING - logo_size[1]
    
    return (left, top)


def build_logo(logo_filepath, duration, video_size, position="bottom-right", scale=0.2):
    """Build logo clip with specified position and scale."""
    image = ImageClip(logo_filepath).with_duration(duration)
    
    if position == "full":
        # Full screen mode - resize to video dimensions
        image = image.resized(newsize=video_size)
        margins = (0, 0)
    else:
        # Calculate height based on scale (scale is relative to video height)
        height = int(video_size[1] * scale)
        image = image.resized(height=height)
        margins = calculate_margins(video_size, image.size, position)
    
    return image.with_position((margins[0], margins[1])).with_opacity(1)
            


def add_watermark(video_filepath, logo_filepath, output_dir=None, position="bottom-right", scale=0.2):
    """Add watermark to video with specified position and scale."""
    print(f"Loading video: {video_filepath}", flush=True)
    video = VideoFileClip(video_filepath)
    
    # Target dimensions for vertical videos (1080x1920)
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    
    # Crop/resize video to exactly 1080x1920 if needed
    if video.size != (TARGET_WIDTH, TARGET_HEIGHT):
        print(f"Video size {video.size} != target {TARGET_WIDTH}x{TARGET_HEIGHT}, cropping...", flush=True)
        
        # Calculate scaling to cover the target area
        scale_w = TARGET_WIDTH / video.w
        scale_h = TARGET_HEIGHT / video.h
        scale_factor = max(scale_w, scale_h)  # Scale to cover (larger factor)
        
        # Resize video to cover target dimensions
        video_resized = video.resized(scale_factor)
        
        # Calculate crop position (center crop)
        x_center = (video_resized.w - TARGET_WIDTH) / 2
        y_center = (video_resized.h - TARGET_HEIGHT) / 2
        
        # Crop to exact target dimensions
        video = video_resized.cropped(
            x1=x_center,
            y1=y_center,
            width=TARGET_WIDTH,
            height=TARGET_HEIGHT
        )
        print(f"Video cropped to {TARGET_WIDTH}x{TARGET_HEIGHT}", flush=True)

    # For fixed position mode, use a single logo throughout
    print(f"Building logo with position={position}, scale={scale}", flush=True)
    logo = build_logo(logo_filepath, video.duration, video.size, position, scale)

    print(f"Compositing video with logo", flush=True)
    final = CompositeVideoClip([video, logo])
    
    # Ensure fps is set from the original video
    final.fps = video.fps
    
    output_filepath = get_output_filepath(video_filepath, output_dir)
    
    print(f"Starting video encoding to: {output_filepath}", flush=True)
    
    # Write video with proper codec settings
    # moviepy 2.1.2 signature:
    # write_videofile(filename, fps=None, codec=None, bitrate=None, audio=True,
    #                 audio_fps=44100, preset='medium', audio_codec=None, threads=None,
    #                 logger='bar', ...)
    try:
        final.write_videofile(
            output_filepath,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',  # Faster encoding
            threads=4,           # Use 4 threads
            logger=None          # Suppress progress bar output
        )
        print(f"✓ Video encoding completed successfully: {output_filepath}", flush=True)
    except Exception as e:
        print(f"✗ Error writing video file: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise
    finally:
        try:
            video.close()
        except:
            pass
    
    return output_filepath