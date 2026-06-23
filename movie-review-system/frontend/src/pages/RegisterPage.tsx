import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/authApi";
import { ApiError } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authApi.register({ username, email, password });
      navigate("/login");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail ?? err.message);
      } else {
        setError("Не удалось зарегистрироваться.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="page-title">Регистрация</h1>
      {error && <ErrorMessage message={error} />}
      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: 400 }}>
        <div className="form-group">
          <label htmlFor="username">Имя пользователя</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Пароль (мин. 8 символов)</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Регистрация..." : "Зарегистрироваться"}
        </button>
        <p style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </form>
    </>
  );
}
