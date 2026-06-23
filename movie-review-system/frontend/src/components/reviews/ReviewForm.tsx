import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { isAuthenticated } from "../../utils/auth";

interface ReviewFormProps {
  onSubmit: (reviewText: string, userRating: number) => Promise<void>;
  submitting: boolean;
}

export default function ReviewForm({ onSubmit, submitting }: ReviewFormProps) {
  const [reviewText, setReviewText] = useState("");
  const [userRating, setUserRating] = useState(8);

  if (!isAuthenticated()) {
    return (
      <p className="alert alert-info">
        Чтобы оставить отзыв, <Link to="/login">войдите</Link> в систему.
      </p>
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await onSubmit(reviewText.trim(), userRating);
    setReviewText("");
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h3>Оставить отзыв</h3>
      {submitting && (
        <p className="alert alert-info">
          Отзыв анализируется, это может занять несколько секунд.
        </p>
      )}
      <div className="form-group">
        <label htmlFor="review_text">Текст отзыва</label>
        <textarea
          id="review_text"
          value={reviewText}
          onChange={(e) => setReviewText(e.target.value)}
          required
          disabled={submitting}
        />
      </div>
      <div className="form-group">
        <label htmlFor="user_rating">Оценка (1–10)</label>
        <input
          id="user_rating"
          type="number"
          min={1}
          max={10}
          step={0.5}
          value={userRating}
          onChange={(e) => setUserRating(Number(e.target.value))}
          required
          disabled={submitting}
        />
      </div>
      <button type="submit" className="btn btn-primary" disabled={submitting}>
        {submitting ? "Анализ отзыва выполняется..." : "Оставить отзыв"}
      </button>
    </form>
  );
}
