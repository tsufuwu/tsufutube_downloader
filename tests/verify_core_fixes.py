import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Adjust path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.core import DownloaderEngine

class TestYouTubeFixes(unittest.TestCase):
    def setUp(self):
        self.engine = DownloaderEngine()
        self.engine.temp_dir = "."  # Mock temp dir
        
        # [FIX] Ensure yt_dlp is imported so we can patch it
        from modules.core import lazy_import_ytdlp
        try: lazy_import_ytdlp()
        except: pass 
        # Even if import fails (no yt-dlp installed?), we might need to mock the MODULE 'modules.core.yt_dlp' itself, 
        # not just the attribute.
        # But assuming yt-dlp is installed in this env, lazy_import_ytdlp() should populate modules.core.yt_dlp


    def test_ios_client_config(self):
        """Verify iOS client is configured in options"""
        task = {"url": "https://www.youtube.com/watch?v=TpX", "dtype": "video_1080"}
        settings = {}
        callbacks = {}
        
        # We can't easily inspect internal variable 'ydl_opts' inside _download_general_ytdlp 
        # without mocking yt_dlp.YoutubeDL
        with patch('modules.core.yt_dlp.YoutubeDL') as MockYDL:
            self.engine._download_general_ytdlp(task, settings, callbacks)
            
            # Check arguments passed to YoutubeDL constructor
            call_args = MockYDL.call_args[0][0]
            self.assertIn('extractor_args', call_args)
            self.assertEqual(call_args['extractor_args']['youtube']['player_client'], ['ios'])
            print("Verified: iOS client configured.")

    def test_fallback_trigger_on_download_error(self):
        """Verify fallback triggers when process_ie_result raises exception"""
        task = {"url": "https://www.youtube.com/watch?v=TpX", "dtype": "video_1080"}
        settings = {}
        callbacks = MagicMock()
        
        with patch('modules.core.yt_dlp.YoutubeDL') as MockYDL:
            instance = MockYDL.return_value
            instance.__enter__.return_value = instance
            
            # Mock extract_info success
            instance.extract_info.return_value = {'id': 'TpX', 'title': 'Test', 'ext': 'mp4'}
            
            # Mock process_ie_result failure (Download Phase)
            import yt_dlp.utils
            instance.process_ie_result.side_effect = Exception("HTTP Error 403: Forbidden")
            
            # Mock PlaywrightEngine to avoid actual browser launch
            with patch('modules.core.PlaywrightEngine') as MockPW:
                pw_instance = MockPW.return_value
                pw_instance.sniff_video.return_value = {'url': 'http://fallback.com/video.mp4', 'headers': {}}
                
                # Mock manual download (requests) to succeed
                with patch('requests.Session') as MockSession:
                    # .. setup mock response ..
                    mock_resp = MagicMock()
                    mock_resp.status_code = 200
                    mock_resp.headers = {'content-length': '1024'}
                    mock_resp.iter_content.return_value = [b'data']
                    MockSession.return_value.get.return_value.__enter__.return_value = mock_resp
                    
                    # Mock os.path.exists/getsize checks for manual download verification
                    with patch('os.path.exists', return_value=True):
                        with patch('os.path.getsize', return_value=2000):
                             
                            # Run
                            self.engine._download_general_ytdlp(task, settings, callbacks)
                            
                            # Verify Trigger
                            # Check if Playwright was called
                            MockPW.assert_called()
                            print("Verified: Playwright Fallback triggered on Download Error.")

if __name__ == '__main__':
    unittest.main()
