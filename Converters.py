import mido
from mido import MidiFile, MidiTrack
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
        self._quantize_threshold = 100

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

    def write_file(self):
        self._destination_mid.save(f"{self._current_file_name}-{self.destination_format}.mid")

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
                if self._msg_is_note_on_note_off(msg):
                    old_note = msg.note
                    msg.note = self._mapping_dict[old_note]
        return self._destination_mid

    def note_only(self):
        """
        Remove all MIDI messages that are not a note (e.g. pitch wheels, automations, foot pedal etc. will be removed)
        :return: the converted midi object with only note events
        """
        new_track_list = [self._make_list_notes_only(track) for track in self._destination_mid.tracks]
        self._destination_mid.tracks = new_track_list
        return self._destination_mid

    def resolve_ties(self):
        """
        Remove any ties between midi notes. Useful for generating sheet music for drummers

        A list that does not contain a tie is where
        every consecutive sequence of note_on or consecutive seqquence of note_off events are simultaneous.
        """
        # Currently this function only works with midi file with notes only. It will automatically convert.
        self.note_only()
        # TODO: Implement
        raise NotImplementedError

    def _make_list_notes_only(self, msg_list: [mido.Message]):
        new_list = []
        time_since_last_note_msg = 0
        # time_elapsed_per_note = {}

        for msg in msg_list:
            time_since_last_note_msg += msg.time
            if self._msg_is_note_on_note_off(msg):
                msg.time = time_since_last_note_msg
                new_list.append(msg)
                time_since_last_note_msg = 0

            # track the elapsed time per note
            # if msg.type == "note_on":
                # this check could be redundant but just in case the midi file is corrupt
                # if msg.note not in time_elapsed_per_note.keys():
                #     time_elapsed_per_note[msg.note] = 0

            # elif msg.type == "note_off":
            #     # time_elapsed_per_note.pop(msg.note, None)
            # time_elapsed_per_note = {note:time + msg.time for note, time in time_elapsed_per_note.items()}
        return MidiTrack(new_list)

    def _check_ties(self, msg_list: [mido.Message]) -> bool:
        """
        Check if this list of midi event have any ties
        A list that does not contain a tie is where
        every consecutive sequence of on or off events are simultaneous.
        :param msg_list: the list of midi message to be checked
        :return: whether this list has ties
        """
        current_status = ""
        simultaneous_list = []
        for msg in msg_list:
            if self._msg_is_note_on_note_off(msg):
                if not simultaneous_list:
                    current_status = msg.type

                # collect all consecutive on or consecutive off sequences in a list
                if msg.type == current_status:
                    simultaneous_list.append(msg)
                # when we are done collecting this sequence, check if they are simultaneous
                else:
                    if not self._check_simultaneous(simultaneous_list):
                        return False
                    else:
                        simultaneous_list = []
        return True

    def _msg_is_note_on_note_off(self, msg: mido.Message) -> bool:
        return msg.type == "note_on" or msg.type == "note_off"

    def _check_simultaneous(self, msg_list: [mido.Message]) -> bool:
        """
        Check if this list of midi events are occuring simultaneously
        :param msg_list: A list of midi messages

        :return: whether this list are simultaneous
        """
        # the list of notes are simultaneous if the gap between first and last note is within threshold
        threshold = self._source_mid.ticks_per_beat / self._quantize_threshold
        return abs(msg_list[0].time - msg_list[-1]) < threshold

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
            self._mapping_dict = dict(zip(df[self.source_format], df[self.destination_format]))

        except ValueError as e:
            print(e)


if __name__ == "__main__":
    source = "C:/- Personal Files/Codes/MIDIConverter/test_midi_files/test-overlapping notes.MID"

    c = Converter("studio_drummer_gm", "guitar_pro_8_drumkit")
    print(c.read_file(source))

    c.convert()
    c.write_file()
