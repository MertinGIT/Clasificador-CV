export function Button({ children, ...props }) {
  return (
    <button
      {...props}
      className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {children}
    </button>
  );
}
