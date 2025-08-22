import React from 'react';
import './globals.css';

export const metadata = {
  title: 'TaxPoynt - Send Invoices to FIRS in Seconds',
  description: 'Stop wasting hours on FIRS compliance. TaxPoynt sends your invoices directly to FIRS - one click and you\'re compliant, every time.',
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