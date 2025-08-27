interface SettingsContainerProps {
  children: React.ReactNode;
}

export default function SettingsContainer({ children }: SettingsContainerProps) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">Manage your preferences and configuration</p>
      </div>
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        {children}
      </div>
    </div>
  );
}