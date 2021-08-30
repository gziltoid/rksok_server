# TODO: mutex
class Phonebook:
    def __init__(self):
        self.phonebook = {}

    def get_phones_by_name(self, name):
        return self.phonebook.get(name)

    def delete_entry_by_name(self, name):
        return self.phonebook.pop(name, None)

    def add_or_update_entry(self, name, phones):
        # log(f"{curr_func_name}({name}, {phones[:30]}... {len(phones)} chars)")
        self.phonebook[name] = phones
        return self.phonebook[name]
