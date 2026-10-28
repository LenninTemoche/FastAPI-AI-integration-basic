"""Prueba de integración de FFmpeg con un MP4 sintético, sin archivos personales ni red."""

import asyncio
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

import httpx

from app.core.config import Settings
from app.modules.media.adapters.ffmpeg_video_processor import FFmpegVideoProcessor


@unittest.skipUnless(
    importlib.util.find_spec("imageio_ffmpeg") is not None,
    "Requiere imageio-ffmpeg (extra media)"
)
class FFmpegVideoProcessorIntegrationTests(unittest.TestCase):
    def test_extracts_bounded_frames_and_audio_from_synthetic_video(self):
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory(prefix="media-test-") as temp_dir:
            video_path = Path(temp_dir) / "synthetic.mp4"
            create_video = [
                ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=2",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-shortest", "-c:v", "mpeg4", "-c:a", "aac", "-y", str(video_path),
            ]
            generated = subprocess.run(create_video, capture_output=True, text=True, timeout=30)
            if generated.returncode != 0:
                self.skipTest("El binario FFmpeg instalado no expone las fuentes de prueba lavfi.")

            settings = Settings(
                _env_file=None,
                media_video_max_duration_seconds=5,
                media_video_max_frames=4,
                media_video_frame_interval_seconds=1,
                media_processing_timeout_seconds=30,
            )
            processor = FFmpegVideoProcessor(settings)
            result = asyncio.run(processor.extract(
                content=video_path.read_bytes(), filename="synthetic.mp4", include_audio=True
            ))
            self.assertGreaterEqual(len(result.frames), 1)
            self.assertLessEqual(len(result.frames), 4)
            self.assertTrue(all(frame.startswith(b"\xff\xd8") for frame in result.frames))
            self.assertIsNotNone(result.audio_mp3)
            self.assertGreater(len(result.audio_mp3 or b""), 100)


if __name__ == "__main__":
    unittest.main()
