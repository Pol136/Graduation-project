import { useCallback, useEffect, useState } from "react";
import { recommendationsApi } from "../api/recommendationsApi";
import { ApiError } from "../api/client";
import RecommendationCard from "../components/recommendations/RecommendationCard";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loading from "../components/ui/Loading";
import type { Recommendation } from "../types/recommendation";

export default function RecommendationsPage() {
  const [items, setItems] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (refresh: boolean) => {
    return recommendationsApi.getRecommendations(10, refresh);
  }, []);

  useEffect(() => {
    let cancelled = false;
    load(false)
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Не удалось загрузить данные."
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      const data = await recommendationsApi.refreshRecommendations(10);
      setItems(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось обновить рекомендации."
      );
    } finally {
      setRefreshing(false);
    }
  }

  if (loading) return <Loading />;

  return (
    <>
      <h1 className="page-title">Рекомендации</h1>
      <p style={{ marginBottom: "1rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? "Рекомендации обновляются..." : "Обновить рекомендации"}
        </button>
      </p>
      {error && <ErrorMessage message={error} />}
      {items.length === 0 ? (
        <p className="empty-state">Пока нет доступных рекомендаций.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {items.map((item) => (
            <RecommendationCard key={item.recommendation_id} item={item} />
          ))}
        </div>
      )}
    </>
  );
}
