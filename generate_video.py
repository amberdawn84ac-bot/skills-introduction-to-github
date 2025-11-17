import os
import subprocess
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont

def generate_chat_bubble_images(script_file, output_dir):
    """
    Generates a series of images, each representing a single chat bubble.
    """
    with open(script_file, 'r') as f:
        lines = f.readlines()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    font = ImageFont.truetype("OpenSans-Regular.ttf", 24)
    for i, line in enumerate(lines):
        speaker, text = line.strip().split(': ', 1)

        # Create a transparent image
        img = Image.new('RGBA', (800, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # Draw the chat bubble
        if speaker.lower() == 'zoe':
            # Blue bubble on the right
            draw.rectangle(((400, 10), (790, 90)), fill=(0, 0, 255, 255), outline='black', width=2)
            draw.text((420, 30), text, fill='white', font=font)
        else:
            # Gray bubble on the left
            draw.rectangle(((10, 10), (400, 90)), fill=(200, 200, 200, 255), outline='black', width=2)
            draw.text((30, 30), text, fill='black', font=font)

        img.save(f'{output_dir}/{i+1}.png')

def create_conversation_video(image_dir, audio_dir, output_video):
    """
    Combines the chat bubble images and audio into a video.
    """
    intermediate_video = 'conversation_video_no_audio.webm'
    if os.path.exists(intermediate_video):
        os.remove(intermediate_video)

    # Create a video from the images
    command = [
        'ffmpeg',
        '-framerate', '1',  # 1 image per second
        '-i', f'{image_dir}/%d.png',
        '-c:v', 'libvpx-vp9',  # Use a codec that supports transparency
        '-pix_fmt', 'yuva420p',
        intermediate_video
    ]
    subprocess.run(command, check=True)

    # Combine the individual audio files
    combined_audio = AudioSegment.empty()
    files = sorted([f for f in os.listdir(audio_dir) if f.endswith('.wav')], key=lambda x: int(x.split('.')[0]))
    for filename in files:
        sound = AudioSegment.from_wav(os.path.join(audio_dir, filename))
        combined_audio += sound
    combined_audio.export('conversation.mp3', format="mp3")

    # Add the audio to the video
    command = [
        'ffmpeg',
        '-y', # Overwrite output files
        '-i', intermediate_video,
        '-i', 'conversation.mp3',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_video.replace('.webm', '.mp4')
    ]
    subprocess.run(command, check=True)

def combine_videos(gameplay_video, conversation_video, output_video):
    """
    Overlays the conversation video onto the gameplay video.
    """
    command = [
        'ffmpeg',
        '-y',
        '-i', gameplay_video,
        '-i', conversation_video,
        '-filter_complex', '[0:v][1:v] overlay=(W-w)/2:(H-h)/2',
        '-c:a', 'copy',
        output_video
    ]
    subprocess.run(command, check=True)

def generate_audio(script_file):
    """
    Generates audio files from a script using the espeak command-line tool.
    """
    with open(script_file, 'r') as f:
        lines = f.readlines()

    if not os.path.exists('audio'):
        os.makedirs('audio')

    for i, line in enumerate(lines):
        speaker, text = line.strip().split(': ', 1)
        voice = 'en-us' if speaker.lower() == 'zoe' else 'en-uk-rp'
        output_file = f'audio/{i+1}.wav'
        command = ['espeak', '-v', voice, '-w', output_file, f'"{text}"']
        subprocess.run(' '.join(command), shell=True, check=True)

if __name__ == '__main__':
    script_file = 'script.txt'
    chat_bubble_dir = 'chat_bubbles'
    audio_dir = 'audio'
    conversation_video = 'conversation_video.mp4'
    gameplay_video = 'gameplay.mp4'
    final_video = 'final_video.mp4'

    generate_chat_bubble_images(script_file, chat_bubble_dir)
    generate_audio(script_file)
    create_conversation_video(chat_bubble_dir, audio_dir, conversation_video)
    combine_videos(gameplay_video, conversation_video, final_video)
