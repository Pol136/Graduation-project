import { Link, useNavigate } from "react-router-dom";
import { clearToken, isAuthenticated } from "../../utils/auth";

export default function Header() {
  const navigate = useNavigate();
  const loggedIn = isAuthenticated();

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <header className="site-header">
      <div className="inner">
        <Link to="/movies" className="brand">
          Movie Review Analyzer
        </Link>
        <nav className="site-nav">
          <Link to="/movies">Фильмы</Link>
          <Link to="/recommendations">Рекомендации</Link>
          <Link to="/watchlist">Смотреть позже</Link>
          <Link to="/profile">Профиль</Link>
        </nav>
        <div className="auth-actions">
          {loggedIn ? (
            <button type="button" className="btn" onClick={handleLogout}>
              Выйти
            </button>
          ) : (
            <>
              <Link to="/login" className="btn">
                Войти
              </Link>
              <Link to="/register" className="btn btn-primary">
                Регистрация
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
