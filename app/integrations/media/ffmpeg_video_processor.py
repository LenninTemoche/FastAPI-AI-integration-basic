"""Procesador de video basado en el binario FFmpeg incluido por imageio-ffmpeg."""

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

from app.core.config import Settings
from app.services.ports.media_provider import (
    ExtractedVideoMedia,
    MediaInputError,
    MediaProcessorUnavailableError,
    MediaProcessingTimeoutError,
)

logger = logging.getLogger(__name__)


class FFmpegVideoProcessor:
    """Extrae hasta N fotogramas y opcionalmente un audio MP3 limitado en duración."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def extract(
        self,
        *,
        content: bytes,
        filename: str,
        include_audio: bool,
    ) -> ExtractedVideoMedia:
        return await asyncio.to_thread(
            self._extract_sync,
            content,
            filename,
            include_audio,
        )

    def _extract_sync(
        self,
        content: bytes,
        filename: str,
        include_audio: bool,
    ) -> ExtractedVideoMedia:
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception as exc:
            logger.error("FFmpeg executable is unavailable")
            raise MediaProcessorUnavailableError from exc

        suffix = Path(filename).suffix.lower()
        if suffix not in {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}:
            suffix = ".mp4"
        interval = self._settings.media_video_frame_interval_seconds
        max_frames = self._settings.media_video_max_frames
        max_duration = self._settings.media_video_max_duration_seconds
        timeout = self._settings.media_processing_timeout_seconds

        with tempfile.TemporaryDirectory(prefix="fastapi-media-") as temp_dir:
            root = Path(temp_dir)
            input_path = root / f"input{suffix}"
            frame_pattern = root / "frame-%03d.jpg"
            input_path.write_bytes(content)
            frame_cmd = [
                ffmpeg_exe, "-nostdin", "-hide_banner", "-loglevel", "error",
                "-protocol_whitelist", "file,pipe", "-i", str(input_path), "-t", str(max_duration), "-map", "0:v:0",
                "-vf", f"fps=1/{interval},scale=640:-2", "-frames:v", str(max_frames),
                "-q:v", "5", "-y", str(frame_pattern),
            ]
            try:
                frame_run = subprocess.run(
                    frame_cmd, capture_output=True, text=True, timeout=timeout, check=False
                )
            except subprocess.TimeoutExpired as exc:
                raise MediaProcessingTimeoutError from exc
            except OSError as exc:
                raise MediaProcessorUnavailableError from exc

            frame_paths = sorted(root.glob("frame-*.jpg"))
            if frame_run.returncode != 0 or not frame_paths:
                # No se exponen detalles de FFmpeg al consumidor: podrían incluir
                # rutas locales o mensajes internos del decodificador.
                logger.info("Video could not be decoded into frames")
                raise MediaInputError(
                    "El archivo de video no pudo decodificarse o no contiene video."
                )
            frames = tuple(path.read_bytes() for path in frame_paths if path.stat().st_size > 0)
            if not frames:
                raise MediaInputError("No se pudieron extraer fotogramas del video.")

            audio_mp3: bytes | None = None
            if include_audio:
                audio_path = root / "audio.mp3"
                audio_cmd = [
                    ffmpeg_exe, "-nostdin", "-hide_banner", "-loglevel", "error",
                    "-protocol_whitelist", "file,pipe", "-i", str(input_path), "-t", str(max_duration), "-map", "0:a:0",
                    "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", "-y",
                    str(audio_path),
                ]
                try:
                    audio_run = subprocess.run(
                        audio_cmd, capture_output=True, text=True, timeout=timeout, check=False
                    )
                    if audio_run.returncode == 0 and audio_path.is_file() and audio_path.stat().st_size:
                        audio_mp3 = audio_path.read_bytes()
                    else:
                        # Pista de audio ausente o no extraíble: el análisis visual aún puede seguir.
                        audio_mp3 = None
                except subprocess.TimeoutExpired as exc:
                    raise MediaProcessingTimeoutError from exc
                except OSError as exc:
                    raise MediaProcessorUnavailableError from exc

        return ExtractedVideoMedia(
            frames=frames,
            audio_mp3=audio_mp3,
            frame_interval_seconds=interval,
        )
