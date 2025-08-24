import React from 'react';
import './globals.css';

export const metadata = {
  title: 'TaxPoynt - Secure E-invoicing Solution',
  description: 'Submit compliant e-invoices in seconds, not hours',
  manifest: '/manifest.json',
  icons: {
    icon: [
      {
        url: '/favicon.svg',
        type: 'image/svg+xml',
      },
      {
        url: '/favicon.ico',
        sizes: '16x16',
        type: 'image/x-icon',
      }
    ],
    apple: [
      {
        url: '/apple-touch-icon.png',
        sizes: '180x180',
        type: 'image/png',
      }
    ],
    other: [
      {
        rel: 'icon',
        url: '/icon-192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        rel: 'icon', 
        url: '/icon-512.png',
        sizes: '512x512',
        type: 'image/png',
      }
    ]
  },
  openGraph: {
    title: 'TaxPoynt - Nigerian E-invoice Leader',
    description: 'Submit compliant e-invoices in seconds, not hours',
    url: 'https://taxpoynt.com',
    siteName: 'TaxPoynt',
    images: [
      {
        url: '/icon-512.png',
        width: 512,
        height: 512,
        alt: 'TaxPoynt Logo',
      }
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TaxPoynt - Nigerian E-invoice Leader',
    description: 'Submit compliant e-invoices in seconds, not hours',
    images: ['/icon-512.png'],
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}