"""La liste de courses partagée de Printr, en liste de tâches Home Assistant.

Printr ne connaît pas d'article « fait » : cocher un article le retire de la liste.
"""

from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import PrintrError
from .coordinator import PrintrConfigEntry
from .entity import PrintrEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PrintrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PrintrShoppingList(entry.runtime_data, "shopping")])


class PrintrShoppingList(PrintrEntity, TodoListEntity):
    _attr_translation_key = "shopping"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=item["id"],
                summary=item["text"],
                status=TodoItemStatus.NEEDS_ACTION,
                description=f"Ajouté par {item['by']}" if item.get("by") else None,
            )
            for item in self.coordinator.data.shopping
        ]

    async def _call(self, coro) -> None:
        try:
            self.coordinator.data.shopping = await coro
        except PrintrError as err:
            raise HomeAssistantError(f"Liste de courses : {err}") from err
        self.async_write_ha_state()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await self._call(self.coordinator.client.add_shopping(item.summary or ""))

    async def async_update_todo_item(self, item: TodoItem) -> None:
        current = next((i for i in self.coordinator.data.shopping if i["id"] == item.uid), None)
        if current is None:
            raise HomeAssistantError("Article introuvable dans Printr")
        if item.status == TodoItemStatus.COMPLETED:
            await self._call(self.coordinator.client.remove_shopping(item.uid))
        elif item.summary and item.summary != current["text"]:
            # Pas de modification dans Printr : on remplace l'article.
            await self._call(self.coordinator.client.remove_shopping(item.uid))
            await self._call(self.coordinator.client.add_shopping(item.summary))

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            await self._call(self.coordinator.client.remove_shopping(uid))
