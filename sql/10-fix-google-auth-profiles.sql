-- ============================================================================
-- Fix Google Authentication User Profiles
-- ============================================================================
-- This migration ensures that Google-authenticated users are properly added
-- to the user_profiles table and improves the trigger to handle OAuth metadata
-- ============================================================================

-- Step 1: Add any existing OAuth users to user_profiles
-- This handles users who signed up before the trigger was properly configured
INSERT INTO public.user_profiles (id, email, full_name, created_at, updated_at)
SELECT 
    au.id,
    au.email,
    COALESCE(
        au.raw_user_meta_data->>'full_name',
        au.raw_user_meta_data->>'name',
        SPLIT_PART(au.email, '@', 1) -- Use email prefix as fallback
    ) as full_name,
    au.created_at,
    au.created_at as updated_at
FROM auth.users au
LEFT JOIN public.user_profiles up ON au.id = up.id
WHERE up.id IS NULL
ON CONFLICT (id) DO NOTHING;

-- Step 2: Drop existing trigger and function to recreate with improvements
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Step 3: Create improved handle_new_user function
-- This function now:
-- - Extracts full_name from OAuth metadata
-- - Handles conflicts gracefully
-- - Includes error handling that won't break authentication
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Insert the new user into user_profiles
    -- Extract full_name from metadata if available (for OAuth providers)
    INSERT INTO public.user_profiles (id, email, full_name, created_at, updated_at)
    VALUES (
        NEW.id, 
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name',
            SPLIT_PART(NEW.email, '@', 1) -- Use email prefix as fallback
        ),
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        full_name = COALESCE(user_profiles.full_name, EXCLUDED.full_name),
        updated_at = NOW();
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        -- Log the error but don't fail the auth process
        RAISE WARNING 'Error in handle_new_user trigger: %', SQLERRM;
        RETURN NEW;
END;
$$;

-- Step 4: Recreate the trigger
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Step 5: Create a function that can be called from the application
-- This ensures user profile exists and can be called after authentication
CREATE OR REPLACE FUNCTION public.ensure_user_profile()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    user_id uuid;
    user_email text;
    user_metadata jsonb;
    result json;
BEGIN
    -- Get the current user's ID from auth context
    user_id := auth.uid();
    
    -- If no user is authenticated, return error
    IF user_id IS NULL THEN
        RETURN json_build_object('error', 'Not authenticated');
    END IF;
    
    -- Get user details from auth.users
    SELECT email, raw_user_meta_data 
    INTO user_email, user_metadata
    FROM auth.users 
    WHERE id = user_id;
    
    -- Ensure user profile exists
    INSERT INTO public.user_profiles (id, email, full_name, created_at, updated_at)
    VALUES (
        user_id,
        user_email,
        COALESCE(
            user_metadata->>'full_name',
            user_metadata->>'name',
            SPLIT_PART(user_email, '@', 1)
        ),
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        full_name = COALESCE(user_profiles.full_name, EXCLUDED.full_name),
        updated_at = NOW()
    RETURNING json_build_object(
        'id', id,
        'email', email,
        'full_name', full_name,
        'is_admin', is_admin
    ) INTO result;
    
    RETURN result;
END;
$$;

-- Step 6: Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.ensure_user_profile() TO authenticated;

-- Step 7: Add helpful comment
COMMENT ON FUNCTION public.ensure_user_profile() IS 
'Ensures the authenticated user has a profile in user_profiles table. 
Can be called after authentication to guarantee profile exists.
Especially useful for OAuth providers like Google where the user might not
go through the normal signup flow.';

-- ============================================================================
-- Verification Query (run this to check if fix worked)
-- ============================================================================
-- SELECT 
--     au.id,
--     au.email,
--     au.raw_app_meta_data->>'provider' as auth_provider,
--     up.id as profile_id,
--     up.full_name,
--     up.email as profile_email
-- FROM auth.users au
-- LEFT JOIN public.user_profiles up ON au.id = up.id
-- WHERE au.raw_app_meta_data->>'provider' IS NOT NULL
-- ORDER BY au.created_at DESC;