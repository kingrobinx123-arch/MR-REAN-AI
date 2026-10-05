import os
from app.workspace import safe_member

def test_safe_member():
    assert safe_member("src/main.py")=="src/main.py"
    assert safe_member("../secret") is None
    assert safe_member("/etc/passwd")=="etc/passwd"
