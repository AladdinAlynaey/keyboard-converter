import pytest
from services.converter_service import ConverterService
from models.schemas import UserRegisterSchema, LayoutCreateSchema
from pydantic import ValidationError

# PC default mapping mock
TEST_MAPPING = {
    "q": "ض", "w": "ص", "e": "ث", "r": "ق", "t": "ف",
    "a": "ش", "s": "س", "d": "ي", "f": "ب",
    "sh": "ش" # multi-character sequence test
}

def test_raw_layout_conversion():
    # Test simple single-char conversion
    res = ConverterService.convert_text("qwe", TEST_MAPPING)
    assert res == "ضصث"

    # Test unknown character preservation
    res = ConverterService.convert_text("qwe123xyz", TEST_MAPPING)
    assert res == "ضصث123xyz"

    # Test spacing and formatting preservation
    res = ConverterService.convert_text("qw\ne a", TEST_MAPPING)
    assert res == "ضص\nث ش"

def test_sequence_layout_conversion():
    # Test greedy longest-prefix matches
    res = ConverterService.convert_text("shq", TEST_MAPPING)
    assert res == "شض"

def test_rtl_detection():
    # LTR detection
    assert ConverterService.detect_rtl("Hello World") is False
    # RTL detection
    assert ConverterService.detect_rtl("مرحبا بك") is True
    # Mixed language detection
    assert ConverterService.detect_rtl("Hello مرحبا بك") is True
    # Numeric/symbol inputs
    assert ConverterService.detect_rtl("12345 @") is False

def test_register_password_validation():
    # Fail on weak passwords
    with pytest.raises(ValidationError):
        UserRegisterSchema(email="test@test.com", password="weak") # under 8 chars
        
    with pytest.raises(ValidationError):
        UserRegisterSchema(email="test@test.com", password="lowercaseonly") # missing uppercase/numbers
        
    # Succeed on complex passwords
    valid = UserRegisterSchema(email="test@test.com", password="ComplexPassword123!")
    assert valid.email == "test@test.com"

def test_layout_pydantic_schema():
    # Fail on empty mapping
    with pytest.raises(ValidationError):
        LayoutCreateSchema(name="Test", language="Arabic", mapping={})
        
    # Fail on overly long input key
    with pytest.raises(ValidationError):
        LayoutCreateSchema(name="Test", language="Arabic", mapping={"toolongkey": "x"})
