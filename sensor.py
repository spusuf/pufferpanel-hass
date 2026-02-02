from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

MINECRAFT_TYPES = ("minecraft", "minecraft-java")

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up PufferPanel sensors."""
    coordinator = entry.runtime_data
    entities = []

    
    if coordinator.data:
        for server_id, data in coordinator.data.items():
            try:
                summary = data.get("summary", {})
                server_name = summary.get("name", f"Server {server_id}")
                server_type = summary.get("type", "unknown")
                node_info = summary.get("node", {})
                local_node = node_info.get("isLocal", True)
                status = data.get("status") or {}

                entities.append(PufferPanelCPUSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelThreadSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelRAMSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelIPSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelPortSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelServerStatusSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelAutoStartSensor(coordinator, server_id, server_name, server_type))
                entities.append(PufferPanelAutoStartCrashSensor(coordinator, server_id, server_name, server_type))

                if not local_node:
                    entities.append(PufferPanelNodeSensor(coordinator, server_id, server_name, server_type))

                if server_type in MINECRAFT_TYPES or "minecraft" in status:
                    entities.append(MinecraftPlayerSensor(coordinator, server_id, server_name, server_type))
                    entities.append(MinecraftVersionSensor(coordinator, server_id, server_name, server_type))
                    entities.append(MinecraftModLauncher(coordinator, server_id, server_name, server_type))
                    entities.append(MinecraftMOTD(coordinator, server_id, server_name, server_type))
            except Exception as err:
                _LOGGER.error("Error adding server %s: %s", server_id, err)

    if entities:
        async_add_entities(entities)

class PufferPanelBaseEntity(CoordinatorEntity):
    """Common base for all PufferPanel entities to handle device grouping."""
    
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator)
        self.server_id = server_id
        self._attr_has_entity_name = True
        
        config_data = self.coordinator.config_entry.data
        host = config_data.get("host", "localhost")
        port = config_data.get("port", 8080)
        use_https = config_data.get("use_https", False)

        type_map = {
            "minecraft-java": "Minecraft Server (Java)",
            "minecraft-bedrock": "Minecraft Server (Bedrock)",
            "srcds": "Source Engine Server",
            "unknown": "Game Server"
        }
        
        protocol = "https" if use_https else "http"
        base_url = f"{protocol}://{host}:{int(float(port))}"
        pretty_type = type_map.get(server_type, server_type.replace("-", " ").capitalize())
        

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_id)},
            name=server_name,
            model=pretty_type,
            manufacturer="Pufferpanel Integration",
            configuration_url=base_url
        )

class PufferPanelServerStatusSensor(PufferPanelBaseEntity, SensorEntity):
    """Server status sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_status"
        self._attr_name = "Server Status"
        self.attr_options = ["Online", "Offline", "Installing"]
        self.attr_device_class = SensorDeviceClass.ENUM

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.server_id, {}).get("status", {})
        if data.get("installing"):
            return "Installing"
        if data.get("running"):
            return "Online"
        return "Offline"

    @property
    def icon(self):
        """Change the icon based on the current state."""
        state = self.native_value
        if state == "Online":
            return "mdi:server-network"
        if state == "Installing":
            return "mdi:sync"
        return "mdi:server-network-off"

class PufferPanelThreadSensor(PufferPanelBaseEntity, SensorEntity):
    """Thread usage sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_thread"
        self._attr_name = "CPU Usage (thread)"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:chip"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.server_id, {}).get("stats")
        return round(data.get("cpu", 0), 2) if data else 0

class PufferPanelCPUSensor(PufferPanelBaseEntity, SensorEntity):
    """CPU usage sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_cpu"
        self._attr_name = "CPU Usage (total)"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:chip"
        self._core_count = self.coordinator.config_entry.options.get(
            "core_count",
            self.coordinator.config_entry.data.get("core_count", 1)
        )

    @property
    def native_value(self):
        stats = self.coordinator.data.get(self.server_id, {}).get("stats")
        if stats and "cpu" in stats:
            try:
                raw_cpu = float(stats["cpu"])
                return round(raw_cpu / self._core_count, 1)
            except (ValueError, TypeError):
                return 0
        return 0

    

class PufferPanelRAMSensor(PufferPanelBaseEntity, SensorEntity):
    """RAM usage sensor in GB."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_ram"
        self._attr_name = "Memory Usage"
        self._attr_native_unit_of_measurement = "GB"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:memory"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.server_id, {}).get("stats")
        if data:
            return round(data.get("memory", 0) / (1024 ** 3), 2)
        return 0

class PufferPanelIPSensor(PufferPanelBaseEntity, SensorEntity):
    """IP address sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_ip"
        self._attr_name = "IP Address"
        self._attr_icon = "mdi:ip-network"

    @property
    def native_value(self):
        server_data = self.coordinator.data.get(self.server_id, {})
        summary = server_data.get("summary", {})
        reported_ip = summary.get("ip", "Unknown")
        
        if reported_ip == "0.0.0.0" or reported_ip == "127.0.0.1" or reported_ip == "localhost":
            return self.coordinator.config_entry.data.get("host", "localhost")
        return reported_ip

class PufferPanelPortSensor(PufferPanelBaseEntity, SensorEntity):
    """Port sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_port"
        self._attr_name = "Port"
        self._attr_icon = "mdi:wall-fire"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.server_id, {}).get("summary", {})
        return data.get("port", "Unknown")


class PufferPanelAutoStartSensor(PufferPanelBaseEntity, SensorEntity):
    """Auto start sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_autostart"
        self._attr_name = "Auto Start"
        self._attr_icon = "mdi:restart"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.server_id, {}).get("flags", {})
        return data.get("autoStart", "Unknown")

class PufferPanelAutoStartCrashSensor(PufferPanelBaseEntity, SensorEntity):
    """Auto start sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_autostart_crash"
        self._attr_name = "Restart on Crash"
        self._attr_icon = "mdi:restart-alert"

    @property
    def native_value(self):
        data = self.coordinator.data.get(self.server_id, {}).get("flags", {})
        return data.get("autoRestartOnCrash", "Unknown")

class PufferPanelNodeSensor(PufferPanelBaseEntity, SensorEntity):
    """Node sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_node"
        self._attr_name = "Node"
        self._attr_icon = "mdi:server-network"
    
    @property
    def native_value(self):
        server_entry = self.coordinator.data.get(self.server_id, {})
        summary = server_entry.get("summary", {})
        node_info = summary.get("node", {})
        if isinstance(node_info, dict):
            return node_info.get("name", "Unknown")
        return "Unknown"

class MinecraftPlayerSensor(PufferPanelBaseEntity, SensorEntity):
    """Minecraft player count sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_players"
        self._attr_name = "Players Online"
        self._attr_native_unit_of_measurement = "players"

    @property
    def native_value(self):
        server_data = self.coordinator.data.get(self.server_id, {})
        query_data = server_data.get("query", {})
        if query_data and isinstance(query_data, dict):
            mc_info = query_data.get("minecraft", {})
            return mc_info.get("numPlayers", 0)
        return 0

    @property
    def icon(self):
        if self.native_value > 2:
            return "mdi:account-group"
        if self.native_value == 2:
            return "mdi:account-multiple"
        if self.native_value == 1:
            return "mdi:account"
        return "mdi:account-off"

class MinecraftVersionSensor(PufferPanelBaseEntity, SensorEntity):
    """Minecraft version sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_version"
        self._attr_name = "Game Version"
        self._attr_icon = "mdi:minecraft"

    @property
    def native_value(self):
        server_data = self.coordinator.data.get(self.server_id, {})
        query_data = server_data.get("query", {})
        if query_data and isinstance(query_data, dict):
            mc_info = query_data.get("minecraft", {})
            return mc_info.get("version", "Unknown")
        return "Unknown"

class MinecraftModLauncher(PufferPanelBaseEntity, SensorEntity):
    """Minecraft mod launcher sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_modlauncher"
        self._attr_name = "Mod Launcher"
        self._attr_icon = "mdi:minecraft"

    @property
    def native_value(self):
        server_data = self.coordinator.data.get(self.server_id, {})
        data_top = server_data.get("data", {})
        if not isinstance(data_top, dict): return "Unknown"

        data_inner = data_top.get("data", {})
        mod_info = data_inner.get("modlauncher", {})
        raw_value = mod_info.get("value")

        if raw_value is None:
            return "Unknown"

        display_value = {
            "paper": "Paper",
            "fabric": "Fabric",
            "minecraftforge": "Forge",
            "minecraft-forge": "Forge",
            "forge": "Forge",
            "neoforge": "NeoForge",
            "vanilla": "Vanilla",
            "": "Vanilla",
            "unknown": "Vanilla",
        }
        return display_value.get(raw_value, raw_value.capitalize())

class MinecraftMOTD(PufferPanelBaseEntity, SensorEntity):
    """Minecraft MOTD sensor."""
    def __init__(self, coordinator, server_id, server_name, server_type):
        super().__init__(coordinator, server_id, server_name, server_type)
        self._attr_unique_id = f"{server_id}_motd"
        self._attr_name = "Server Message"
        self._attr_icon = "mdi:minecraft"

    @property
    def native_value(self):
        server_data = self.coordinator.data.get(self.server_id, {})
        data_top = server_data.get("data", {})
        if not isinstance(data_top, dict): return "Unknown"

        data_inner = data_top.get("data", {})
        motd_top = data_inner.get("motd", {})
        motd_value = motd_top.get("value", {})
        return motd_value
    
