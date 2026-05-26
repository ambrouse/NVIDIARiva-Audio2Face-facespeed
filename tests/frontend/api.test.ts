import { describe, expect, it } from 'vitest';
import { resolveApiUrl } from '../../frontend/src/services/api';

describe('resolveApiUrl', () => {
  it('keeps API calls same-origin by default for nginx proxy runtime', () => {
    expect(resolveApiUrl('/api/rag/status')).toBe('/api/rag/status');
    expect(resolveApiUrl('api/documents')).toBe('/api/documents');
  });

  it('does not rewrite absolute artifact or provider URLs', () => {
    expect(resolveApiUrl('http://127.0.0.1:6300/api/rag/status')).toBe('http://127.0.0.1:6300/api/rag/status');
  });
});
