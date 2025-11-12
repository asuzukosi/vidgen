"""
Tests for voiceover_generator module.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from core.voiceover_generator import VoiceoverGenerator, generate_voiceovers


class TestVoiceoverGenerator:
    """Test suite for VoiceoverGenerator class."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_script_data(self):
        """Create sample script data."""
        return {
            'title': 'Test Video',
            'segments': [
                {
                    'title': 'Intro',
                    'script': 'This is the introduction script.',
                    'duration': 10
                },
                {
                    'title': 'Main',
                    'script': 'This is the main content script.',
                    'duration': 15
                }
            ]
        }
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_initialization_gtts(self, mock_init_gtts, temp_output_dir):
        """Test VoiceoverGenerator initialization with gTTS."""
        generator = VoiceoverGenerator(
            provider='gtts',
            output_dir=temp_output_dir
        )
        
        assert generator.provider == 'gtts'
        assert generator.output_dir == temp_output_dir
        mock_init_gtts.assert_called_once()
    
    @patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test_key'})
    @patch('core.voiceover_generator.VoiceoverGenerator._init_elevenlabs')
    def test_initialization_elevenlabs(self, mock_init_elevenlabs, temp_output_dir):
        """Test VoiceoverGenerator initialization with ElevenLabs."""
        generator = VoiceoverGenerator(
            provider='elevenlabs',
            api_key='test_key',
            output_dir=temp_output_dir
        )
        
        assert generator.provider == 'elevenlabs'
        assert generator.api_key == 'test_key'
        mock_init_elevenlabs.assert_called_once()
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_initialization_fallback_to_gtts(self, mock_init_gtts, temp_output_dir):
        """Test fallback to gTTS when ElevenLabs key missing."""
        with patch.dict(os.environ, {}, clear=True):
            generator = VoiceoverGenerator(
                provider='elevenlabs',
                output_dir=temp_output_dir
            )
            
            assert generator.provider == 'gtts'
    
    @patch('core.voiceover_generator.VoiceoverGenerator._generate_segment_audio')
    def test_generate_voiceovers(self, mock_generate_audio, temp_output_dir, sample_script_data):
        """Test generating voiceovers for all segments."""
        mock_generate_audio.return_value = ('/path/to/audio.mp3', 10.5)
        
        with patch('core.voiceover_generator.VoiceoverGenerator._init_gtts'):
            generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
            result = generator.generate_voiceovers(sample_script_data)
        
        assert 'segments' in result
        assert len(result['segments']) == 2
        assert all('audio_file' in s for s in result['segments'])
        assert all('audio_duration' in s for s in result['segments'])
        assert 'total_audio_duration' in result
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_generate_voiceovers_empty_script(self, mock_init_gtts, temp_output_dir):
        """Test handling segments with empty scripts."""
        script_data = {
            'title': 'Test',
            'segments': [
                {
                    'title': 'Empty',
                    'script': '',
                    'duration': 10
                }
            ]
        }
        
        generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
        result = generator.generate_voiceovers(script_data)
        
        # Should handle empty script gracefully
        assert len(result['segments']) == 1
    
    @patch('core.voiceover_generator.gTTS')
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_generate_gtts_audio(self, mock_init_gtts, mock_gtts_class, temp_output_dir):
        """Test generating audio with gTTS."""
        mock_tts = MagicMock()
        mock_gtts_class.return_value = mock_tts
        
        generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
        generator.gtts_class = mock_gtts_class
        
        output_path = os.path.join(temp_output_dir, 'test.mp3')
        duration = generator._generate_gtts_audio("Test script", output_path)
        
        assert duration > 0
        mock_tts.save.assert_called_once_with(output_path)
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_generate_segment_audio(self, mock_init_gtts, temp_output_dir):
        """Test generating audio for a single segment."""
        with patch('core.voiceover_generator.gTTS') as mock_gtts_class:
            mock_tts = MagicMock()
            mock_gtts_class.return_value = mock_tts
            
            generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
            generator.gtts_class = mock_gtts_class
            
            audio_path, duration = generator._generate_segment_audio(
                "Test script text",
                1,
                "Test Segment"
            )
            
            assert os.path.basename(audio_path).startswith('segment_01_')
            assert audio_path.endswith('.mp3')
            assert duration > 0
    
    @patch('core.voiceover_generator.AudioSegment')
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_generate_full_audio(self, mock_init_gtts, mock_audiosegment, temp_output_dir):
        """Test combining segments into full audio."""
        mock_audio = MagicMock()
        mock_audio.__len__ = lambda self: 10000
        mock_audio.__add__ = lambda self, other: self
        mock_audiosegment.empty.return_value = mock_audio
        mock_audiosegment.from_mp3.return_value = mock_audio
        mock_audiosegment.silent.return_value = mock_audio
        
        generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
        
        # Create temp audio files
        audio_file1 = os.path.join(temp_output_dir, 'audio1.mp3')
        audio_file2 = os.path.join(temp_output_dir, 'audio2.mp3')
        
        with open(audio_file1, 'w') as f:
            f.write('fake audio')
        with open(audio_file2, 'w') as f:
            f.write('fake audio')
        
        script_data = {
            'segments': [
                {'audio_file': audio_file1},
                {'audio_file': audio_file2}
            ]
        }
        
        output_path = os.path.join(temp_output_dir, 'full.mp3')
        duration = generator.generate_full_audio(script_data, output_path)
        
        assert duration > 0
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_generate_full_audio_no_pydub(self, mock_init_gtts, temp_output_dir):
        """Test full audio generation without pydub installed."""
        generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
        
        with patch('core.voiceover_generator.AudioSegment', side_effect=ImportError):
            script_data = {'segments': []}
            duration = generator.generate_full_audio(script_data, 'output.mp3')
            
            assert duration == 0.0
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_save_metadata(self, mock_init_gtts, temp_output_dir):
        """Test saving audio metadata to JSON."""
        generator = VoiceoverGenerator(provider='gtts', output_dir=temp_output_dir)
        
        script_data = {
            'title': 'Test',
            'segments': []
        }
        
        output_path = os.path.join(temp_output_dir, 'metadata.json')
        generator.save_metadata(script_data, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            assert loaded['title'] == 'Test'
    
    @patch('core.voiceover_generator.ElevenLabs')
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_init_elevenlabs_success(self, mock_init_gtts, mock_elevenlabs_class):
        """Test successful ElevenLabs initialization."""
        mock_client = MagicMock()
        mock_elevenlabs_class.return_value = mock_client
        
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test_key'}):
            generator = VoiceoverGenerator(provider='elevenlabs', api_key='test_key')
            generator._init_elevenlabs()
            
            assert generator.provider == 'elevenlabs'
    
    @patch('core.voiceover_generator.VoiceoverGenerator._init_gtts')
    def test_init_elevenlabs_import_error(self, mock_init_gtts):
        """Test ElevenLabs initialization with import error."""
        with patch.dict('sys.modules', {'elevenlabs': None}):
            with patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test_key'}):
                generator = VoiceoverGenerator(provider='elevenlabs', api_key='test_key')
                
                # Should fallback to gtts
                assert generator.provider == 'gtts'
    
    @patch('core.voiceover_generator.gTTS')
    def test_init_gtts_success(self, mock_gtts_class):
        """Test successful gTTS initialization."""
        generator = VoiceoverGenerator(provider='gtts')
        
        assert generator.provider == 'gtts'
        assert generator.gtts_class == mock_gtts_class
    
    def test_init_gtts_import_error(self):
        """Test gTTS initialization with import error."""
        with patch.dict('sys.modules', {'gtts': None}):
            with pytest.raises(ImportError):
                generator = VoiceoverGenerator(provider='gtts')
                generator._init_gtts()


class TestGenerateVoiceovers:
    """Test suite for generate_voiceovers convenience function."""
    
    @patch('core.voiceover_generator.VoiceoverGenerator')
    def test_generate_voiceovers_function(self, mock_generator_class):
        """Test convenience function."""
        mock_generator = MagicMock()
        mock_generator.generate_voiceovers.return_value = {'segments': []}
        mock_generator_class.return_value = mock_generator
        
        script_data = {'title': 'Test', 'segments': []}
        result = generate_voiceovers(script_data, 'elevenlabs')
        
        assert 'segments' in result
        mock_generator.generate_voiceovers.assert_called_once()

