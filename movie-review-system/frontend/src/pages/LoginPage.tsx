import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../api/authApi";
import { ApiError } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";
import { setToken } from "../utils/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await authApi.login({ email, password });
      setToken(access_token);
      navigate("/movies");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail ?? "Неверный email или пароль");
      } else {
        setError("Не удалось войти. Проверьте подключение к серверу.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="page-title">Вход</h1>
      {error && <ErrorMessage message={error} />}
      <form onSubmit={handleSubmit} className="card" style={{ maxWidth: 400 }}>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Вход..." : "Войти"}
        </button>
        <p style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
          Нет аккаунта? <Link to="/register">Регистрация</Link>
        </p>
      </form>
    </>
  );
}
