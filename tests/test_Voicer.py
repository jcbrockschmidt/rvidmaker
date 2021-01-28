import pytest

from rvidmaker.voices import Voicer


def test_list_voice_ids():
    with pytest.raises(NotImplementedError):
        Voicer().list_voice_ids()


def test_assign_voice():
    with pytest.raises(NotImplementedError):
        Voicer().assign_voice(123, "default")


def test_select_voice():
    with pytest.raises(NotImplementedError):
        Voicer().select_voice()


def test_read_text():
    with pytest.raises(NotImplementedError):
        Voicer().read_text("This will not be read")


if __name__ == "__main__":
    pytest.main()
