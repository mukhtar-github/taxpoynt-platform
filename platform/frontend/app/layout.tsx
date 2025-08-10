import React from 'react';
import './globals.css';

export const metadata = {
  title: 'TaxPoynt Platform',
  description: 'Enterprise Nigerian e-invoicing and business integration platform',
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