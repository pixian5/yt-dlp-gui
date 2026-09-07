"""Tab creation mixins"""

from .general import GeneralTabMixin
from .network import NetworkTabMixin
from .geo import GeoRestrictionMixin
from .video_selection import VideoSelectionMixin
from .download import DownloadTabMixin
from .filesystem import FilesystemTabMixin
from .video_format import VideoFormatMixin
from .subtitles import SubtitleTabMixin
from .authentication import AuthenticationTabMixin
from .postprocessing import PostprocessingTabMixin
from .thumbnail import ThumbnailTabMixin
from .verbosity import VerbosityTabMixin
from .workarounds import WorkaroundsTabMixin
from .sponsorblock import SponsorblockTabMixin
from .extractor import ExtractorTabMixin
from .advanced import AdvancedTabMixin
from .batch import BatchDownloadMixin
from .playlist import PlaylistTabMixin


__all__ = [
    'AdvancedTabMixin',
    'AuthenticationTabMixin',
    'BatchDownloadMixin',
    'DownloadTabMixin',
    'ExtractorTabMixin',
    'FilesystemTabMixin',
    'GeneralTabMixin',
    'GeoRestrictionMixin',
    'NetworkTabMixin',
    'PlaylistTabMixin',
    'PostprocessingTabMixin',
    'SponsorblockTabMixin',
    'SubtitleTabMixin',
    'ThumbnailTabMixin',
    'VerbosityTabMixin',
    'VideoFormatMixin',
    'VideoSelectionMixin',
    'WorkaroundsTabMixin',
]
