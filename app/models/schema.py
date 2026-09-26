import warnings
from enum import Enum
from typing import Any, List, Literal, Optional, Union

import pydantic
from pydantic import BaseModel, ConfigDict, Field

from app.config import config

# 忽略 Pydantic 的特定警告
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Field name.*shadows an attribute in parent.*",
)

class VideoConcatMode(str, Enum):
    random = "random"
    sequential = "sequential"

class VideoTransitionMode(str, Enum):
    none = None
    shuffle = "Shuffle"
    fade_in = "FadeIn"
    fade_out = "FadeOut"
    slide_in = "SlideIn"
    slide_out = "SlideOut"
    zoom_in = "ZoomIn"
    zoom_out = "ZoomOut"

class VideoAspect(str, Enum):
    landscape = "16:9"
    portrait = "9:16"
    square = "1:1"

    def to_resolution(self):
        if self == VideoAspect.landscape:
            return 1920, 1080
        elif self == VideoAspect.portrait:
            return 1080, 1920
        elif self == VideoAspect.square:
            return 1080, 1080
        raise ValueError(f"unsupported video aspect: {self}")

class VideoFitMode(str, Enum):
    """How source clips with a different aspect ratio fill the output canvas."""
    cover = "cover"
    contain = "contain"

SubtitleDisplayMode = Literal["sentence", "word_by_word"]
SubtitleAnimation = Literal["none", "pop_spring"]
_SUBTITLE_DISPLAY_MODES = ("sentence", "word_by_word")
_SUBTITLE_ANIMATIONS = ("none", "pop_spring")

def _get_valid_ui_choice(key: str, allowed_values: tuple[str, ...], default: str) -> str:
    """
    读取经过校验的 WebUI 枚举配置，兼容旧用户可能残留的无效值。

    请求体由 Pydantic 的 Literal 严格校验，拼写错误会返回明确的字段校验错误；
    配置文件则需要宽容处理，避免用户升级后因为历史手工配置错误导致整个服务
    无法启动。HTTP 状态码由应用统一的校验异常处理器决定，这里不绑定具体数值。
    """
    configured_value = config.ui.get(key, default)
    return configured_value if configured_value in allowed_values else default

_Config = ConfigDict(
    arbitrary_types_allowed=True,
    # Note: ensure your key names match renamed V2 parameters if needed
)

@pydantic.dataclasses.dataclass(config=_Config)
class MaterialInfo:
    provider: str = "pexels"
    url: str = ""
    duration: int = 0
    # 在线素材搜索会附带经过筛选的公开来源信息，供搜索缓存和任务记录复用。
    # 本地上传素材不需要填写；写入任务文件前仍会按字段白名单重新构造，
    # 避免外部请求传入的签名 URL、凭据或无关字段进入持久化数据。
    source_info: Optional[dict[str, Any]] = None

class VideoParams(BaseModel):
    """
    {
    "video_subject": "",
    "video_aspect": "横屏 16:9（西瓜视频）",
    "voice_name": "女生-晓晓",
    "bgm_name": "random",
    "font_name": "MicrosoftYaHeiBold.ttc 黑体-中",
    "text_color": "#FFFFFF",
    "font_size": 60,
    "stroke_color": "#000000",
    "stroke_width": 1.5
    }
    """
    video_subject: str
    video_script: str = ""
    video_terms: Optional[str | list] = None
    video_aspect: Optional[VideoAspect] = VideoAspect.portrait.value
    video_fit_mode: VideoFitMode = VideoFitMode.cover
    video_concat_mode: Optional[VideoConcatMode] = VideoConcatMode.random.value
    video_transition_mode: Optional[VideoTransitionMode] = None
    video_clip_duration: int = Field(default=5, ge=1)
    video_clip_speed: Optional[float] = 1.0
    match_materials_to_script: bool = False
    video_count: int = Field(default=1, ge=1)

    video_source: Optional[str] = "pexels"
    video_materials: Optional[List[MaterialInfo]] = None

    custom_audio_file: Optional[str] = None
    video_language: Optional[str] = ""

    voice_name: Optional[str] = ""
    voice_volume: Optional[float] = 1.0
    voice_rate: Optional[float] = 1.0
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2

    video_music_prompt: str = Field(default="", max_length=2000)
    sonilo_bgm_prompt: str = Field(default="", max_length=2000)

    subtitle_enabled: Optional[bool] = True
    subtitle_position: Optional[str] = config.ui.get("subtitle_position", "bottom")
    subtitle_display_mode: SubtitleDisplayMode = _get_valid_ui_choice(
        "subtitle_display_mode", _SUBTITLE_DISPLAY_MODES, "sentence"
    )
    subtitle_animation: SubtitleAnimation = _get_valid_ui_choice(
        "subtitle_animation", _SUBTITLE_ANIMATIONS, "none"
    )
    custom_position: float = config.ui.get("custom_position", 70.0)

    # FIXED: use a font that exists in resource/fonts
    font_name: Optional[str] = "MicrosoftYaHeiBold.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    
    # Missing fields required by the pipeline:
    paragraph_number: int = Field(default=1, ge=1)
    text_background_color: Optional[str] = None
    stroke_color: Optional[str] = "#000000"
    stroke_width: Optional[float] = 1.5
