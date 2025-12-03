from dataclasses import dataclass
from pathlib import Path

from networkx import config
import rasterio


@dataclass
class Config:

    dtm_path: Path = None
    correct_magnetic_declinaison: bool = False
    rtk_file_available: bool = False
    cog: bool = False
    image_equalize: bool = False
    global_elevation: bool = False
    lense_correction: bool = True
    nodejgraphical_interface: bool = False
    epsg_code: int = 4326
    center_distance: float = 0.0
    global_target_delta: float = 0.0
    relative_altitude: float = 0.0
    absolute_altitude: float = 0.0
    drone_properties = None
    utm_zone: str = ""
    hemisphere: str = ""
    im_file_name: str = ""
    crs_utm: str = ""
    geo_type: str = "standard"

    def __post_init__(self):
        self.crs_utm = f"+proj=utm +zone={self.utm_zone} +{self.hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        if self.cog :
            self.geo_type = "Cloud Optimized"
        self.dtm_cached = None

    def init_dtm_cache(self):
        """Initialize DTM cache after dtm_path is set"""
        if self.dtm_path and self.dtm_path.exists():
            with rasterio.open(self.dtm_path) as src:
                dtm_data = src.read(1)
                dtm_crs = src.crs
                dtm_transform = src.transform
            self.dtm_cached = (dtm_data, dtm_crs, dtm_transform)



def update_utm_data(self,utm_zone, hemisphere):
    if not utm_zone or not hemisphere:
        raise ValueError("Invalid UTM data.")
    self.crs_utm = f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


