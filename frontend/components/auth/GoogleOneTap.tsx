'use client'

import { useEffect, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: any) => void
          prompt: () => void
          disableAutoSelect: () => void
        }
      }
    }
  }
}

interface GoogleOneTapProps {
  clientId: string
}

export default function GoogleOneTap({ clientId }: GoogleOneTapProps) {
  const router = useRouter()
  const initialized = useRef(false)

  useEffect(() => {
    const initializeGoogleOneTap = async () => {
      // Check if already initialized or if Google library is not loaded
      if (initialized.current || !window.google?.accounts?.id) {
        return
      }

      initialized.current = true

      // Generate a nonce for security
      const generateNonce = () => {
        const array = new Uint8Array(32)
        crypto.getRandomValues(array)
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
      }

      const nonce = generateNonce()
      const supabase = createClient()

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: any) => {
          try {
            const { data, error } = await supabase.auth.signInWithIdToken({
              provider: 'google',
              token: response.credential,
              nonce,
            })

            if (error) {
              console.error('[google-onetap] Authentication error:', error)
              return
            }

            if (data?.user) {
              // Ensure user profile exists
              const { error: profileError } = await supabase.rpc('ensure_user_profile')
              
              if (profileError) {
                console.error('[google-onetap] Error ensuring user profile:', profileError)
              }

              // Redirect to home page
              router.refresh()
              router.push('/')
            }
          } catch (error) {
            console.error('[google-onetap] Unexpected error:', error)
          }
        },
        use_fedcm_for_prompt: true, // For Chrome's third-party cookie changes
        auto_select: false, // Don't auto-select if user has multiple accounts
        context: 'signin', // Show "Sign in with Google" instead of "Sign up"
        itp_support: true, // Support for Intelligent Tracking Prevention
      })

      // Show the One Tap prompt
      window.google.accounts.id.prompt()
    }

    // Load Google Identity Services library
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = initializeGoogleOneTap
    document.head.appendChild(script)

    return () => {
      // Cleanup
      if (window.google?.accounts?.id) {
        window.google.accounts.id.disableAutoSelect()
      }
    }
  }, [clientId, router])

  return null // This component doesn't render anything visible
}