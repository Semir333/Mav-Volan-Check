"""DataUpdateCoordinator for BKK & MÁV Transit Sync."""
import logging
import time
from datetime import timedelta
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_TRANSPORT_TYPE,
    CONF_STOP_ID,
    CONF_DIRECTION_FILTER,
    CONF_API_KEY,
    TRANSPORT_TYPE_TRAIN,
    TRANSPORT_TYPE_BUS,
    TRAIN_OFFSETS,
)

_LOGGER = logging.getLogger(__name__)

class TransitDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching transit data."""

    def __init__(self, hass: HomeAssistant, entry, scan_interval: int):
        """Initialize coordinator."""
        self.entry = entry
        self.transport_type = entry.data.get(CONF_TRANSPORT_TYPE)
        self.direction_filter = entry.options.get(
            CONF_DIRECTION_FILTER, entry.data.get(CONF_DIRECTION_FILTER, "nyugati")
        ).lower()
        self.stop_id = entry.options.get(CONF_STOP_ID, entry.data.get(CONF_STOP_ID, "volan_777764_2"))
        self.api_key = entry.data.get(CONF_API_KEY)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Transit Coordinator ({self.transport_type})",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API based on transport type."""
        try:
            if self.transport_type == TRANSPORT_TYPE_TRAIN:
                return await self._fetch_train_data()
            else:
                return await self._fetch_bus_data()
        except Exception as err:
            raise UpdateFailed(f"Hiba történt a lekérdezés során: {err}") from err

    async def _fetch_train_data(self):
        """Fetch and process MÁV train data."""
        url = "https://data.traintrack.hu/live"
        headers = {"User-Agent": "Mozilla/5.0"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP hiba: {resp.status}")
                live_data = await resp.json(content_type=None)

        vehicles = live_data.get("v", [])
        now_unix = time.time()
        lt = time.localtime(now_unix)
        now_seconds = lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec

        found_trains = []
        for item in vehicles:
            hd = str(item.get("hd") or "").lower()
            rl = str(item.get("rl") or "").upper()
            sn = str(item.get("sn") or "").upper()
            sname = str(item.get("sname") or "").lower()

            if self.direction_filter not in hd:
                continue

            is_s71_or_g71 = "S71" in rl or "G71" in rl or "S71" in sn or "G71" in sn
            train_no_raw = sn.split()[0] if sn else ""
            if train_no_raw.isdigit() and (train_no_raw.startswith("29") or train_no_raw.startswith("25")):
                is_s71_or_g71 = True

            if not is_s71_or_g71:
                continue

            if sname in TRAIN_OFFSETS:
                offset = TRAIN_OFFSETS[sname]
                dep_val = item.get("dep") or item.get("arr")
                if not dep_val:
                    continue

                if dep_val > 86400:
                    erd_dep_seconds = (dep_val - now_unix) + now_seconds + offset
                else:
                    erd_dep_seconds = dep_val + offset

                time_diff = erd_dep_seconds - now_seconds
                delay_min = int(item.get("delay_minutes") or item.get("delay") or 0)
                display_no = train_no_raw if train_no_raw.isdigit() else ("G71" if "G71" in sn else "S71")

                erd_dep_seconds = erd_dep_seconds % 86400
                dep_string = f"{int(erd_dep_seconds // 3600):02d}:{int((erd_dep_seconds % 3600) // 60):02d}"

                sch_seconds = (erd_dep_seconds - (delay_min * 60)) % 86400
                sch_string = f"{int(sch_seconds // 3600):02d}:{int((sch_seconds % 3600) // 60):02d}"

                found_trains.append({
                    "time_diff": time_diff,
                    "departure": dep_string,
                    "scheduled": sch_string,
                    "delay": delay_min,
                    "train_no": display_no
                })

        last_update_str = time.strftime('%H:%M:%S', lt)

        if not found_trains:
            return {
                "departure": "Indulásra vár",
                "delay": 0,
                "scheduled": "N/A",
                "train_no": "N/A",
                "last_update": last_update_str
            }

        found_trains.sort(key=lambda x: x["time_diff"])
        next_train = None
        for train in found_trains:
            if train["time_diff"] > -120:
                next_train = train
                break

        if next_train and next_train["time_diff"] <= 2700:
            res = next_train
            res["last_update"] = last_update_str
            res.pop("time_diff", None)
            return res

        return {
            "departure": "Indulásra vár",
            "delay": 0,
            "scheduled": "N/A",
            "train_no": "N/A",
            "last_update": last_update_str
        }

    async def _fetch_bus_data(self):
        """Fetch and process BKK/Volánbusz data."""
        url = f"https://go.bkk.hu/api/query/v1/ws/otp/api/where/arrivals-and-departures-for-stop.json?stopId={self.stop_id}&onlyDepartures=true&minutesBefore=0&minutesAfter=180&key={self.api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP hiba: {resp.status}")
                json_data = await resp.json()

        entry_data = json_data.get("data", {}).get("entry", {})
        references = json_data.get("data", {}).get("references", {})
        stop_times = entry_data.get("stopTimes", [])

        if not stop_times:
            return {
                "departure": "Nincs indulás",
                "delay": 0,
                "route": "-",
                "raw_entry": entry_data,
                "raw_references": references
            }

        # Keresünk egy irány-szűrőnek megfelelő buszt (alapértelmezetten Pl. Újpest)
        selected_st = None
        for st in stop_times:
            headsign = st.get("stopHeadsign", "")
            if self.direction_filter in headsign.lower():
                selected_st = st
                break

        if not selected_st:
            selected_st = stop_times[0]

        terv = selected_st.get("departureTime", 0)
        valos = selected_st.get("predictedDepartureTime") or terv
        keses_perc = int((valos - terv) / 60)

        # Idő formázása
        ts = valos if valos > 1000000000000 else valos * 1000
        lt = time.localtime(ts / 1000)
        dep_str = time.strftime("%H:%M", lt)

        # Járat azonosítása a references objektumból
        trip_id = selected_st.get("tripId")
        route_id = references.get("trips", {}).get(trip_id, {}).get("routeId") if trip_id else None
        route_short = references.get("routes", {}).get(route_id, {}).get("shortName", "Busz") if route_id else "Busz"

        return {
            "departure": dep_str,
            "delay": keses_perc,
            "route": route_short,
            "headsign": selected_st.get("stopHeadsign", ""),
            "raw_entry": entry_data,
            "raw_references": references
        }