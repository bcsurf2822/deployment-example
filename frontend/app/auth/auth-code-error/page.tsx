/**
 * Authentication error page
 * Shown when OAuth or email confirmation fails
 */

import Link from 'next/link'

export default function AuthCodeErrorPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-purple-950 to-black flex items-center justify-center px-4">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-red-400/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl"></div>
      </div>

      {/* Error Card */}
      <div className="relative w-full max-w-md">
        <div className="bg-black/40 backdrop-blur-xl border border-red-400/20 rounded-2xl p-8 shadow-2xl">
          {/* Glow Effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-red-400/5 to-purple-600/5 rounded-2xl blur-xl"></div>
          
          <div className="relative text-center">
            {/* Error Icon */}
            <div className="mx-auto w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>

            {/* Header */}
            <h1 className="text-2xl font-bold text-white mb-4">
              Authentication Error
            </h1>
            <p className="text-gray-400 mb-8">
              There was an error with your authentication request. This could be due to an expired link or invalid code.
            </p>

            {/* Action Button */}
            <Link
              href="/auth/login"
              className="inline-block w-full bg-gradient-to-r from-yellow-400 to-yellow-600 hover:from-yellow-300 hover:to-yellow-500 text-black font-semibold py-3 px-4 rounded-lg transition-all duration-300 transform hover:scale-[1.02] shadow-lg shadow-yellow-400/25"
            >
              Try Again
            </Link>

            {/* Help Text */}
            <p className="text-gray-500 text-sm mt-4">
              If the problem persists, please contact support.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}