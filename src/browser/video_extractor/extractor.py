"""Universal Video Extractor - 多平台视频文案提取

支持平台：
- YouTube: 优先使用官方字幕
- 抖音/快手/小红书/B站: 使用 Whisper 语音转文字
- 自动解析短链接
- 繁简转换
"""
import os
import asyncio
import tempfile
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

from loguru import logger


# 尝试导入可选依赖
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    logger.warning("yt-dlp not installed. Audio download will not work.")

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Will use openai-whisper as fallback.")

try:
    import opencc
    OPENCC_AVAILABLE = True
    converter = opencc.OpenCC('t2s')  # 繁体转简体
except ImportError:
    OPENCC_AVAILABLE = False
    logger.warning("opencc not installed. Traditional to Simplified conversion disabled.")


@dataclass
class VideoMetadata:
    """视频元数据"""
    video_id: str = ""
    title: str = ""
    uploader: str = ""
    duration: int = 0
    url: str = ""
    platform: str = "unknown"


@dataclass
class TranscriptSegment:
    """字幕片段"""
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass
class VideoExtractResult:
    """视频提取结果"""
    success: bool
    metadata: VideoMetadata = field(default_factory=VideoMetadata)
    transcript: str = ""
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: str = "unknown"
    is_auto_generated: bool = False
    error: str = ""


class VideoExtractor:
    """
    Universal Video Extractor - 多平台视频文案提取器

    支持：
    - YouTube: 官方字幕
    - 抖音/快手/小红书/B站: Whisper语音转文字
    - 自动短链接解析
    - 繁简转换
    """

    # 短链接域名
    SHORT_DOMAINS = [
        "v.douyin.com",   # 抖音短链
        "b23.tv",         # B站短链
        "xhslink.com",     # 小红书短链
        "youtu.be",        # YouTube短链
    ]

    def __init__(
        self,
        whisper_model: str = "base",
        paragraph_gap: float = 4.0,
        output_dir: str = "./data/audios",
        cookies: Dict[str, str] = None
    ):
        """
        初始化提取器

        Args:
            whisper_model: Whisper模型大小 (tiny/base/small/medium/large)
            paragraph_gap: 段落间隔（秒）
            output_dir: 音频输出目录
            cookies: Cookie字典，用于登录验证
        """
        self.whisper_model = whisper_model
        self.paragraph_gap = paragraph_gap
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookies = cookies or {}
        self._whisper_model = None

    async def resolve_short_url(self, url: str) -> str:
        """
        解析短链接

        Args:
            url: 原始URL

        Returns:
            解析后的完整URL
        """
        url_lower = url.lower()
        if not any(domain in url_lower for domain in self.SHORT_DOMAINS):
            return url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            async with asyncio.timeout(15):
                response = requests.get(
                    url,
                    headers=headers,
                    allow_redirects=False,
                    timeout=15
                )

                if response.status_code in (301, 302, 303, 307, 308):
                    resolved = response.headers.get('Location', url)

                    # 反爬虫检测
                    bad_patterns = ['captcha', 'login', 'explore', 'verification']
                    if any(p in resolved.lower() for p in bad_patterns):
                        logger.warning(f"Anti-bot detected, using original URL: {url}")
                        return url

                    logger.info(f"Resolved short URL: {url} -> {resolved}")
                    return resolved

        except Exception as e:
            logger.warning(f"Failed to resolve short URL {url}: {e}")

        return url

    def detect_platform(self, url: str) -> str:
        """
        检测视频平台

        Args:
            url: 视频URL

        Returns:
            平台名称: youtube/douyin/kuaishou/xiaohongshu/bilibili/other
        """
        url_lower = url.lower()

        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'douyin.com' in url_lower:
            return 'douyin'
        elif 'kuaishou.com' in url_lower:
            return 'kuaishou'
        elif 'xiaohongshu.com' in url_lower or 'xhslink.com' in url_lower:
            return 'xiaohongshu'
        elif 'bilibili.com' in url_lower or 'b23.tv' in url_lower:
            return 'bilibili'
        elif 'weibo.com' in url_lower:
            return 'weibo'
        elif 'zhihu.com' in url_lower:
            return 'zhihu'

        return 'other'

    async def extract(self, url: str, use_whisper: bool = True) -> VideoExtractResult:
        """
        提取视频文案

        Args:
            url: 视频链接
            use_whisper: 是否使用Whisper作为备选

        Returns:
            VideoExtractResult
        """
        try:
            # 1. 解析短链接
            url = await self.resolve_short_url(url)

            # 2. 检测平台
            platform = self.detect_platform(url)

            # 3. 获取元数据
            metadata = await self.get_metadata(url, platform)

            # 4. 提取文案
            segments = []
            language = "zh"  # 默认中文

            if platform == 'youtube':
                # YouTube尝试获取官方字幕
                segments, language = await self._get_youtube_transcript(url)
                if not segments and use_whisper:
                    segments, language = await self._transcribe_with_whisper(url)
            else:
                # 其他平台使用Whisper
                if use_whisper:
                    segments, language = await self._transcribe_with_whisper(url)
                else:
                    return VideoExtractResult(
                        success=False,
                        error=f"Platform {platform} requires Whisper. Install with: pip install faster-whisper"
                    )

            # 5. 合并为段落
            transcript = self._merge_segments(segments)

            # 6. 繁简转换
            if language and language.startswith('zh'):
                transcript = self._to_simplified(transcript)
                metadata.title = self._to_simplified(metadata.title)

            return VideoExtractResult(
                success=True,
                metadata=metadata,
                transcript=transcript,
                segments=segments,
                language=language,
                is_auto_generated=len(segments) > 0 and platform != 'youtube'
            )

        except Exception as e:
            logger.error(f"Video extraction failed: {e}")
            return VideoExtractResult(
                success=False,
                error=str(e)
            )

    async def get_metadata(self, url: str, platform: str = "unknown") -> VideoMetadata:
        """获取视频元数据"""
        metadata = VideoMetadata(url=url, platform=platform)

        if not YT_DLP_AVAILABLE:
            return metadata

        try:
            def sync_extract():
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info

            info = await asyncio.to_thread(sync_extract)

            if info:
                metadata.video_id = info.get('id', '')
                metadata.title = info.get('title', '')
                metadata.uploader = info.get('uploader', info.get('channel', ''))
                metadata.duration = info.get('duration', 0)

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")

        return metadata

    async def _get_youtube_transcript(self, url: str) -> tuple:
        """获取YouTube字幕"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
            )

            # 提取video_id
            video_id = None
            if 'youtube.com' in url:
                import re
                match = re.search(r'v=([a-zA-Z0-9_-]+)', url)
                if match:
                    video_id = match.group(1)
            elif 'youtu.be' in url:
                video_id = url.split('/')[-1].split('?')[0]

            if not video_id:
                return [], "unknown"

            # 获取字幕
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 优先获取中文字幕
            try:
                transcript = transcript_list.find_transcript(['zh', 'zh-CN', 'zh-Hans'])
            except:
                try:
                    transcript = transcript_list.find_transcript(['en'])
                except:
                    transcript = transcript_list[0]

            segments = []
            for seg in transcript.fetch():
                segments.append(TranscriptSegment(
                    text=seg['text'],
                    start=seg['start'],
                    duration=seg['duration']
                ))

            return segments, transcript.language_code

        except Exception as e:
            logger.warning(f"YouTube transcript fetch failed: {e}")
            return [], "unknown"

    async def _transcribe_with_whisper(self, url: str) -> tuple:
        """使用Whisper进行语音转文字"""
        audio_path = None

        try:
            # 1. 下载音频
            audio_path = await self._download_audio(url)

            if not audio_path or not os.path.exists(audio_path):
                raise RuntimeError("Audio download failed")

            # 2. 加载Whisper模型
            model = await self._get_whisper_model()

            # 3. 转录
            if FASTER_WHISPER_AVAILABLE:
                segments, language = await self._transcribe_faster(audio_path, model)
            else:
                segments, language = await self._transcribe_openai(audio_path)

            return segments, language

        finally:
            # 清理临时文件
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

    async def _download_audio(self, url: str) -> Optional[str]:
        """下载视频音频"""
        if not YT_DLP_AVAILABLE:
            return None

        def sync_download():
            output_path = str(self.output_dir / f"temp_{id(url)}.mp3")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path.replace('.mp3', ''),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128',
                }],
                'quiet': True,
                'no_warnings': True,
            }

            # 如果有Cookie，添加到请求头
            if self.cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
                ydl_opts['http_headers'] = {'Cookie': cookie_str}
                logger.info(f"Using cookies for download: {list(self.cookies.keys())}")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # 查找生成的文件
                base = output_path.replace('.mp3', '')
                for ext in ['.mp3', '.m4a', '.wav']:
                    if os.path.exists(base + ext):
                        return base + ext

            except Exception as e:
                logger.error(f"Audio download failed: {e}")

            return None

        return await asyncio.to_thread(sync_download)

    async def _get_whisper_model(self):
        """获取Whisper模型（延迟加载）"""
        if self._whisper_model is None:
            if FASTER_WHISPER_AVAILABLE:
                self._whisper_model = WhisperModel(
                    self.whisper_model,
                    device="cpu",
                    compute_type="int8"
                )
            else:
                import whisper
                self._whisper_model = whisper.load_model(self.whisper_model)

        return self._whisper_model

    async def _transcribe_faster(self, audio_path: str, model) -> tuple:
        """使用faster-whisper转录"""
        segments, info = model.transcribe(
            audio_path,
            language='zh',
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        result_segments = []
        for seg in segments:
            result_segments.append(TranscriptSegment(
                text=seg.text.strip(),
                start=seg.start,
                duration=seg.end - seg.start
            ))

        return result_segments, info.language

    async def _transcribe_openai(self, audio_path: str) -> tuple:
        """使用openai-whisper转录"""
        import whisper

        if self._whisper_model is None:
            self._whisper_model = whisper.load_model(self.whisper_model)

        result = self._whisper_model.transcribe(audio_path, language='zh')

        result_segments = []
        for seg in result['segments']:
            result_segments.append(TranscriptSegment(
                text=seg['text'].strip(),
                start=seg['start'],
                duration=seg['end'] - seg['start']
            ))

        return result_segments, result.get('language', 'zh')

    def _merge_segments(self, segments: List[TranscriptSegment]) -> str:
        """将字幕片段合并为可读的段落文本"""
        if not segments:
            return ""

        paragraphs = []
        current_para = []
        last_end = 0

        for seg in segments:
            # 检查是否需要分段
            if seg.start - last_end > self.paragraph_gap and current_para:
                paragraphs.append(''.join(current_para))
                current_para = []

            current_para.append(seg.text)
            last_end = seg.end

        if current_para:
            paragraphs.append(''.join(current_para))

        return '\n\n'.join(paragraphs)

    def _to_simplified(self, text: str) -> str:
        """繁体转简体"""
        if not OPENCC_AVAILABLE:
            return text

        try:
            return converter.convert(text)
        except Exception:
            return text


# 便捷函数
async def extract_video_text(url: str, whisper_model: str = "base") -> VideoExtractResult:
    """
    提取视频文案

    Args:
        url: 视频链接
        whisper_model: Whisper模型大小

    Returns:
        VideoExtractResult
    """
    extractor = VideoExtractor(whisper_model=whisper_model)
    return await extractor.extract(url)