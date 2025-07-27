# Lesson Notes

## Add Fetch Messages Functionality

Add functionality to fetch messages from the "messages" table.

### Example Implementation

```typescript
export const fetchMessages = async (session_id: string, user_id: string) => {
  try {
    // Updated query approach - instead of using computed_session_user_id, query directly by session_id
    // This avoids the UUID format issue
    const { data, error } = await supabase
      .from("messages")
      .select("*")
      .eq("session_id", session_id)
      .order("created_at", { ascending: true });

    if (error) throw error;
    return data as Message[];
  } catch (error) {
    console.error("Error fetching messages:", error);
    throw error;
  }
};
```

### Set up own SMTP server in supabase

### Add Options for other providers
