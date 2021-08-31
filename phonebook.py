from loguru import logger


class Phonebook:
    def __init__(self):
        self.phonebook = {}

    def get_phones_by_name(self, name):
        logger.info(f"Getting phones: ({name})")
        return self.phonebook.get(name)

    def delete_entry_by_name(self, name):
        logger.info(f"Deleting: ({name})")
        return self.phonebook.pop(name, None)

    def add_or_update_entry(self, name, phones):
        logger.info(f"Adding: ({name}, {phones[:30]}... {len(phones)} chars)")
        self.phonebook[name] = phones
        return self.phonebook[name]
