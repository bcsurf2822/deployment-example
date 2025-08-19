'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'

export async function login(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    console.error('[login-action] Login error:', error)
    
    if (error.message.includes('Email not confirmed')) {
      redirect('/auth/login?error=Please check your email and click the confirmation link before signing in')
    }
    if (error.message.includes('Invalid login credentials')) {
      redirect('/auth/login?error=Invalid email or password')
    }
    
    redirect(`/auth/login?error=${encodeURIComponent(error.message)}`)
  }

  console.log('[login-action] Login successful')
  
  revalidatePath('/', 'layout')
  
  redirect('/')
}

export async function signup(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { data: result, error } = await supabase.auth.signUp(data)

  if (error) {
    console.error('[signup-action] Signup error:', error)
    redirect(`/auth/login?error=${encodeURIComponent(error.message)}`)
  }

  console.log('[signup-action] Signup successful')
  
  revalidatePath('/', 'layout')
  
  if (result.user && !result.user.email_confirmed_at) {
    redirect('/auth/login?message=Check your email and click the confirmation link to complete registration')
  }
  
  if (result.user && result.session) {
    redirect('/')
  }
  
  redirect('/auth/login?message=Account created successfully! You can now sign in.')
}

export async function signInWithGoogle() {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'}/auth/callback`,
    },
  })

  if (error) {
    console.error('[google-signin-action] Google sign-in error:', error)
    redirect('/auth/login?error=Could not authenticate with Google')
  }

  if (data.url) {
    redirect(data.url)
  }
}