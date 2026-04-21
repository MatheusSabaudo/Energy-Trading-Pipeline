from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config import userdata_config as cfg


MONTHLY_NORMALS = {
    "temp_mean_c": [2.8, 4.7, 8.9, 12.8, 17.2, 21.1, 23.9, 23.3, 19.2, 13.7, 8.0, 3.7],
    "temp_min_c": [-0.6, 0.5, 3.8, 7.5, 11.8, 15.7, 18.4, 18.0, 14.4, 9.2, 4.0, 0.3],
    "temp_max_c": [6.3, 9.0, 14.0, 18.0, 22.7, 26.8, 29.8, 29.2, 24.2, 18.1, 11.8, 6.8],
    "humidity_pct": [80, 76, 71, 69, 70, 68, 67, 69, 74, 78, 82, 83],
    "cloud_cover_pct": [61, 56, 52, 51, 54, 46, 36, 38, 45, 54, 60, 63],
    "wind_speed_kmh": [7.8, 7.6, 8.1, 8.0, 7.2, 6.5, 6.0, 5.8, 6.1, 6.4, 6.8, 7.2],
}


class EuropeRomeFallbackTZ(tzinfo):
    """Fallback timezone for Europe/Rome when tzdata is unavailable."""

    def _last_sunday(self, year: int, month: int) -> datetime:
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        current = next_month - timedelta(days=1)
        while current.weekday() != 6:
            current -= timedelta(days=1)
        return current

    def _dst_window_utc(self, year: int) -> tuple[datetime, datetime]:
        dst_start_local = self._last_sunday(year, 3).replace(hour=2)
        dst_end_local = self._last_sunday(year, 10).replace(hour=3)
        dst_start_utc = dst_start_local - timedelta(hours=1)
        dst_end_utc = dst_end_local - timedelta(hours=2)
        return dst_start_utc, dst_end_utc

    def _is_dst(self, dt: datetime | None) -> bool:
        if dt is None:
            return False
        naive = dt.replace(tzinfo=None)
        dst_start_utc, dst_end_utc = self._dst_window_utc(naive.year)

        if dt.tzinfo is self:
            winter_candidate_utc = naive - timedelta(hours=1)
            summer_candidate_utc = naive - timedelta(hours=2)

            if dst_start_utc <= summer_candidate_utc < dst_end_utc:
                return True
            if dst_start_utc <= winter_candidate_utc < dst_end_utc and naive.hour >= 3:
                return True
            return False

        if dt.tzinfo is timezone.utc:
            utc_naive = naive
        else:
            utc_naive = (dt - (dt.utcoffset() or timedelta(0))).replace(tzinfo=None)

        return dst_start_utc <= utc_naive < dst_end_utc

    def utcoffset(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=2 if self._is_dst(dt) else 1)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(hours=1 if self._is_dst(dt) else 0)

    def tzname(self, dt: datetime | None) -> str:
        return "CEST" if self._is_dst(dt) else "CET"

    def fromutc(self, dt: datetime) -> datetime:
        standard_time = (dt + timedelta(hours=1)).replace(tzinfo=self)
        if self._is_dst(standard_time):
            return (dt + timedelta(hours=2)).replace(tzinfo=self)
        return standard_time


@dataclass(frozen=True)
class TurinSimulationConfig:
    city: str = cfg.LOCATION_PARAMS["city"]
    latitude: float = cfg.LOCATION_PARAMS["latitude"]
    longitude: float = cfg.LOCATION_PARAMS["longitude"]
    timezone: str = cfg.LOCATION_PARAMS["timezone"]
    system_size_kw: float = cfg.PANEL_PARAMS["panel_power_kw"]
    panel_tilt_deg: float = cfg.SIMULATION_PARAMS["panel_tilt_deg"]
    panel_azimuth_deg: float = cfg.SIMULATION_PARAMS["panel_azimuth_deg"]
    temp_coefficient: float = cfg.PANEL_PARAMS["temp_loss_coeff"]
    derating_factor: float = cfg.LOSS_PARAMS.get("derating_factor", 0.85)
    noct_c: float = cfg.SIMULATION_PARAMS["nominal_operating_cell_temp_c"]
    albedo: float = cfg.SIMULATION_PARAMS["albedo"]
    site_calibration_factor: float = cfg.SIMULATION_PARAMS["site_calibration_factor"]
    seed: int = cfg.SIMULATION_PARAMS["seed"]

    @property
    def tzinfo(self) -> tzinfo:
        try:
            return ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            if self.timezone == "Europe/Rome":
                return EuropeRomeFallbackTZ()
            raise


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def stable_noise(*parts: object, low: float = -1.0, high: float = 1.0) -> float:
    key = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(key).digest()
    fraction = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
    return low + (high - low) * fraction


def interpolate_monthly_value(values: list[float], timestamp: datetime) -> float:
    month_index = timestamp.month - 1
    next_index = (month_index + 1) % 12
    days_in_month = (timestamp.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    fraction = ((timestamp.day - 1) + timestamp.hour / 24) / days_in_month.day
    return values[month_index] + (values[next_index] - values[month_index]) * fraction


def solar_position(timestamp: datetime, latitude: float, longitude: float) -> dict[str, float]:
    n = timestamp.timetuple().tm_yday
    fractional_hour = timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600
    b = math.radians((360 / 364) * (n - 81))
    equation_of_time = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    utc_offset_hours = timestamp.utcoffset().total_seconds() / 3600 if timestamp.utcoffset() else 0
    local_standard_meridian = 15 * utc_offset_hours
    time_correction = 4 * (longitude - local_standard_meridian) + equation_of_time
    local_solar_time = fractional_hour + time_correction / 60

    hour_angle_deg = 15 * (local_solar_time - 12)
    declination_deg = 23.45 * math.sin(math.radians(360 * (284 + n) / 365))

    latitude_rad = math.radians(latitude)
    declination_rad = math.radians(declination_deg)
    hour_angle_rad = math.radians(hour_angle_deg)

    cos_zenith = (
        math.sin(latitude_rad) * math.sin(declination_rad)
        + math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle_rad)
    )
    cos_zenith = clamp(cos_zenith, -1.0, 1.0)
    zenith_rad = math.acos(cos_zenith)
    elevation_deg = 90 - math.degrees(zenith_rad)

    sin_azimuth = -math.sin(hour_angle_rad) * math.cos(declination_rad)
    cos_azimuth = (
        math.sin(declination_rad) * math.cos(latitude_rad)
        - math.cos(declination_rad) * math.sin(latitude_rad) * math.cos(hour_angle_rad)
    ) / max(math.cos(zenith_rad), 1e-6)
    azimuth_deg = (math.degrees(math.atan2(sin_azimuth, cos_azimuth)) + 180) % 360

    return {
        "day_of_year": n,
        "equation_of_time_min": equation_of_time,
        "declination_deg": declination_deg,
        "hour_angle_deg": hour_angle_deg,
        "zenith_deg": math.degrees(zenith_rad),
        "elevation_deg": elevation_deg,
        "azimuth_deg": azimuth_deg,
        "solar_factor": max(0.0, math.sin(math.radians(max(elevation_deg, 0.0)))),
    }


def clear_sky_irradiance_wm2(cos_zenith: float) -> float:
    if cos_zenith <= 0:
        return 0.0
    return 1098 * cos_zenith * math.exp(-0.059 / cos_zenith)


def uv_index_from_conditions(solar_factor: float, cloud_cover_pct: float) -> float:
    if solar_factor <= 0:
        return 0.0
    cloud_transmittance = 1 - 0.55 * ((cloud_cover_pct / 100) ** 2.2)
    return round(clamp(11 * (solar_factor**1.25) * cloud_transmittance, 0.0, 10.5), 1)


def plane_of_array_irradiance(
    ghi_wm2: float,
    solar_factor: float,
    declination_deg: float,
    hour_angle_deg: float,
    latitude_deg: float,
    tilt_deg: float,
    azimuth_from_south_deg: float,
    cloud_cover_pct: float,
    albedo: float,
) -> float:
    if ghi_wm2 <= 0 or solar_factor <= 0:
        return 0.0

    latitude_rad = math.radians(latitude_deg)
    declination_rad = math.radians(declination_deg)
    hour_angle_rad = math.radians(hour_angle_deg)
    tilt_rad = math.radians(tilt_deg)
    surface_azimuth_rad = math.radians(azimuth_from_south_deg)

    cos_zenith = solar_factor
    cos_incidence = (
        math.sin(declination_rad) * math.sin(latitude_rad) * math.cos(tilt_rad)
        - math.sin(declination_rad) * math.cos(latitude_rad) * math.sin(tilt_rad) * math.cos(surface_azimuth_rad)
        + math.cos(declination_rad) * math.cos(latitude_rad) * math.cos(tilt_rad) * math.cos(hour_angle_rad)
        + math.cos(declination_rad) * math.sin(latitude_rad) * math.sin(tilt_rad) * math.cos(surface_azimuth_rad) * math.cos(hour_angle_rad)
        + math.cos(declination_rad) * math.sin(tilt_rad) * math.sin(surface_azimuth_rad) * math.sin(hour_angle_rad)
    )
    cos_incidence = max(0.0, cos_incidence)

    diffuse_fraction = clamp(0.22 + 0.42 * (cloud_cover_pct / 100), 0.18, 0.72)
    diffuse_horizontal = ghi_wm2 * diffuse_fraction
    beam_horizontal = max(0.0, ghi_wm2 - diffuse_horizontal)
    beam_ratio = cos_incidence / max(cos_zenith, 1e-6)

    beam_tilted = beam_horizontal * beam_ratio
    diffuse_tilted = diffuse_horizontal * (1 + math.cos(tilt_rad)) / 2
    ground_reflected = ghi_wm2 * albedo * (1 - math.cos(tilt_rad)) / 2

    return max(0.0, beam_tilted + diffuse_tilted + ground_reflected)


def simulate_hour(
    timestamp: datetime,
    config: TurinSimulationConfig | None = None,
    daily_cloud_state: float | None = None,
) -> dict[str, float | int | str]:
    config = config or TurinSimulationConfig()
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=config.tzinfo)
    else:
        timestamp = timestamp.astimezone(config.tzinfo)

    position = solar_position(timestamp, config.latitude, config.longitude)
    day_of_year = position["day_of_year"]
    solar_factor = position["solar_factor"]

    mean_temp = interpolate_monthly_value(MONTHLY_NORMALS["temp_mean_c"], timestamp)
    min_temp = interpolate_monthly_value(MONTHLY_NORMALS["temp_min_c"], timestamp)
    max_temp = interpolate_monthly_value(MONTHLY_NORMALS["temp_max_c"], timestamp)
    mean_humidity = interpolate_monthly_value(MONTHLY_NORMALS["humidity_pct"], timestamp)
    mean_cloud = interpolate_monthly_value(MONTHLY_NORMALS["cloud_cover_pct"], timestamp)
    mean_wind = interpolate_monthly_value(MONTHLY_NORMALS["wind_speed_kmh"], timestamp)

    daily_temp_shift = stable_noise(config.seed, timestamp.date(), "temp", low=-3.5, high=3.5)
    hourly_temp_shift = stable_noise(config.seed, timestamp.date(), timestamp.hour, "temp-hour", low=-1.0, high=1.0)
    diurnal_phase = 2 * math.pi * (timestamp.hour - 14) / 24
    diurnal_span = max(4.0, (max_temp - min_temp) / 2)
    temperature_c = mean_temp + daily_temp_shift + diurnal_span * math.cos(diurnal_phase) + hourly_temp_shift

    cloud_state = daily_cloud_state if daily_cloud_state is not None else stable_noise(
        config.seed, timestamp.date(), "cloud-day", low=-18.0, high=18.0
    )
    hourly_cloud_shift = stable_noise(config.seed, timestamp.date(), timestamp.hour, "cloud-hour", low=-10.0, high=10.0)
    cloud_cover_pct = clamp(mean_cloud + cloud_state + hourly_cloud_shift - 12 * solar_factor, 0.0, 100.0)

    humidity_shift = stable_noise(config.seed, timestamp.date(), timestamp.hour, "humidity", low=-6.0, high=6.0)
    humidity_pct = clamp(
        mean_humidity
        - 2.2 * (temperature_c - mean_temp)
        + 0.18 * (cloud_cover_pct - mean_cloud)
        + humidity_shift,
        28.0,
        99.0,
    )

    wind_shift = stable_noise(config.seed, timestamp.date(), timestamp.hour, "wind", low=-1.7, high=1.7)
    diurnal_wind = 1.4 * max(0.0, math.sin(2 * math.pi * (timestamp.hour - 11) / 24))
    wind_speed_kmh = clamp(mean_wind + diurnal_wind + 0.05 * abs(cloud_state) + wind_shift, 1.0, 28.0)

    cos_zenith = solar_factor
    clear_sky_ghi = clear_sky_irradiance_wm2(cos_zenith)
    cloud_transmittance = clamp(1 - 0.72 * ((cloud_cover_pct / 100) ** 3.2), 0.16, 1.0)
    haze_factor = clamp(1 - ((humidity_pct - 55) / 230), 0.82, 1.0)
    ghi_wm2 = clear_sky_ghi * cloud_transmittance * haze_factor
    poa_irradiance_wm2 = plane_of_array_irradiance(
        ghi_wm2=ghi_wm2,
        solar_factor=solar_factor,
        declination_deg=position["declination_deg"],
        hour_angle_deg=position["hour_angle_deg"],
        latitude_deg=config.latitude,
        tilt_deg=config.panel_tilt_deg,
        azimuth_from_south_deg=config.panel_azimuth_deg,
        cloud_cover_pct=cloud_cover_pct,
        albedo=config.albedo,
    )

    cell_temperature_c = temperature_c + ((config.noct_c - 20) / 800.0) * poa_irradiance_wm2
    temp_efficiency = 1.0 if cell_temperature_c <= 25 else max(
        0.0, 1 - (cell_temperature_c - 25) * config.temp_coefficient
    )
    production_kw = max(
        0.0,
        config.system_size_kw
        * (poa_irradiance_wm2 / 1000.0)
        * config.derating_factor
        * config.site_calibration_factor
        * temp_efficiency,
    )
    uv_index = uv_index_from_conditions(solar_factor, cloud_cover_pct)

    return {
        "city": config.city,
        "timestamp": timestamp.isoformat(),
        "date": timestamp.date().isoformat(),
        "hour": timestamp.hour,
        "month": timestamp.month,
        "day_of_year": day_of_year,
        "is_daylight": int(solar_factor > 0),
        "temperature": round(temperature_c, 2),
        "humidity": int(round(humidity_pct)),
        "wind_speed": round(wind_speed_kmh, 2),
        "cloudcover": int(round(cloud_cover_pct)),
        "uv_index": uv_index,
        "solar_elevation_deg": round(position["elevation_deg"], 3),
        "solar_azimuth_deg": round(position["azimuth_deg"], 3),
        "solar_angle": round(solar_factor, 6),
        "cloud_factor": round(cloud_transmittance, 6),
        "temp_efficiency": round(temp_efficiency, 6),
        "uv_factor": round(clamp(uv_index / 10.0, 0.0, 1.0), 6),
        "clear_sky_ghi_wm2": round(clear_sky_ghi, 2),
        "ghi_wm2": round(ghi_wm2, 2),
        "poa_irradiance_wm2": round(poa_irradiance_wm2, 2),
        "cell_temperature_c": round(cell_temperature_c, 2),
        "production_kw": round(production_kw, 6),
        "hourly_production_kwh": round(production_kw, 6),
        "solar_potential": round(production_kw, 6),
    }


def generate_hourly_dataset(year: int, config: TurinSimulationConfig | None = None) -> list[dict[str, float | int | str]]:
    config = config or TurinSimulationConfig()
    current = datetime(year, 1, 1, tzinfo=config.tzinfo)
    end = datetime(year + 1, 1, 1, tzinfo=config.tzinfo)
    rows: list[dict[str, float | int | str]] = []
    cloud_state = 0.0

    while current < end:
        cloud_state = clamp(
            0.62 * cloud_state + stable_noise(config.seed, current.date(), "front", low=-20.0, high=20.0),
            -30.0,
            30.0,
        )
        for hour in range(24):
            timestamp = current.replace(hour=hour)
            rows.append(simulate_hour(timestamp, config=config, daily_cloud_state=cloud_state))
        current += timedelta(days=1)

    return rows


def build_live_panel_event(
    panel_id: str,
    when: datetime | None = None,
    config: TurinSimulationConfig | None = None,
) -> dict[str, float | str]:
    config = config or TurinSimulationConfig()
    local_now = when.astimezone(config.tzinfo) if when else datetime.now(config.tzinfo)
    row = simulate_hour(local_now, config=config)
    panel_variation = stable_noise(config.seed, panel_id, "panel-variance", low=0.97, high=1.03)
    production_kw = round(float(row["production_kw"]) * panel_variation, 3)

    return {
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
        "panel_id": panel_id,
        "panel_power_kw": config.system_size_kw,
        "production_kw": production_kw,
        "temperature_c": row["temperature"],
        "cloud_factor": round(float(row["cloud_factor"]), 3),
        "temp_efficiency": round(float(row["temp_efficiency"]), 3),
        "status": "active" if production_kw > 0 else "idle",
        "city": config.city,
    }
