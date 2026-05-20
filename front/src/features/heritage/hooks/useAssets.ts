/**
 * Heritage assets view-model (MVVM hook).
 * See: document/coding_convention.md §4.1
 */
import { useCallback, useEffect, useRef, useState } from 'react';

import {
    type Asset,
    type AssetCreatePayload,
    type AssetSummary,
    type AssetType,
    type AssetUpdatePayload,
    describeError,
    heritageApi,
} from '../../../api/client';

export interface UseAssetsOptions {
    /** Case-insensitive substring match on asset name. */
    search?: string;
    /** Filter by asset type. */
    typeFilter?: AssetType | null;
}

export interface UseAssetsState {
    assets: Asset[];
    summary: AssetSummary | null;
    isLoading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
    createAsset: (payload: AssetCreatePayload) => Promise<Asset>;
    updateAsset: (id: string, payload: AssetUpdatePayload) => Promise<Asset>;
    deleteAsset: (id: string) => Promise<void>;
}

export function useAssets(options: UseAssetsOptions = {}): UseAssetsState {
    const { search, typeFilter } = options;

    const [assets, setAssets] = useState<Asset[]>([]);
    const [summary, setSummary] = useState<AssetSummary | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // 마지막으로 시작된 refresh 의 순번. 늦게 도착한 응답은 무시해
    // 검색어를 빠르게 타이핑할 때의 race condition (stale write) 을 막는다.
    const requestSeq = useRef(0);

    const refresh = useCallback(async () => {
        const mySeq = ++requestSeq.current;
        setError(null);
        setIsLoading(true);
        try {
            const trimmed = search?.trim() || undefined;
            const [list, sum] = await Promise.all([
                heritageApi.listAssets({
                    search: trimmed,
                    type: typeFilter ?? undefined,
                }),
                heritageApi.getSummary(),
            ]);
            // 더 새로운 요청이 이미 시작됐다면 이 결과는 stale.
            if (mySeq !== requestSeq.current) return;
            setAssets(list);
            setSummary(sum);
        } catch (e) {
            if (mySeq !== requestSeq.current) return;
            console.error('[useAssets] refresh failed', e);
            setError(describeError(e, '자산을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'));
        } finally {
            if (mySeq === requestSeq.current) setIsLoading(false);
        }
    }, [search, typeFilter]);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    const createAsset = useCallback(
        async (payload: AssetCreatePayload) => {
            const created = await heritageApi.createAsset(payload);
            await refresh();
            return created;
        },
        [refresh],
    );

    const updateAsset = useCallback(
        async (id: string, payload: AssetUpdatePayload) => {
            const updated = await heritageApi.updateAsset(id, payload);
            await refresh();
            return updated;
        },
        [refresh],
    );

    const deleteAsset = useCallback(
        async (id: string) => {
            await heritageApi.deleteAsset(id);
            await refresh();
        },
        [refresh],
    );

    return {
        assets,
        summary,
        isLoading,
        error,
        refresh,
        createAsset,
        updateAsset,
        deleteAsset,
    };
}
