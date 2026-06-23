import { useEffect, useState } from "react";
import { authApi } from "../api/authApi";
import { profileApi } from "../api/profileApi";
import { ApiError } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loading from "../components/ui/Loading";
import type { User } from "../types/auth";
import type { PreferenceProfile } from "../types/profile";

function AspectWeightsTable({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) return null;
  return (
    <table className="key-value-table">
      <thead>
        <tr>
          <th>Аспект</th>
          <th>Вес</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([aspect, weight]) => (
          <tr key={aspect}>
            <td>{aspect}</td>
            <td>{weight.toFixed(3)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function hasAspectWeights(profile: PreferenceProfile): boolean {
  const weights = profile.aspect_weights ?? {};
  return Object.keys(weights).length > 0;
}

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<PreferenceProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([authApi.getMe(), profileApi.getPreferenceProfile()])
      .then(([userData, profileData]) => {
        if (!cancelled) {
          setUser(userData);
          setProfile(profileData);
        }
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
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (!user) return null;

  const aspectWeights = profile?.aspect_weights ?? {};
  const showWeights = profile != null && hasAspectWeights(profile);

  return (
    <>
      <h1 className="page-title">Профиль пользователя</h1>
      <div className="card profile-block">
        <p>
          <strong>Имя пользователя:</strong> {user.username}
        </p>
        <p>
          <strong>Email:</strong> {user.email}
        </p>
      </div>

      <div className="card profile-block">
        <h3>Вес аспектов</h3>
        {showWeights ? (
          <AspectWeightsTable data={aspectWeights} />
        ) : (
          <p className="empty-state" style={{ margin: 0 }}>
            Профиль предпочтений будет уточняться по мере добавления отзывов.
          </p>
        )}
      </div>
    </>
  );
}
