from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up PufferPanel buttons."""
    coordinator = entry.runtime_data
    entities = []

    for server_id, data in coordinator.data.items():
        summary = data.get("summary", {})
        server_name = summary.get("name", f"Server {server_id}")

        actions = [
            ("start", "Start", "mdi:play"),
            ("stop", "Stop", "mdi:stop"),
            ("restart", "Restart", "mdi:restart"),
            ("reload", "Reload", "mdi:refresh"),
            ("install", "Install", "mdi:cloud-download"),
            ("kill", "Kill", "mdi:skull")
            #("backup", "Backup", "mdi:cloud-upload") # Backup, needs server down
        ]

        for action_id, action_name, icon in actions:
            entities.append(
                PufferPanelButton(
                    coordinator, 
                    server_id, 
                    server_name, 
                    action_id, 
                    action_name, 
                    icon
                )
            )

    async_add_entities(entities)

class PufferPanelButton(ButtonEntity):
    """Representation of a PufferPanel action button."""

    def __init__(self, coordinator, server_id, server_name, action_id, action_name, icon):
        """Initialize the button."""
        self.coordinator = coordinator
        self.server_id = server_id
        self.action_id = str(action_id)
        
        self._attr_name = (action_name or action_id or "Action").capitalize()
        self._attr_icon = icon
        self._attr_unique_id = f"{server_id}_{action_id}"
        
        diagnostic_buttons = ["install", "kill", "reload"]

        if action_id in diagnostic_buttons:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_id)},
            name=server_name
        )
    @property
    def available(self) -> bool:
        """Return True if the server is available."""
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Handle the button press."""
        success = await self.coordinator.client.send_server_action(
            self.server_id, 
            self.action_id
        )
        if success:
            await self.coordinator.async_request_refresh()
        return None
