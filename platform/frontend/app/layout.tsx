import React from 'react';
import './globals.css';
import { CombinedRoleProvider } from '../role_management/combined_provider';

export const metadata = {
  title: 'TaxPoynt - Secure E-invoicing Solution',
  description: 'Submit compliant e-invoices in seconds, not hours',
  manifest: '/manifest.json',
  icons: {
    icon: [
      {
        url: '/favicon.svg',
        type: 'image/svg+xml',
      }
    ],
    other: [
      {
        rel: 'icon',
        url: '/logo.svg',
        type: 'image/svg+xml',
      }
    ]
  },
  openGraph: {
    title: 'TaxPoynt - Secure E-invoicing Solution',
    description: 'Submit compliant e-invoices in seconds, not hours',
    url: 'https://taxpoynt.com',
    siteName: 'TaxPoynt',
    images: [
      {
        url: '/logo.svg',
        width: 200,
        height: 200,
        alt: 'TaxPoynt Logo',
      }
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TaxPoynt - Secure E-invoicing Solution',
    description: 'Submit compliant e-invoices in seconds, not hours',
    images: ['/logo.svg'],
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CombinedRoleProvider>
          {children}
        </CombinedRoleProvider>
      </body>
    </html>
  );
}
