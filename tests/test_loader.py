import yaml
import pytest
from salteventsd.loader import SaltEventsdLoader
from testfixtures import compare


def _build_data(data, tmpdir):
    """
    Helper method to create a dummy config file
    """
    f = tmpdir.join("custom_eventsd")
    f.write(yaml.dump(data))
    return f


def test_custom_config_file_load(tmpdir):
    """
    Test that providing the loader with a config file it is properly loaded.
    """
    # Test loading
    data = {"general": {"foo": "bar"}}
    f = _build_data(data, tmpdir)
    s = SaltEventsdLoader(config=str(f))
    compare(s.opts, data)
    compare(s.config_file, str(f))


def test_constructor_options(tmpdir):
    """
    Test that all available flags that can be passed into the constructor
    acctually overrides the settings defined in the config file.

    Flags that is passed into the constructor should come from cli.
    """
    # Test flags
    s = SaltEventsdLoader(
        config=str(_build_data({"general": {"loglevel": "info", "logfile": "/tmp/foo/bar"}}, tmpdir)),
        log_level="debug",
        log_file="/tmp/bar/foo",
        daemonize=True,
    )
    compare(s.gen_opts["loglevel"], "debug")
    compare(s.gen_opts["logfile"], "/tmp/bar/foo")
    compare(s.gen_opts["daemonize"], True)


def test_no_general_options(tmpdir):
    """
    Test that when no general options exists it should raise an exception.
    """
    data = {}

    with pytest.raises(Exception) as e:
        SaltEventsdLoader(config=str(_build_data(data, tmpdir)))
    assert "No 'general' options found in config file" in str(e.value)


def test_get_opts(tmpdir):
    """
    Test getopts method.
    """
    data = {"general": {"foo": "bar"}}
    f = _build_data(data, tmpdir)
    s = SaltEventsdLoader(config=str(f))
    compare(s.getopts(), data)
