import os
import json
import argparse
from core.logger import setup_logging, get_logger
from core.config_loader import get_config
from core.script_generator import ScriptGenerator
from core.voiceover_generator import VoiceoverGenerator

setup_logging(log_dir='temp')
logger = get_logger(__name__)


def generate_scripts_and_voiceovers(pdf_path: str, 
                                    use_cached: bool = False, 
                                    provider: str = None):
    """
    generate scripts and voiceovers from video outline.
    args:
        pdf_path: path to pdf file
        use_cached: use cached outline
        provider: voiceover provider (elevenlabs or gtts)
    """
    logger.info("generating scripts and voiceovers")
    
    config = get_config()

    # set temporary directory
    temp_dir = 'temp'
    outline_path = os.path.join(temp_dir, 'video_outline.json')
    
    # load outline
    if not os.path.exists(outline_path):
        logger.error("video outline not found. run test_stage3_content.py first")
        raise ValueError("video outline not found")
    
    with open(outline_path, 'r') as f:
        outline = json.load(f)
    logger.info(f"loaded outline with {len(outline['segments'])} segments")
    
    # generate scripts
    script_gen = ScriptGenerator(api_key=config.openai_api_key)
    script_data = script_gen.generate_script(outline)
    logger.info(f"generated scripts for {len(script_data['segments'])} segments")
    
    # save scripts
    script_path = os.path.join(temp_dir, 'video_script.json')
    text_path = os.path.join(temp_dir, 'video_script.txt')
    script_gen.save_script(script_data, script_path)
    script_gen.export_script_text(script_data, text_path)
    
    
    # generate voiceovers
    voiceover_provider = provider or config.get('voiceover.provider', 'elevenlabs')
    logger.info(f"using provider: {voiceover_provider}")
    
    voiceover_gen = VoiceoverGenerator(
        provider=voiceover_provider,
        api_key=config.elevenlabs_api_key,
        voice_id=config.get('voiceover.voice_id'),
        output_dir=os.path.join(temp_dir, 'audio')
    )
    
    result = voiceover_gen.generate_voiceovers(script_data)
    logger.info(f"generated voiceovers for {len(result['segments'])} segments")
    
    # save result
    audio_metadata_path = os.path.join(temp_dir, 'script_with_audio.json')
    voiceover_gen.save_metadata(result, audio_metadata_path)
    
    # create combined audio
    combined_audio_path = os.path.join(temp_dir, 'full_voiceover.mp3')
    total_duration = voiceover_gen.generate_full_audio(result, combined_audio_path)
    logger.info(f"combined audio generated successfully: {combined_audio_path} ({total_duration:.1f}s)")
    
    logger.info(f"scripts and voiceovers generated successfully")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate narration scripts and voiceover audio for video segments.')
    parser.add_argument("pdf_file", type=str, help="Path to the PDF file")
    parser.add_argument("--use-cached", action="store_true", help="Use previously generated outline")
    parser.add_argument("--provider", type=str, choices=['elevenlabs', 'gtts'], default=None,
                        help="Voiceover provider: elevenlabs or gtts")
    
    args = parser.parse_args()
    pdf_path = args.pdf_file
    use_cached = args.use_cached
    provider = args.provider

    generate_scripts_and_voiceovers(pdf_path, use_cached, provider)
