class VoiceNotFound(Exception):
    """Raised when an invalid voice ID is used"""


class NarrationError(Exception):
    """Raised when something goes wrong while generating narrated audio"""


class VoicerInterface:
    """An interface for voicers for generating narrated text"""

    def list_voice_ids(self):
        """
        List available voices IDs.

        Returns:
            list: List of strings of valid voice IDs.
        """
        raise NotImplementedError

    def assign_voice(self, person_id, voice_id):
        """
        Assigns a voice to an ID. This is the voice that will be selected for a
        person when `select_voice()` is called with their ID.

        Args:
            person_id: ID of who is being voiced.
            voice_id (str): ID of their preferred voice.

        Raises:
            VoiceNotFound: If no voice can be found for the provided `voice_id`.
        """
        raise NotImplementedError

    def select_voice(self, person_id=None):
        """
        Changes the voice that reads text. A given ID will always have the same
        voice selected. Different IDs may be assigned the same voice.

        Args:
            person_id: ID of who is being voiced (e.g. a username). None if a
                predetermined or random voice is to be selected.

        Returns:
            str: ID of the voice selected.
        """
        raise NotImplementedError

    def read_text(self, text):
        """
        Generates audio of text being narrated in the selected voice.

        Args:
            text: Text to be narrated.

        Returns:
            str: Path to the generated audio file.

        Raises:
            NarrationError: If the audio fails to generate.
        """
        raise NotImplementedError
