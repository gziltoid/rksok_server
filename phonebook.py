from loguru import logger
from typing import Optional


class Phonebook:
    def __init__(self):
        self.phonebook = {}

    def get_phones_by_name(self, name: str) -> Optional[str]:
        logger.info(f"Getting phones: ({name})")
        return self.phonebook.get(name)

    def delete_entry_by_name(self, name: str) -> Optional[str]:
        logger.info(f"Deleting: ({name})")
        return self.phonebook.pop(name, None)

    def add_or_update_entry(self, name: str, phones: str) -> str:
        logger.info(f"Adding: ({name}, {phones[:30]}... {len(phones)} chars)")
        self.phonebook[name] = phones
        return self.phonebook[name]
