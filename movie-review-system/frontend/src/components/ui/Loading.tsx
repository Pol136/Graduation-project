export default function Loading({ text = "Загрузка..." }: { text?: string }) {
  return <p className="loading">{text}</p>;
}
