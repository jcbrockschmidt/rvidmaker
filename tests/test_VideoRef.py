import pytest

from rvidmaker.videos import VideoRef


def test_get_title():
    with pytest.raises(NotImplementedError):
        VideoRef().title


def test_get_author():
    with pytest.raises(NotImplementedError):
        VideoRef().author


def test_get_duration():
    assert VideoRef().duration is None


def test_download():
    with pytest.raises(NotImplementedError):
        VideoRef().download("not-used.mp4")


if __name__ == "__main__":
    pytest.main()
