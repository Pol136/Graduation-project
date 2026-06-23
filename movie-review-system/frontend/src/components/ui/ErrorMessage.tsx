export default function ErrorMessage({ message }: { message: string }) {
  return <div className="alert alert-error" role="alert">{message}</div>;
}
