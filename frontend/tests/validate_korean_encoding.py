#!/usr/bin/env python3
"""
Korean text encoding validation test (T304, FR-115)

Validates that errorMessages.ts contains proper Korean text
and no mojibake corruption from T302 fix.

Run: python3 frontend/tests/validate_korean_encoding.py
"""

import re
import sys
from pathlib import Path

# ANSI colors
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
RESET = '\033[0m'

# Test configuration
SCRIPT_DIR = Path(__file__).parent
ERROR_MESSAGES_PATH = SCRIPT_DIR.parent / 'src' / 'lib' / 'errorMessages.ts'

# Korean Unicode range: AC00-D7A3 (Hangul Syllables)
KOREAN_CHAR_REGEX = re.compile(r'[\uAC00-\uD7A3]')
KOREAN_CHARS_REGEX = re.compile(r'[\uAC00-\uD7A3]+')

# Mojibake patterns (common corruption patterns)
MOJIBAKE_PATTERNS = [
    re.compile(r'\ufffd'),              # Replacement character �
    re.compile(r'�+'),                  # Multiple � characters
    re.compile(r'[\x80-\xFF]{3,}'),     # Invalid byte sequences
]

# Expected Korean strings (from T302 fix)
EXPECTED_STRINGS = [
    '사용자 이름 또는 비밀번호가 올바르지 않습니다.',
    '세션이 만료되었습니다.',
    '네트워크 연결에 실패했습니다.',
    '파일 크기가 너무 큽니다.',
    '대화를 찾을 수 없습니다.',
]

# Test results tracking
tests_passed = 0
tests_failed = 0
errors = []


def log(message, color=RESET):
    """Print colored log message"""
    print(f'{color}{message}{RESET}')


def pass_test(test_name, detail=''):
    """Record a passing test"""
    global tests_passed
    tests_passed += 1
    log(f'  ✅ {test_name}', GREEN)
    if detail:
        log(f'     {detail}', GREEN)


def fail_test(test_name, reason):
    """Record a failing test"""
    global tests_failed
    tests_failed += 1
    errors.append({'test': test_name, 'reason': reason})
    log(f'  ❌ {test_name}', RED)
    log(f'     {reason}', YELLOW)


def run_tests():
    """Run all validation tests"""
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE)
    log('한글 텍스트 인코딩 검증 테스트 (T304, FR-115)', BLUE)
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE)
    print()

    # Test 1: File exists
    log('Test 1: errorMessages.ts 파일 존재 확인')
    if not ERROR_MESSAGES_PATH.exists():
        fail_test('File exists', f'File not found: {ERROR_MESSAGES_PATH}')
        return print_summary()
    pass_test('File exists')

    # Read file content
    try:
        with open(ERROR_MESSAGES_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        fail_test('File read (UTF-8)', f'Failed to read as UTF-8: {e}')
        return print_summary()
    except Exception as e:
        fail_test('File read', f'Failed to read file: {e}')
        return print_summary()

    # Test 2: File is not empty
    log('Test 2: 파일이 비어있지 않은지 확인')
    if not content or not content.strip():
        fail_test('File not empty', 'File is empty')
    else:
        pass_test('File not empty', f'{len(content)} characters')

    # Test 3: Contains Korean characters
    log('Test 3: 한글 문자 존재 확인')
    if not KOREAN_CHAR_REGEX.search(content):
        fail_test('Contains Korean', 'No Korean characters found in file')
    else:
        korean_matches = KOREAN_CHARS_REGEX.findall(content)
        korean_blocks = len(korean_matches) if korean_matches else 0
        pass_test('Contains Korean', f'{korean_blocks} Korean text blocks found')

    # Test 4: No mojibake patterns
    log('Test 4: Mojibake 패턴 존재하지 않음 확인')
    has_mojibake = False
    for pattern in MOJIBAKE_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            fail_test('No mojibake', f'Found {len(matches)} mojibake pattern(s): {pattern.pattern}')
            has_mojibake = True
            break
    if not has_mojibake:
        pass_test('No mojibake patterns detected')

    # Test 5: Expected strings present
    log('Test 5: 예상 한글 문자열 존재 확인')
    missing_strings = []
    for expected_string in EXPECTED_STRINGS:
        if expected_string not in content:
            missing_strings.append(expected_string)

    if missing_strings:
        fail_test(
            'Expected strings present',
            f'Missing {len(missing_strings)} expected strings:\n' +
            '\n'.join(f'       - "{s}"' for s in missing_strings)
        )
    else:
        pass_test('Expected strings present', f'{len(EXPECTED_STRINGS)}/{len(EXPECTED_STRINGS)} found')

    # Test 6: UTF-8 encoding validation
    log('Test 6: UTF-8 인코딩 확인')
    try:
        # Try to encode and decode - if it fails, encoding is wrong
        encoded = content.encode('utf-8')
        decoded = encoded.decode('utf-8')

        # Check if round-trip is successful
        if decoded == content:
            pass_test('UTF-8 encoding valid')
        else:
            fail_test('UTF-8 encoding', 'Content changed after UTF-8 round-trip encoding')
    except Exception as e:
        fail_test('UTF-8 encoding', f'Encoding validation failed: {e}')

    # Test 7: Specific error messages validation
    log('Test 7: 특정 에러 메시지 검증')
    specific_tests = [
        {'key': 'AUTH_FAILED', 'text': '사용자 이름 또는 비밀번호가 올바르지 않습니다.'},
        {'key': 'AUTH_SESSION_EXPIRED', 'text': '세션이 만료되었습니다.'},
        {'key': 'NETWORK_ERROR', 'text': '네트워크 연결에 실패했습니다.'},
    ]

    specific_tests_passed = 0
    for test in specific_tests:
        # Look for the error message definition
        # Match: 'KEY': { ... problem: 'text', ...
        # Use simpler regex that just checks if key and text are both present
        key_present = test['key'] in content
        text_present = test['text'] in content

        if key_present and text_present:
            # Verify they're near each other (within 200 characters)
            key_pos = content.find(test['key'])
            text_pos = content.find(test['text'], key_pos)
            if text_pos >= 0 and (text_pos - key_pos) < 200:
                specific_tests_passed += 1
            else:
                fail_test(f"Error message: {test['key']}", f"Key and text not associated: \"{test['text']}\"")
                break
        else:
            fail_test(f"Error message: {test['key']}", f"Message not found or corrupted: \"{test['text']}\"")
            break

    if specific_tests_passed == len(specific_tests):
        pass_test('Error messages valid', f'{specific_tests_passed}/{len(specific_tests)} validated')

    print_summary()


def print_summary():
    """Print test results summary"""
    print()
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE)
    log('테스트 결과', BLUE)
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE)
    print()

    total = tests_passed + tests_failed
    log(f'통과: {tests_passed}/{total}', GREEN if tests_passed > 0 else RESET)
    log(f'실패: {tests_failed}/{total}', RED if tests_failed > 0 else RESET)
    print()

    if tests_failed > 0:
        log('실패한 테스트:', RED)
        for error in errors:
            log(f"  - {error['test']}", RED)
            log(f"    {error['reason']}", YELLOW)
        print()
        log('❌ 한글 인코딩 검증 실패', RED)
        print()
        log('해결 방법:', YELLOW)
        log('  1. errorMessages.ts 파일을 UTF-8로 다시 저장', YELLOW)
        log('  2. T302 작업 참조: 파일 전체를 정상 한글로 재작성', YELLOW)
        log('  3. Pre-commit hook 설치: ./.githooks/install.sh', YELLOW)
        print()
        sys.exit(1)
    else:
        log('✅ 모든 테스트 통과!', GREEN)
        log('   한글 텍스트가 올바르게 인코딩되어 있습니다.', GREEN)
        print()
        sys.exit(0)


if __name__ == '__main__':
    run_tests()
