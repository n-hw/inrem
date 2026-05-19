/**
 * Unit tests for `describeError` — pure function so jest-expo runtime
 * troubles don't apply (no React, no Expo).
 */
import { AxiosError, AxiosHeaders } from 'axios';

import { describeError } from '../client';

function axiosErrFromStatus(status: number, opts: { detail?: string; headers?: Record<string, string> } = {}): AxiosError {
    const err = new AxiosError('Request failed', undefined, undefined, undefined, {
        status,
        statusText: '',
        data: opts.detail ? { detail: opts.detail } : {},
        headers: new AxiosHeaders(opts.headers ?? {}),
        config: { headers: new AxiosHeaders() } as any,
    } as any);
    return err;
}

describe('describeError', () => {
    test('non-axios error → fallback', () => {
        expect(describeError(new Error('boom'))).toBe('문제가 발생했어요.');
        expect(describeError('string error', '커스텀')).toBe('커스텀');
    });

    test('timeout (ECONNABORTED) → timeout message', () => {
        const err = new AxiosError('timeout', 'ECONNABORTED');
        expect(describeError(err)).toMatch(/시간/);
    });

    test('no response (offline) → offline message', () => {
        const err = new AxiosError('Network Error');
        expect(describeError(err)).toMatch(/인터넷/);
    });

    test('401 → 로그인 메시지', () => {
        expect(describeError(axiosErrFromStatus(401))).toMatch(/로그인/);
    });

    test('403 → 접근 권한', () => {
        expect(describeError(axiosErrFromStatus(403))).toMatch(/권한/);
    });

    test('410 with detail → detail surfaces', () => {
        expect(
            describeError(axiosErrFromStatus(410, { detail: '유예 기간이 만료됐어요.' })),
        ).toBe('유예 기간이 만료됐어요.');
    });

    test('429 with Retry-After → seconds included', () => {
        expect(
            describeError(axiosErrFromStatus(429, { headers: { 'retry-after': '60' } })),
        ).toMatch(/60초/);
    });

    test('429 without Retry-After → generic 잠시 후', () => {
        expect(describeError(axiosErrFromStatus(429))).toMatch(/잠시 후/);
    });

    test('5xx → 서버 응답 메시지', () => {
        expect(describeError(axiosErrFromStatus(500))).toMatch(/서버/);
        expect(describeError(axiosErrFromStatus(503))).toMatch(/서버/);
    });

    test('unknown status → fallback', () => {
        expect(describeError(axiosErrFromStatus(418), '🫖')).toBe('🫖');
    });
});
