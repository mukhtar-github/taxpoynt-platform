import React from 'react';
import Head from 'next/head';

export default function HomePage() {
  return (
    <>
      <Head>
        <title>TaxPoynt Platform</title>
        <meta name="description" content="Enterprise Nigerian e-invoicing platform" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#f9fafb', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ 
          maxWidth: '28rem', 
          width: '100%', 
          padding: '2rem' 
        }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h1 style={{ 
              fontSize: '2.5rem', 
              fontWeight: 'bold', 
              color: '#111827',
              marginBottom: '0.5rem'
            }}>
              TaxPoynt Platform
            </h1>
            <p style={{ 
              color: '#6b7280', 
              fontSize: '0.875rem' 
            }}>
              Enterprise Nigerian e-invoicing and business integration platform
            </p>
          </div>
          
          <div style={{ 
            backgroundColor: 'white', 
            padding: '2rem', 
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
          }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ 
                fontSize: '1.125rem', 
                fontWeight: '500', 
                color: '#111827',
                marginBottom: '0.5rem'
              }}>
                Platform Status
              </h2>
              <p style={{ 
                fontSize: '0.875rem', 
                color: '#6b7280' 
              }}>
                🚀 Frontend deployment successful
              </p>
            </div>
            
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ 
                backgroundColor: '#ecfdf5', 
                border: '1px solid #d1fae5', 
                borderRadius: '0.375rem', 
                padding: '1rem' 
              }}>
                <h3 style={{ 
                  fontSize: '0.875rem', 
                  fontWeight: '500', 
                  color: '#065f46',
                  marginBottom: '0.25rem'
                }}>
                  ✅ Backend API
                </h3>
                <p style={{ 
                  fontSize: '0.875rem', 
                  color: '#047857' 
                }}>
                  Railway deployment operational
                </p>
              </div>
              
              <div style={{ 
                backgroundColor: '#eff6ff', 
                border: '1px solid #dbeafe', 
                borderRadius: '0.375rem', 
                padding: '1rem' 
              }}>
                <h3 style={{ 
                  fontSize: '0.875rem', 
                  fontWeight: '500', 
                  color: '#1e40af',
                  marginBottom: '0.25rem'
                }}>
                  🏗️ Architecture
                </h3>
                <p style={{ 
                  fontSize: '0.875rem', 
                  color: '#1d4ed8' 
                }}>
                  Role-based microservices ready
                </p>
              </div>
              
              <div style={{ 
                backgroundColor: '#fef3c7', 
                border: '1px solid #fde68a', 
                borderRadius: '0.375rem', 
                padding: '1rem' 
              }}>
                <h3 style={{ 
                  fontSize: '0.875rem', 
                  fontWeight: '500', 
                  color: '#92400e',
                  marginBottom: '0.25rem'
                }}>
                  🔗 Integration Status
                </h3>
                <p style={{ 
                  fontSize: '0.875rem', 
                  color: '#b45309' 
                }}>
                  Ready for FIRS sandbox testing
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}