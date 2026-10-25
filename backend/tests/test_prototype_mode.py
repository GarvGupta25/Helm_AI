"""The prototype must not send real messages just because credentials exist."""
import runpy
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize('real_delivery', [False, True])
def test_prototype_requires_explicit_real_delivery(monkeypatch, real_delivery):
    launch = runpy.run_path
    monkeypatch.setenv('OTP_DELIVERY_MODE', 'twilio')
    monkeypatch.setenv('WHATSAPP_MOCK_AUTH', 'false')
    monkeypatch.setattr(sys, 'argv', ['prototype_server.py'] +
                        (['--allow-configured-sandbox'] if real_delivery else []))
    calls = []
    monkeypatch.setattr(runpy, 'run_path', lambda path, **kwargs: calls.append(path))
    launch(str(Path(__file__).resolve().parents[1] / 'scripts/prototype_server.py'), run_name='__main__')
    import os
    assert os.environ['OTP_DELIVERY_MODE'] == ('twilio' if real_delivery else 'mock')
    assert os.environ['WHATSAPP_MOCK_AUTH'] == ('false' if real_delivery else 'true')
    assert len(calls) == 1 and calls[0].endswith('uk_test_server.py')
    assert '--allow-configured-sandbox' in sys.argv
