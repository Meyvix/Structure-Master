"""
Stracture-Master - Security Module
Handles encryption, decryption, and security-related operations.
Features:
- AES-256-CBC encryption with PBKDF2 key derivation
- Secure file handling
- Sensitive data detection
- Digital signatures
"""

import os
import hashlib
import hmac
import base64
import secrets
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field

from ..config import Config
from .logger import Logger


@dataclass
class SensitiveMatch:
    """Represents a detected sensitive data match."""
    file: str
    line: int
    pattern_type: str
    match: str
    context: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file': self.file,
            'line': self.line,
            'pattern_type': self.pattern_type,
            'match': self.match,
            'context': self.context,
        }


@dataclass 
class SecurityScanResult:
    """Result of security scan."""
    has_sensitive_data: bool
    matches: List[SensitiveMatch] = field(default_factory=list)
    files_scanned: int = 0
    warnings: List[str] = field(default_factory=list)


class SecurityManager:
    """
    Manages security operations including encryption and sensitive data detection.
    """
    
    # Encryption settings
    SALT_SIZE = 16
    IV_SIZE = 16
    KEY_SIZE = 32  # 256 bits
    ITERATIONS = 100000
    BLOCK_SIZE = 16
    
    # Sensitive data patterns
    SENSITIVE_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{4,})["\']?',
        'secret': r'(?i)(secret|private[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-+/=]{20,})["\']?',
        'token': r'(?i)(token|auth[_-]?token|access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)["\']?',
        'aws_key': r'(?i)aws[_-]?access[_-]?key[_-]?id\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?',
        'aws_secret': r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
        'private_key_header': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
        'database_url': r'(?i)(mongodb|mysql|postgres|redis)://[^\s"\']+',
        'jwt_token': r'eyJ[a-zA-Z0-9_\-]*\.eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*',
        'bearer_token': r'(?i)bearer\s+[a-zA-Z0-9_\-\.]+',
    }
    
    # Sensitive file patterns
    SENSITIVE_FILE_PATTERNS = [
        '*.pem', '*.key', '*.crt', '*.cer', '*.p12', '*.pfx',
        '.env', '.env.*', 'credentials.json', 'secrets.yaml', 'secrets.yml',
        'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519',
        '.htpasswd', 'wp-config.php',
    ]
    
    def __init__(self):
        """Initialize security manager."""
        self.logger = Logger.get_instance()
        self._crypto_available = False
        
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            self._crypto_available = True
        except ImportError:
            self.logger.warn("cryptography library not available - encryption disabled")
    
    def encrypt(self, data: bytes, password: str) -> bytes:
        """
        Encrypt data using AES-256-CBC with PBKDF2 key derivation.
        
        Args:
            data: Data to encrypt
            password: Encryption password
            
        Returns:
            Encrypted data with salt and IV prepended
        """
        if not self._crypto_available:
            raise RuntimeError("Encryption not available - install cryptography library")
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        
        # Generate salt and IV
        salt = secrets.token_bytes(self.SALT_SIZE)
        iv = secrets.token_bytes(self.IV_SIZE)
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Pad data
        padder = padding.PKCS7(self.BLOCK_SIZE * 8).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        # Prepend salt and IV
        result = salt + iv + encrypted
        
        # Add HMAC for integrity
        h = hmac.new(key, result, hashlib.sha256)
        return result + h.digest()
    
    def decrypt(self, data: bytes, password: str) -> bytes:
        """
        Decrypt data encrypted with encrypt().
        
        Args:
            data: Encrypted data
            password: Decryption password
            
        Returns:
            Decrypted data
        """
        if not self._crypto_available:
            raise RuntimeError("Decryption not available - install cryptography library")
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        
        # Extract HMAC
        hmac_size = 32
        received_hmac = data[-hmac_size:]
        data = data[:-hmac_size]
        
        # Extract salt, IV, and ciphertext
        salt = data[:self.SALT_SIZE]
        iv = data[self.SALT_SIZE:self.SALT_SIZE + self.IV_SIZE]
        ciphertext = data[self.SALT_SIZE + self.IV_SIZE:]
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Verify HMAC
        h = hmac.new(key, data, hashlib.sha256)
        if not hmac.compare_digest(h.digest(), received_hmac):
            raise ValueError("Invalid password or corrupted data")
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(self.BLOCK_SIZE * 8).unpadder()
        return unpadder.update(padded) + unpadder.finalize()
    
    def encrypt_file(self, input_path: Path, output_path: Path, password: str) -> bool:
        """Encrypt a file."""
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            encrypted = self.encrypt(data, password)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return False
    
    def decrypt_file(self, input_path: Path, output_path: Path, password: str) -> bool:
        """Decrypt a file."""
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            decrypted = self.decrypt(data, password)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            return True
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return False
    
    def scan_for_sensitive_data(self, 
                                 content: str,
                                 filename: str = '') -> List[SensitiveMatch]:
        """
        Scan content for sensitive data patterns.
        
        Args:
            content: Text content to scan
            filename: Name of file being scanned
            
        Returns:
            List of SensitiveMatch objects
        """
        matches = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_type, pattern in self.SENSITIVE_PATTERNS.items():
                for match in re.finditer(pattern, line):
                    # Mask the actual sensitive value
                    full_match = match.group(0)
                    masked = self._mask_sensitive(full_match)
                    
                    matches.append(SensitiveMatch(
                        file=filename,
                        line=line_num,
                        pattern_type=pattern_type,
                        match=masked,
                        context=self._get_context(line, match.start())
                    ))
        
        return matches
    
    def scan_directory(self, path: Path) -> SecurityScanResult:
        """
        Scan a directory for sensitive data.
        
        Args:
            path: Directory to scan
            
        Returns:
            SecurityScanResult
        """
        result = SecurityScanResult(has_sensitive_data=False)
        
        if not path.exists():
            result.warnings.append(f"Path does not exist: {path}")
            return result
        
        text_extensions = Config.TEXT_EXTENSIONS
        
        for file_path in path.rglob('*'):
            if not file_path.is_file():
                continue
            
            result.files_scanned += 1
            
            # Check if it's a sensitive filename
            if self._is_sensitive_filename(file_path.name):
                result.matches.append(SensitiveMatch(
                    file=str(file_path),
                    line=0,
                    pattern_type='sensitive_file',
                    match=file_path.name,
                    context='Sensitive filename detected'
                ))
                result.has_sensitive_data = True
            
            # Scan text files for sensitive content
            if file_path.suffix.lower() in text_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    matches = self.scan_for_sensitive_data(content, str(file_path))
                    if matches:
                        result.matches.extend(matches)
                        result.has_sensitive_data = True
                        
                except Exception as e:
                    result.warnings.append(f"Error scanning {file_path}: {e}")
        
        return result
    
    def sanitize_content(self, content: str) -> str:
        """
        Remove or mask sensitive data from content.
        
        Args:
            content: Content to sanitize
            
        Returns:
            Sanitized content
        """
        for pattern in self.SENSITIVE_PATTERNS.values():
            content = re.sub(pattern, lambda m: self._mask_sensitive(m.group(0)), content)
        
        return content
    
    def _is_sensitive_filename(self, filename: str) -> bool:
        """Check if filename matches sensitive patterns."""
        import fnmatch
        for pattern in self.SENSITIVE_FILE_PATTERNS:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        return False
    
    def _mask_sensitive(self, text: str) -> str:
        """Mask sensitive value in text."""
        # Find the value part (after : or = sign)
        if ':' in text or '=' in text:
            sep_idx = max(text.find(':'), text.find('='))
            prefix = text[:sep_idx + 1]
            value = text[sep_idx + 1:].strip().strip('"\'')
            if len(value) > 4:
                masked = value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                masked = '*' * len(value)
            return f"{prefix} {masked}"
        return text[:4] + '*' * (len(text) - 4) if len(text) > 4 else '*' * len(text)
    
    def _get_context(self, line: str, position: int, context_size: int = 50) -> str:
        """Get context around a match position."""
        start = max(0, position - context_size)
        end = min(len(line), position + context_size)
        context = line[start:end]
        if start > 0:
            context = '...' + context
        if end < len(line):
            context = context + '...'
        return context
    
    def generate_checksum(self, filepath: Path, algorithm: str = 'sha256') -> str:
        """Generate file checksum."""
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def verify_checksum(self, filepath: Path, expected: str, 
                        algorithm: str = 'sha256') -> bool:
        """Verify file checksum."""
        actual = self.generate_checksum(filepath, algorithm)
        return hmac.compare_digest(actual.lower(), expected.lower())
    
    def is_encryption_available(self) -> bool:
        """Check if encryption is available."""
        return self._crypto_available


# Create singleton instance
security = SecurityManager()
