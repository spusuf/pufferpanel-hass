import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST, 
    CONF_PORT, 
    CONF_CLIENT_ID, 
    CONF_CLIENT_SECRET, 
    Platform
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PufferPanelClient
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PufferPanel from a config entry."""
    
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    use_https = entry.data.get("use_https", False)
    
    scan_interval = entry.options.get(
        "refresh_frequency", 
        entry.data.get("refresh_frequency", 60)
    )
    host = entry.data[CONF_HOST]

    session = async_get_clientsession(hass)
    client = PufferPanelClient(
        host=host,
        port=port,
        client_id=client_id,
        client_secret=client_secret,
        session=session,
        use_https=use_https
    )

    async def async_update_data():
        """Fetch data from PufferPanel for all servers."""
        try:
            response = await client.get_servers()
            if response is None:
                raise UpdateFailed("Failed to fetch servers from PufferPanel")

            server_list = response.get("servers", [])
            all_server_results = {}

            for server in server_list:
                sid = server["id"]
                status = await client.get_server_status(sid)
                flags = await client.get_server_flags(sid)
                is_running = status.get("running", False)
                
                stats = None
                query= {}
                server_raw_data = {}

                if is_running:
                    try:
                        stats = await client.get_server_stats(sid)
                        query = await client.get_server_query(sid) or {}
                        server_raw_data = await client.get_server_data(sid)
                    except Exception as e:
                        _LOGGER.warning("Could not fetch stats for %s: %s", sid, e)

                all_server_results[sid] = {
                    "summary": server,
                    "status": status,
                    "flags": flags,
                    "stats": stats,
                    "query": query,
                    "data": server_raw_data
                }

            return all_server_results
            
        except Exception as err:
            raise UpdateFailed(f"Communication error: {err}")


    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"PufferPanel {host}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )
    coordinator.client = client

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Could not connect to PufferPanel: {err}") from err

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
