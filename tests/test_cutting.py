import pytest
from unittest.mock import MagicMock
from core import DownloaderEngine

class TestCuttingLogic:
    @pytest.fixture
    def engine(self):
        e = DownloaderEngine()
        e.execute_ffmpeg_cmd = MagicMock(return_value=(True, "Success"))
        return e

    def test_fast_cut_command(self, engine):
        engine.fast_cut("in.mp4", "out.mp4", "00:00:10", "00:00:20")
        args = engine.execute_ffmpeg_cmd.call_args[0][0]
        # Verify -c copy is present
        assert "-c" in args
        idx = args.index("-c")
        assert args[idx+1] == "copy"
        # Verify input seeking pattern (-ss before -i)
        assert args.index("-ss") < args.index("-i")

    def test_accurate_cut_command(self, engine):
        engine.accurate_cut("in.mp4", "out.mp4", "00:00:10", "00:00:20")
        args = engine.execute_ffmpeg_cmd.call_args[0][0]
        # Verify re-encoding is present (libx264)
        assert "libx264" in args
        # Verify -c copy is NOT present (for video stream)
        if "-c" in args:
             assert args[args.index("-c")+1] != "copy"
        
        # Check specific flags
        assert "-c:v" in args
        assert args[args.index("-c:v")+1] == "libx264"
