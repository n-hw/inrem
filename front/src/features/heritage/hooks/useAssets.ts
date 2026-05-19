/**
 * Heritage assets view-model (MVVM hook).
 * See: document/coding_convention.md §4.1
 */
import { useCallback, useEffect, useState } from 'react';

import {
    type Asset,
    type AssetCreatePayload,
    type AssetSummary,
    type AssetUpdatePayload,
    heritageApi,
} from '../../../api/client';

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

export function useAssets(): UseAssetsState {
    const [assets, setAssets] = useState<Asset[]>([]);
    const [summary, setSummary] = useState<AssetSummary | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        setError(null);
        setIsLoading(true);
        try {
            const [list, sum] = await Promise.all([
                heritageApi.listAssets(),
                heritageApi.getSummary(),
            ]);
            setAssets(list);
            setSummary(sum);
        } catch (e) {
            console.error('[useAssets] refresh failed', e);
            setError('자산을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.');
        } finally {
            setIsLoading(false);
        }
    }, []);

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
