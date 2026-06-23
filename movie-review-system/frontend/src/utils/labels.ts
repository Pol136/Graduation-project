const SENTIMENT_LABELS: Record<string, string> = {
  positive: "положительный",
  neutral: "нейтральный",
  negative: "отрицательный",
};

export function sentimentLabel(sentiment: string): string {
  return SENTIMENT_LABELS[sentiment.toLowerCase()] ?? sentiment;
}

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function formatGenres(genres: string[] | null | undefined): string {
  if (!genres?.length) return "—";
  return genres.join(", ");
}

export function formatRating(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toFixed(1);
}
