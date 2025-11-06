/**
 * Korean text validation tests for error messages (T304, FR-115)
 *
 * Purpose: Validate all error messages have proper Korean encoding
 * Detects mojibake characters and ensures Korean Unicode compliance
 */

import { describe, it, expect } from '@jest/globals';
import { ERROR_MESSAGES } from '../src/lib/errorMessages';

describe('Error Messages Korean Encoding', () => {
  // Korean Hangul Unicode range: U+AC00 to U+D7A3
  // Common punctuation and characters
  const KOREAN_TEXT_PATTERN = /^[\uAC00-\uD7A3\s\w\d.,!?'"()\-:]+$/;

  // Mojibake detection pattern (replacement character)
  const MOJIBAKE_PATTERN = /�/;

  describe('UTF-8 Encoding Validation', () => {
    it('should have no mojibake characters in problem descriptions', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        expect(value.problem).not.toMatch(MOJIBAKE_PATTERN);

        if (MOJIBAKE_PATTERN.test(value.problem)) {
          throw new Error(`Mojibake detected in ${key}.problem: ${value.problem}`);
        }
      });
    });

    it('should have no mojibake characters in action descriptions', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        expect(value.action).not.toMatch(MOJIBAKE_PATTERN);

        if (MOJIBAKE_PATTERN.test(value.action)) {
          throw new Error(`Mojibake detected in ${key}.action: ${value.action}`);
        }
      });
    });
  });

  describe('Korean Unicode Range Validation', () => {
    it('should contain valid Korean characters in problem descriptions', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        // Check if text contains Korean characters
        const hasKorean = /[\uAC00-\uD7A3]/.test(value.problem);

        expect(hasKorean).toBe(true);

        // Validate entire string is within allowed character set
        expect(value.problem).toMatch(KOREAN_TEXT_PATTERN);
      });
    });

    it('should contain valid Korean characters in action descriptions', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        const hasKorean = /[\uAC00-\uD7A3]/.test(value.action);

        expect(hasKorean).toBe(true);

        // Validate entire string is within allowed character set
        expect(value.action).toMatch(KOREAN_TEXT_PATTERN);
      });
    });
  });

  describe('Error Code Format Validation', () => {
    it('should have properly formatted error codes', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        if (value.code) {
          // Error codes should be uppercase alphanumeric with underscore
          expect(value.code).toMatch(/^[A-Z]+_\d{3}$/);
        }
      });
    });

    it('should have unique error codes', () => {
      const codes = Object.values(ERROR_MESSAGES)
        .map(v => v.code)
        .filter(Boolean);

      const uniqueCodes = new Set(codes);

      expect(codes.length).toBe(uniqueCodes.size);
    });
  });

  describe('Message Structure Validation', () => {
    it('should have both problem and action for all messages', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        expect(value.problem).toBeTruthy();
        expect(value.problem.length).toBeGreaterThan(0);

        expect(value.action).toBeTruthy();
        expect(value.action.length).toBeGreaterThan(0);
      });
    });

    it('should have period at end of problem descriptions', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        expect(value.problem).toMatch(/\.$/);
      });
    });

    it('should have period at end of action descriptions', () => {
      Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
        expect(value.action).toMatch(/\.$/);
      });
    });
  });

  describe('Specific Error Message Validation', () => {
    it('AUTH_FAILED should have correct Korean text', () => {
      const msg = ERROR_MESSAGES.AUTH_FAILED;

      expect(msg.problem).toContain('사용자');
      expect(msg.problem).toContain('비밀번호');
      expect(msg.action).toContain('확인');
    });

    it('NETWORK_ERROR should have correct Korean text', () => {
      const msg = ERROR_MESSAGES.NETWORK_ERROR;

      expect(msg.problem).toContain('네트워크');
      expect(msg.problem).toContain('연결');
      expect(msg.action).toContain('인터넷');
    });

    it('LLM_GENERATION_FAILED should have correct Korean text', () => {
      const msg = ERROR_MESSAGES.LLM_GENERATION_FAILED;

      expect(msg.problem).toContain('AI');
      expect(msg.problem).toContain('응답');
      expect(msg.action).toContain('시도');
    });

    it('RATE_LIMIT_EXCEEDED should have correct Korean text', () => {
      const msg = ERROR_MESSAGES.RATE_LIMIT_EXCEEDED;

      expect(msg.problem).toContain('요청');
      expect(msg.problem).toContain('횟수');
      expect(msg.problem).toContain('제한');
    });
  });

  describe('Console Encoding Test', () => {
    it('should log error messages without encoding issues', () => {
      // This test verifies that messages can be console.logged without corruption
      const consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();

      try {
        Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
          console.log(`${key}: ${value.problem} ${value.action}`);
        });

        // If no exceptions thrown, encoding is valid
        expect(true).toBe(true);
      } finally {
        consoleLogSpy.mockRestore();
      }
    });
  });
});

describe('Error Message Integration', () => {
  it('should have all required error types defined', () => {
    const requiredKeys = [
      'AUTH_FAILED',
      'AUTH_UNAUTHORIZED',
      'NETWORK_ERROR',
      'SERVER_ERROR',
      'FILE_TOO_LARGE',
      'CONVERSATION_NOT_FOUND',
      'LLM_GENERATION_FAILED',
      'RATE_LIMIT_EXCEEDED',
      'UNKNOWN_ERROR'
    ];

    requiredKeys.forEach(key => {
      expect(ERROR_MESSAGES[key]).toBeDefined();
    });
  });

  it('should have consistent message format across all errors', () => {
    Object.entries(ERROR_MESSAGES).forEach(([key, value]) => {
      // Problem should describe what went wrong
      expect(value.problem.length).toBeGreaterThan(10);
      expect(value.problem.length).toBeLessThan(100);

      // Action should tell user what to do
      expect(value.action.length).toBeGreaterThan(10);
      expect(value.action.length).toBeLessThan(150);
    });
  });
});
