"use client";

import { useEffect, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

interface GoogleCredentialResponse {
  credential: string;
  select_by: string;
}

interface GoogleOneTapConfig {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void | Promise<void>;
  use_fedcm_for_prompt?: boolean;
  auto_select?: boolean;
  context?: "signin" | "signup" | "use";
  itp_support?: boolean;
  nonce?: string;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: GoogleOneTapConfig) => void;
          prompt: () => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}

interface GoogleOneTapProps {
  clientId: string;
}

export default function GoogleOneTap({ clientId }: GoogleOneTapProps) {
  const router = useRouter();
  const initialized = useRef(false);

  useEffect(() => {
    const initializeGoogleOneTap = async () => {
      if (initialized.current || !window.google?.accounts?.id) {
        return;
      }

      initialized.current = true;

      const generateNonce = () => {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, (byte) =>
          byte.toString(16).padStart(2, "0")
        ).join("");
      };

      const nonce = generateNonce();
      const supabase = createClient();

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: GoogleCredentialResponse) => {
          try {
            const { data, error } = await supabase.auth.signInWithIdToken({
              provider: "google",
              token: response.credential,
              nonce,
            });

            if (error) {
              console.error("[google-onetap] Authentication error:", error);
              return;
            }

            if (data?.user) {
              const { error: profileError } = await supabase.rpc(
                "ensure_user_profile"
              );

              if (profileError) {
                console.error(
                  "[google-onetap] Error ensuring user profile:",
                  profileError
                );
              }

              router.refresh();
              router.push("/");
            }
          } catch (error) {
            console.error("[google-onetap] Unexpected error:", error);
          }
        },
        use_fedcm_for_prompt: true, // For Chrome's third-party cookie changes
        auto_select: false, // Don't auto-select if user has multiple accounts
        context: "signin", // Show "Sign in with Google" instead of "Sign up"
        itp_support: true, // Support for Intelligent Tracking Prevention
      });

      window.google.accounts.id.prompt();
    };

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = initializeGoogleOneTap;
    document.head.appendChild(script);

    return () => {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.disableAutoSelect();
      }
    };
  }, [clientId, router]);

  return null;
}
