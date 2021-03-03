import json
import os


class States(dict):

    def __init__(self, default: {}, file_name='states.json'):
        self.file_name = file_name

        if os.path.exists(file_name):
            super().__init__(json.loads(open(file_name).read()))
            print("Loaded states from file: %r" % self)
            return

        super().__init__(default)
        self.save()

    def update(self, E=None, **F):
        dict.update(self, E, **F) # Call normal dict function
        self.save()  # Save file

    def save(self):
        print("Saving state file")
        with open(self.file_name, 'w') as fp:
            json.dump(self, fp)