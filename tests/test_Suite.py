import pytest

from rvidmaker.suites import Suite


def test_config():
    with pytest.raises(NotImplementedError):
        Suite().config("foobar.toml")


def test_generate():
    with pytest.raises(NotImplementedError):
        Suite().generate("fake-directory")


if __name__ == "__main__":
    pytest.main()
