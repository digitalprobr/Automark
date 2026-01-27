import os
import time
from marker import add_watermark

inp = os.path.join('storage', 'inputs', 'test_video.mp4')
logo = os.path.join('storage', 'logos', 'test_logo.png')
outdir = os.path.join('storage', 'outputs')

threads_list = [1, 2, 4]

for threads in threads_list:
    os.environ['FFMPEG_THREADS'] = str(threads)
    start = time.time()
    try:
        out = add_watermark(inp, logo, output_dir=outdir, position='bottom-right', scale=0.2)
        dur = time.time() - start
        print(f"threads={threads} -> output={out} time={dur:.2f}s")
    except Exception as e:
        dur = time.time() - start
        print(f"threads={threads} -> ERROR after {dur:.2f}s: {e}")
