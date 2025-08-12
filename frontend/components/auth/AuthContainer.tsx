import { ReactNode } from 'react';

interface AuthContainerProps {
  children: ReactNode;
}

export default function AuthContainer({ children }: AuthContainerProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center px-4">
      <div className="relative w-full max-w-md">
        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-lg">
          {children}
        </div>
      </div>
    </div>
  );
}