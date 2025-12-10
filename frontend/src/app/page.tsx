// frontend/app/page.tsx
export default function HomePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Welcome to revove</h1>
      <p className="text-gray-700 max-w-xl">
        revove analyzes Google Reviews for Bozeman restaurants and generates concise,
        AI-powered &quot;what to order&quot; recommendations.
      </p>
      <a
        href="/places"
        className="inline-block px-4 py-2 rounded bg-blue-600 text-white font-medium hover:bg-blue-700 transition"
      >
        View places
      </a>
    </div>
  );
}
