export function Card({ children }) {
  return (
    <div className="rounded-lg border border-gray-300 bg-white p-6 shadow-md">
      {children}
    </div>
  );
}
