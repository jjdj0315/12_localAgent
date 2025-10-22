"use client";

/**
 * React Query Provider Configuration
 *
 * Sets up React Query for data fetching and caching throughout the application.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Prevent automatic refetching in air-gapped environment
            refetchOnWindowFocus: false,
            refetchOnReconnect: false,
            // Retry failed requests up to 2 times
            retry: 2,
            // Consider data stale after 5 minutes
            staleTime: 5 * 60 * 1000,
            // Keep unused data in cache for 10 minutes (gcTime in v5)
            gcTime: 10 * 60 * 1000,
          },
          mutations: {
            // Retry mutations once on failure
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}
