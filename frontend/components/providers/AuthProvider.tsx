'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'

interface AuthContextType {
  user: User | null
  loading: boolean
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
})

export const useAuth = () => useContext(AuthContext)

const publicPaths = ['/auth/login', '/auth/callback', '/auth/signout', '/auth/auth-code-error']

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [initialized, setInitialized] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const supabase = createClient()

  // Initial auth check - only runs once
  useEffect(() => {
    if (initialized) return
    
    const checkUser = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser()
        setUser(user)
        setInitialized(true)
        
        const isPublicPath = publicPaths.some(path => pathname.startsWith(path))
        
        if (!user && !isPublicPath) {
          router.push('/auth/login')
        } else if (user && pathname === '/auth/login') {
          router.push('/')
        }
      } catch (error) {
        console.error('[AuthProvider] Error checking user:', error)
      } finally {
        setLoading(false)
      }
    }

    checkUser()
  }, [initialized, supabase, router, pathname])
  
  // Listen for auth state changes
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
      
      if (_event === 'SIGNED_IN') {
        router.push('/')
      } else if (_event === 'SIGNED_OUT') {
        router.push('/auth/login')
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [supabase, router])

  // Protect routes after initial load
  useEffect(() => {
    if (!initialized || loading) return
    
    const isPublicPath = publicPaths.some(path => pathname.startsWith(path))
    
    if (!user && !isPublicPath) {
      router.push('/auth/login')
    }
  }, [pathname, user, initialized, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, loading }}>
      {children}
    </AuthContext.Provider>
  )
}