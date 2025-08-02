-- Fix missing RLS policies for users to insert their own requests
-- Run this script to allow users to insert their own requests

-- Add policy for users to insert their own requests
CREATE POLICY "Users can insert their own requests"
ON requests
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Verify the policy was created
SELECT schemaname, tablename, policyname, cmd, roles 
FROM pg_policies 
WHERE tablename = 'requests' 
AND policyname = 'Users can insert their own requests';