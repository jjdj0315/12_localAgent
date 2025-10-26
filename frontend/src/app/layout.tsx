import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'Local LLM - 지방자치단체 AI 지원 시스템',
  description: '폐쇄망 환경에서 이용 가능한 Local LLM 웹 애플리케이션',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>
        <Providers>
          <AuthProvider>{children}</AuthProvider>
        </Providers>
      </body>
    </html>
  )
}
