'use client'

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

interface LoginFormProps {
  onSubmit: (formData: FormData) => Promise<void>;
  onGoogleSignIn: () => Promise<void>;
}

export default function LoginForm({ onSubmit, onGoogleSignIn }: LoginFormProps) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const searchParams = useSearchParams();

  useEffect(() => {
    const errorParam = searchParams.get('error');
    const messageParam = searchParams.get('message');
    
    if (errorParam) {
      setError(errorParam);
    }
    if (messageParam) {
      setMessage(messageParam);
    }
  }, [searchParams]);

  const handleFormSubmit = async (formData: FormData) => {
    setIsLoading(true);
    try {
      await onSubmit(formData);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      await onGoogleSignIn();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {isSignUp ? 'Create Account' : 'Welcome Back'}
        </h1>
        <p className="text-gray-600">
          {isSignUp ? 'Join RAG Studio' : 'Sign in to continue'}
        </p>
      </div>

      <button
        onClick={handleGoogleSignIn}
        disabled={isLoading}
        className="w-full mb-6 bg-white hover:bg-gray-50 border border-gray-300 hover:border-gray-400 text-gray-700 py-2.5 px-4 rounded-lg transition-all duration-200 flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        <span className="text-gray-700 font-medium">
          Continue with Google
        </span>
      </button>

      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">or continue with email</span>
        </div>
      </div>

      <form action={handleFormSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors duration-200"
            placeholder="Enter your email"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors duration-200"
            placeholder="Enter your password"
          />
        </div>

        <input
          type="hidden"
          name="isSignUp"
          value={isSignUp.toString()}
        />

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Loading...' : isSignUp ? 'Create Account' : 'Sign In'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <button
          onClick={() => setIsSignUp(!isSignUp)}
          className="text-gray-600 hover:text-gray-900 transition-colors text-sm"
        >
          {isSignUp 
            ? "Already have an account? Sign in" 
            : "Don't have an account? Sign up"
          }
        </button>
      </div>

      {(error || message) && (
        <div className="mt-4 text-center text-sm">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-2 rounded-lg mb-2">
              {error}
            </div>
          )}
          {message && (
            <div className="bg-green-50 border border-green-200 text-green-600 px-4 py-2 rounded-lg">
              {message}
            </div>
          )}
        </div>
      )}
    </>
  );
}