from typing import Dict, Any, Optional

class ConverterService:
    @staticmethod
    def convert_text(text: str, mapping: Dict[str, str]) -> str:
        """
        Converts text according to a keyboard layout mapping.
        Supports multi-character keys by matching the longest key prefix first.
        Preserves spacing, line breaks, and characters not found in the mapping.
        """
        if not text:
            return ""
        if not mapping:
            return text

        # Sort mapping keys by length descending to match longest sequences first
        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
        
        result = []
        i = 0
        n = len(text)
        
        while i < n:
            match_found = False
            # Try to match keys starting at current index i
            for key in sorted_keys:
                key_len = len(key)
                if i + key_len <= n and text[i:i+key_len] == key:
                    result.append(mapping[key])
                    i += key_len
                    match_found = True
                    break
            
            if not match_found:
                # Append original character if no mapping key matches
                result.append(text[i])
                i += 1
                
        return "".join(result)

    @staticmethod
    def detect_rtl(text: str) -> bool:
        """
        Quick check to determine if the string is primarily RTL (e.g. Arabic, Hebrew).
        """
        if not text:
            return False
        # RTL unicode range boundaries
        rtl_chars = 0
        ltr_chars = 0
        for char in text:
            val = ord(char)
            if 0x0590 <= val <= 0x06FF or 0x0750 <= val <= 0x077F or 0x08A0 <= val <= 0x08FF or 0xFB50 <= val <= 0xFDFF or 0xFE70 <= val <= 0xFEFF:
                rtl_chars += 1
            elif char.isalpha():
                ltr_chars += 1
        
        return rtl_chars > ltr_chars
