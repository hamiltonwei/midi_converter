import mido
from mido import MidiFile
import os
import pandas as pd


class Converter:
    _source_mid: MidiFile
    _destination_mid: MidiFile

    def __init__(self, source_format, destination_format):
        self.source_format = source_format
        self.destination_format = destination_format
        self._source_mid = MidiFile()
        self._destination_mid = MidiFile()
        self._mapping_table = "./mapping.csv"
        self._mapping_dict = {}
        self._current_file_name = ""

    def _load_mapping(self):
        """
        Load the mapping csv file into memory based on the source and destination format
        """
        try:
            df = pd.read_csv(self._mapping_table)
            if self.source_format not in df:
                raise ValueError(f"The source format '{self.source_format}' is not recognized. Check for typo.")
            if self.destination_format not in df:
                raise ValueError(f"The destination format '{self.destination_format}' is not recognized. Check for typo.")

            print(df)
            self._mapping_dict = dict(zip(df[self.source_format], df[self.destination_format]))

        except ValueError as e:
            print(e)

    def read_file(self, file_path):
        """
        Read a source MIDI file to convert and store it in the instance

        :param file_path: the path of the file to be read
        :return: the midi object read into the file
        """
        self._current_file_name = os.path.splitext(os.path.basename(file_path))[0]
        file_abspath = os.path.abspath(file_path)
        self._source_mid = MidiFile(file_abspath, clip=True)
        return self._source_mid

    def convert(self):
        """
        Map the notes of the midi file.
        :return: the converted midi object.
        """
        self._load_mapping()
        self._destination_mid = self._source_mid
        for track in self._destination_mid.tracks:
            msg: mido.Message
            for msg in track:
                if msg.type in ["note_on", "note_off"]:
                    old_note = msg.note
                    msg.note = self._mapping_dict[old_note]
        return self._destination_mid

    def write_file(self):
        self._destination_mid.save(f"{self._current_file_name}-{self.destination_format}.mid")


if __name__ == "__main__":
    c = Converter("studio_drummer_gm", "guitar_pro_8_drumkit")
    print(c.read_file("C:/- Personal Files/Codes/MIDIConverter/References/Dazer.mid"))
    c.convert()
    c.write_file()
