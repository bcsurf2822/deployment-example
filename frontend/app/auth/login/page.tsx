'use client'

import { Suspense } from 'react';
import AuthContainer from '@/components/auth/AuthContainer';
import LoginForm from '@/components/auth/LoginForm';
import { login, signup, signInWithGoogle } from './actions';

function LoginContent() {
  const handleSubmit = async (formData: FormData) => {
    const isSignUp = formData.get('isSignUp') === 'true';
    if (isSignUp) {
      await signup(formData);
    } else {
      await login(formData);
    }
  };

  return (
    <AuthContainer>
      <LoginForm 
        onSubmit={handleSubmit}
        onGoogleSignIn={signInWithGoogle}
      />
    </AuthContainer>
  );
}

function LoginLoading() {
  return (
    <AuthContainer>
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded mb-4"></div>
        <div className="h-4 bg-gray-200 rounded mb-8"></div>
        <div className="h-10 bg-gray-200 rounded mb-6"></div>
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded"></div>
      </div>
    </AuthContainer>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginLoading />}>
      <LoginContent />
    </Suspense>
  );
}