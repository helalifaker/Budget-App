import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-key'

// Log warning if using placeholder values
if (supabaseUrl === 'https://placeholder.supabase.co' || supabaseAnonKey === 'placeholder-key') {
  console.warn(
    '⚠️  Using placeholder Supabase configuration. ' +
      'Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.'
  )
} else if (import.meta.env.DEV) {
  // In development, log configuration status
  console.log('[supabase] ✅ Supabase client initialized:', {
    url: supabaseUrl,
    hasAnonKey: !!supabaseAnonKey && supabaseAnonKey.length > 0,
    keyLength: supabaseAnonKey.length,
  })
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

// Diagnostic helper: Check session after initialization
if (import.meta.env.DEV) {
  supabase.auth.getSession().then(({ data: { session }, error }) => {
    if (error) {
      console.error('[supabase] Error checking initial session:', error)
    } else if (session) {
      console.log('[supabase] ✅ Initial session found:', {
        userId: session.user.id,
        email: session.user.email,
      })
    } else {
      console.log('[supabase] ℹ️ No initial session (user not logged in)')
    }
  })
}
