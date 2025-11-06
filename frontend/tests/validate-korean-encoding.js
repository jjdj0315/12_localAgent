#!/usr/bin/env node
/**
 * Korean text encoding validation test (T304, FR-115)
 *
 * Validates that errorMessages.ts contains proper Korean text
 * and no mojibake corruption from T302 fix.
 *
 * Run: node frontend/tests/validate-korean-encoding.js
 */

const fs = require('fs');
const path = require('path');

// ANSI colors
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const RESET = '\x1b[0m';

// Test configuration
const ERROR_MESSAGES_PATH = path.join(__dirname, '../src/lib/errorMessages.ts');

// Korean Unicode range: AC00-D7A3 (Hangul Syllables)
const KOREAN_CHAR_REGEX = /[\uAC00-\uD7A3]/;
const KOREAN_CHARS_REGEX = /[\uAC00-\uD7A3]+/g;

// Mojibake patterns (common corruption patterns)
const MOJIBAKE_PATTERNS = [
  /\ufffd/g,              // Replacement character �
  /\ufffd+/g,             // Multiple replacement characters
  /[\x80-\xFF]{3,}/g,     // Invalid UTF-8 sequences
  /\uFFFD{2,}/g,          // Multiple U+FFFD
];

// Expected Korean strings (from T302 fix)
const EXPECTED_STRINGS = [
  '사용자 이름 또는 비밀번호가 올바르지 않습니다.',
  '세션이 만료되었습니다.',
  '네트워크 연결에 실패했습니다.',
  '파일 크기가 너무 큽니다.',
  '대화를 찾을 수 없습니다.',
];

// Test results tracking
let testsPassed = 0;
let testsFailed = 0;
const errors = [];

function log(message, color = RESET) {
  console.log(`${color}${message}${RESET}`);
}

function pass(testName) {
  testsPassed++;
  log(`  ✅ ${testName}`, GREEN);
}

function fail(testName, reason) {
  testsFailed++;
  errors.push({ test: testName, reason });
  log(`  ❌ ${testName}`, RED);
  log(`     ${reason}`, YELLOW);
}

function runTests() {
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE);
  log('한글 텍스트 인코딩 검증 테스트 (T304, FR-115)', BLUE);
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE);
  console.log();

  // Test 1: File exists
  log('Test 1: errorMessages.ts 파일 존재 확인');
  if (!fs.existsSync(ERROR_MESSAGES_PATH)) {
    fail('File exists', `File not found: ${ERROR_MESSAGES_PATH}`);
    return printSummary();
  }
  pass('File exists');

  // Read file content
  let content;
  try {
    content = fs.readFileSync(ERROR_MESSAGES_PATH, 'utf8');
  } catch (error) {
    fail('File read', `Failed to read file: ${error.message}`);
    return printSummary();
  }

  // Test 2: File is not empty
  log('Test 2: 파일이 비어있지 않은지 확인');
  if (!content || content.trim().length === 0) {
    fail('File not empty', 'File is empty');
  } else {
    pass('File not empty');
  }

  // Test 3: Contains Korean characters
  log('Test 3: 한글 문자 존재 확인');
  if (!KOREAN_CHAR_REGEX.test(content)) {
    fail('Contains Korean', 'No Korean characters found in file');
  } else {
    const koreanMatches = content.match(KOREAN_CHARS_REGEX);
    const koreanStrings = koreanMatches ? koreanMatches.length : 0;
    pass(`Contains Korean (${koreanStrings} Korean text blocks found)`);
  }

  // Test 4: No mojibake patterns
  log('Test 4: Mojibake 패턴 존재하지 않음 확인');
  let hasMojibake = false;
  for (const pattern of MOJIBAKE_PATTERNS) {
    const matches = content.match(pattern);
    if (matches && matches.length > 0) {
      fail('No mojibake', `Found ${matches.length} mojibake pattern(s): ${pattern}`);
      hasMojibake = true;
      break;
    }
  }
  if (!hasMojibake) {
    pass('No mojibake patterns detected');
  }

  // Test 5: Expected strings present
  log('Test 5: 예상 한글 문자열 존재 확인');
  let missingStrings = [];
  for (const expectedString of EXPECTED_STRINGS) {
    if (!content.includes(expectedString)) {
      missingStrings.push(expectedString);
    }
  }
  if (missingStrings.length > 0) {
    fail(
      'Expected strings present',
      `Missing ${missingStrings.length} expected strings:\n` +
      missingStrings.map(s => `       - "${s}"`).join('\n')
    );
  } else {
    pass(`Expected strings present (${EXPECTED_STRINGS.length}/${EXPECTED_STRINGS.length})`);
  }

  // Test 6: UTF-8 encoding validation (via Buffer)
  log('Test 6: UTF-8 인코딩 확인');
  try {
    // Try to encode and decode - if it fails, encoding is wrong
    const buffer = Buffer.from(content, 'utf8');
    const decoded = buffer.toString('utf8');

    // Check if round-trip is successful
    if (decoded === content) {
      pass('UTF-8 encoding valid');
    } else {
      fail('UTF-8 encoding', 'Content changed after UTF-8 round-trip encoding');
    }
  } catch (error) {
    fail('UTF-8 encoding', `Encoding validation failed: ${error.message}`);
  }

  // Test 7: Specific error messages validation
  log('Test 7: 특정 에러 메시지 검증');
  const specificTests = [
    { key: 'AUTH_FAILED', text: '사용자 이름 또는 비밀번호가 올바르지 않습니다.' },
    { key: 'AUTH_SESSION_EXPIRED', text: '세션이 만료되었습니다.' },
    { key: 'NETWORK_ERROR', text: '네트워크 연결에 실패했습니다.' },
  ];

  let specificTestsPassed = 0;
  for (const test of specificTests) {
    // Look for the error message definition
    const regex = new RegExp(`['"]${test.key}['"]\\s*:\\s*{[^}]*problem\\s*:\\s*['"]${test.text}['"]`, 's');
    if (regex.test(content)) {
      specificTestsPassed++;
    } else {
      fail(`Error message: ${test.key}`, `Message not found or corrupted: "${test.text}"`);
      break;
    }
  }

  if (specificTestsPassed === specificTests.length) {
    pass(`Error messages valid (${specificTestsPassed}/${specificTests.length})`);
  }

  printSummary();
}

function printSummary() {
  console.log();
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE);
  log('테스트 결과', BLUE);
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', BLUE);
  console.log();

  const total = testsPassed + testsFailed;
  log(`통과: ${testsPassed}/${total}`, testsPassed > 0 ? GREEN : RESET);
  log(`실패: ${testsFailed}/${total}`, testsFailed > 0 ? RED : RESET);
  console.log();

  if (testsFailed > 0) {
    log('실패한 테스트:', RED);
    errors.forEach(({ test, reason }) => {
      log(`  - ${test}`, RED);
      log(`    ${reason}`, YELLOW);
    });
    console.log();
    log('❌ 한글 인코딩 검증 실패', RED);
    console.log();
    log('해결 방법:', YELLOW);
    log('  1. errorMessages.ts 파일을 UTF-8로 다시 저장', YELLOW);
    log('  2. T302 작업 참조: 파일 전체를 정상 한글로 재작성', YELLOW);
    log('  3. Pre-commit hook 설치: ./.githooks/install.sh', YELLOW);
    console.log();
    process.exit(1);
  } else {
    log('✅ 모든 테스트 통과!', GREEN);
    log('   한글 텍스트가 올바르게 인코딩되어 있습니다.', GREEN);
    console.log();
    process.exit(0);
  }
}

// Run tests
runTests();
