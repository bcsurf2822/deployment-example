"use client";

import { useState, useEffect } from "react";
import { User } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { formatDistanceToNow } from "date-fns";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
} from "@/components/ui/sidebar";
import {
  MessageCircle,
  Plus,
  Archive,
  User as UserIcon,
  Clock,
  Search,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface Conversation {
  session_id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  last_message_at: string;
  is_archived: boolean;
  metadata: Record<string, unknown> | null;
}

interface ConversationsSidebarProps {
  user: User | null;
  currentSessionId?: string;
  onNewConversation?: () => void;
  onSelectConversation?: (sessionId: string) => void;
}

export default function ConversationsSidebar({
  user,
  currentSessionId,
  onNewConversation,
  onSelectConversation,
}: ConversationsSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [archivedConversations, setArchivedConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const supabase = createClient();

  // Fetch conversations for the current user
  useEffect(() => {
    if (!user) return;

    const fetchConversations = async () => {
      try {
        setIsLoading(true);
        console.log("[ConversationsSidebar-fetchConversations] Fetching conversations for user:", user.id);

        const { data, error } = await supabase
          .from("conversations")
          .select("*")
          .eq("user_id", user.id)
          .order("last_message_at", { ascending: false });

        if (error) {
          console.error("[ConversationsSidebar-fetchConversations] Error:", error);
          return;
        }

        console.log("[ConversationsSidebar-fetchConversations] Fetched conversations:", data.length);
        
        // Separate active and archived conversations
        const active = data.filter(conv => !conv.is_archived);
        const archived = data.filter(conv => conv.is_archived);
        
        setConversations(active);
        setArchivedConversations(archived);
      } catch (err) {
        console.error("[ConversationsSidebar-fetchConversations] Error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [user, supabase]);

  // Filter conversations based on search query
  const filteredConversations = conversations.filter(conv =>
    conv.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.session_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredArchivedConversations = archivedConversations.filter(conv =>
    conv.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.session_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Helper function to get conversation title
  const getConversationTitle = (conversation: Conversation): string => {
    if (conversation.title) {
      return conversation.title;
    }
    // Generate a title from session_id if none exists
    const timestamp = conversation.created_at;
    const date = new Date(timestamp);
    return `Chat ${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  };

  // Helper function to format relative time
  const getRelativeTime = (timestamp: string): string => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return "Unknown";
    }
  };

  if (!user) {
    return (
      <Sidebar side="left" variant="sidebar" collapsible="icon">
        <SidebarHeader>
          <div className="flex items-center gap-2 px-4 py-2">
            <MessageCircle size={20} />
            <span className="font-semibold">Please Sign In</span>
          </div>
        </SidebarHeader>
      </Sidebar>
    );
  }

  return (
    <Sidebar side="left" variant="sidebar" collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-2">
            <MessageCircle size={20} />
            <span className="font-semibold">Conversations</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={onNewConversation}
            className="h-8 w-8 p-0"
            title="New Conversation"
          >
            <Plus size={16} />
          </Button>
        </div>
        
        {/* Search Bar */}
        <div className="px-4 pb-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {/* Active Conversations */}
        <SidebarGroup>
          <SidebarGroupLabel>Recent Conversations</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {isLoading ? (
                // Loading skeleton
                Array.from({ length: 5 }).map((_, index) => (
                  <SidebarMenuItem key={index}>
                    <SidebarMenuSkeleton showIcon />
                  </SidebarMenuItem>
                ))
              ) : filteredConversations.length === 0 ? (
                <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                  {searchQuery ? "No conversations found" : "No conversations yet"}
                  <br />
                  {!searchQuery && "Start a new chat to see conversations here"}
                </div>
              ) : (
                filteredConversations.map((conversation) => (
                  <SidebarMenuItem key={conversation.session_id}>
                    <SidebarMenuButton
                      onClick={() => onSelectConversation?.(conversation.session_id)}
                      isActive={currentSessionId === conversation.session_id}
                      className="flex flex-col items-start gap-1 h-auto py-2 px-3"
                    >
                      <div className="flex w-full items-center justify-between">
                        <div className="flex items-center gap-2">
                          <MessageCircle size={14} />
                          <span className="truncate text-sm font-medium">
                            {getConversationTitle(conversation)}
                          </span>
                        </div>
                      </div>
                      <div className="flex w-full items-center gap-1 text-xs text-muted-foreground">
                        <Clock size={10} />
                        <span>{getRelativeTime(conversation.last_message_at)}</span>
                      </div>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Archived Conversations */}
        {archivedConversations.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>
              <button
                onClick={() => setShowArchived(!showArchived)}
                className="flex w-full items-center justify-between"
              >
                <span>Archived ({archivedConversations.length})</span>
                <Archive size={14} />
              </button>
            </SidebarGroupLabel>
            {showArchived && (
              <SidebarGroupContent>
                <SidebarMenu>
                  {filteredArchivedConversations.map((conversation) => (
                    <SidebarMenuItem key={conversation.session_id}>
                      <SidebarMenuButton
                        onClick={() => onSelectConversation?.(conversation.session_id)}
                        isActive={currentSessionId === conversation.session_id}
                        className="flex flex-col items-start gap-1 h-auto py-2 px-3 opacity-75"
                      >
                        <div className="flex w-full items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Archive size={14} />
                            <span className="truncate text-sm font-medium">
                              {getConversationTitle(conversation)}
                            </span>
                          </div>
                        </div>
                        <div className="flex w-full items-center gap-1 text-xs text-muted-foreground">
                          <Clock size={10} />
                          <span>{getRelativeTime(conversation.last_message_at)}</span>
                        </div>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            )}
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton className="flex items-center gap-2 px-3 py-2">
              <UserIcon size={16} />
              <div className="flex flex-col items-start">
                <span className="text-sm font-medium truncate">
                  {user.email}
                </span>
                <span className="text-xs text-muted-foreground">
                  {conversations.length} conversations
                </span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}