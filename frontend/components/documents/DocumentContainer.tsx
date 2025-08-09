interface DocumentContainerProps {
  children: React.ReactNode;
}

export default function DocumentContainer({ children }: DocumentContainerProps) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
        <p className="mt-2 text-gray-600">Browse and manage your document collection</p>
      </div>
      {children}
    </div>
  );
}