from gtts import gTTS
from os import path

from .voicerinterface import VoiceNotFound, VoicerInterface, NarrationError


class GTTSVoicer(VoicerInterface):
    """A voicer that uses Google Text-to-Speech"""

    LANG = "en"
    SOUND_OUTPUT_ROOT = "/tmp"
    _voices = ["default"]

    def __init__(self):
        self.output_count = 0

    def list_voice_ids(self):
        return self._voices.copy()

    def assign_voice(self, person_id, voice_id):
        if voice_id not in self._voices:
            raise VoiceNotFound

    def select_voice(self, person_id=None):
        # gtts only provides one voice.
        return "default"

    def read_text(self, text):
        output_path = path.join(
            self.SOUND_OUTPUT_ROOT, "gtts-{}.mp3".format(self.output_count)
        )
        self.output_count += 1
        tts = gTTS(text=text, lang=self.LANG)
        tts.save(output_path)
        return output_path
