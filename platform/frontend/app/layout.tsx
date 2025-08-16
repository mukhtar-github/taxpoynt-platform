import React from 'react';
import './globals.css';

export const metadata = {
  title: 'TaxPoynt Platform - Nigerian E-Invoice Solution',
  description: 'Nigeria\'s Premier Intelligent Universal E-Invoicing Platform - Connect Every System, Automate Every Transaction',
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