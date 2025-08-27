/**
 * Testimonials Section Component
 * ==============================
 * Extracted from LandingPage.tsx - Customer social proof and success stories
 */

import React from 'react';
import { getSectionBackground, TYPOGRAPHY_STYLES, combineStyles } from '../../design_system/style-utilities';

export interface TestimonialsSectionProps {
  className?: string;
}

interface TestimonialCardProps {
  quote: string;
  author: string;
  title: string;
  company: string;
  location: string;
  avatar?: string;
  rating: number;
  metrics?: {
    timeSaved?: string;
    moneySaved?: string;
    errorReduction?: string;
  };
}

const TestimonialCard: React.FC<TestimonialCardProps> = ({
  quote,
  author,
  title,
  company,
  location,
  avatar,
  rating,
  metrics
}) => {
  return (
    <div className="bg-white rounded-3xl p-8 shadow-xl border border-gray-100 relative overflow-hidden">
      
      {/* Rating Stars */}
      <div className="flex items-center mb-6">
        {[...Array(5)].map((_, index) => (
          <svg
            key={index}
            className={`w-5 h-5 ${index < rating ? 'text-yellow-400' : 'text-gray-300'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>

      {/* Quote */}
      <blockquote className="text-lg text-slate-700 mb-6 leading-relaxed">
        "{quote}"
      </blockquote>

      {/* Metrics */}
      {metrics && (
        <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl">
          {metrics.timeSaved && (
            <div className="text-center">
              <div className="text-lg font-bold text-green-600">{metrics.timeSaved}</div>
              <div className="text-xs text-slate-600">Time Saved</div>
            </div>
          )}
          {metrics.moneySaved && (
            <div className="text-center">
              <div className="text-lg font-bold text-blue-600">{metrics.moneySaved}</div>
              <div className="text-xs text-slate-600">Money Saved</div>
            </div>
          )}
          {metrics.errorReduction && (
            <div className="text-center">
              <div className="text-lg font-bold text-purple-600">{metrics.errorReduction}</div>
              <div className="text-xs text-slate-600">Error Reduction</div>
            </div>
          )}
        </div>
      )}

      {/* Author Info */}
      <div className="flex items-center">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg mr-4">
          {avatar || author.charAt(0)}
        </div>
        <div>
          <div className="font-bold text-slate-800">{author}</div>
          <div className="text-sm text-slate-600">{title}</div>
          <div className="text-sm text-blue-600 font-medium">{company} • {location}</div>
        </div>
      </div>

      {/* Verified Badge */}
      <div className="absolute top-4 right-4">
        <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold flex items-center">
          ✓ Verified Customer
        </div>
      </div>
    </div>
  );
};

export const TestimonialsSection: React.FC<TestimonialsSectionProps> = ({ className = '' }) => {
  const sectionBackground = getSectionBackground('slate');
  
  const headlineStyle = combineStyles(
    TYPOGRAPHY_STYLES.sectionHeadline,
    {
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }
  );

  const testimonials: TestimonialCardProps[] = [
    {
      quote: "TaxPoynt completely transformed our business operations. We went from spending 4 hours daily on tax compliance to having everything automated. Our FIRS rejection rate dropped from 60% to zero. The ROI was immediate and substantial.",
      author: "Adebayo Ogundimu",
      title: "Chief Financial Officer",
      company: "Lagos Manufacturing Ltd",
      location: "Lagos",
      rating: 5,
      metrics: {
        timeSaved: "32 hrs/week",
        moneySaved: "₦4.2M/year",
        errorReduction: "100%"
      }
    },
    {
      quote: "As a tech startup, we needed a solution that could scale with us. TaxPoynt's API integration with our systems was seamless. The real-time compliance tracking gives us peace of mind, and the cost savings allow us to invest more in product development.",
      author: "Fatima Abdullahi",
      title: "Co-founder & CTO",
      company: "InnovateTech Solutions",
      location: "Abuja",
      rating: 5,
      metrics: {
        timeSaved: "25 hrs/week",
        moneySaved: "₦1.8M/year",
        errorReduction: "95%"
      }
    },
    {
      quote: "The difference is night and day. Before TaxPoynt, we constantly missed deadlines and faced penalties. Now everything is automated, and we never worry about compliance. Our accountant says it's the best investment we've ever made.",
      author: "Chinedu Okechukwu",
      title: "Managing Director",
      company: "Port Harcourt Retail Group",
      location: "Port Harcourt",
      rating: 5,
      metrics: {
        timeSaved: "20 hrs/week",
        moneySaved: "₦2.1M/year",
        errorReduction: "98%"
      }
    },
    {
      quote: "We were skeptical about automation, but TaxPoynt proved us wrong. The platform integrated perfectly with our Odoo ERP system. Customer support is exceptional - they helped us optimize our entire workflow.",
      author: "Amina Hassan",
      title: "Finance Manager",
      company: "Northern Logistics Company",
      location: "Kano",
      rating: 5,
      metrics: {
        timeSaved: "18 hrs/week",
        moneySaved: "₦1.5M/year",
        errorReduction: "92%"
      }
    },
    {
      quote: "TaxPoynt's enterprise features are outstanding. The dedicated account manager ensures we get maximum value. The custom integrations with our SAP system work flawlessly. Highly recommended for large organizations.",
      author: "Olumide Adeyemi",
      title: "Head of Operations",
      company: "West African Enterprises",
      location: "Ibadan",
      rating: 5,
      metrics: {
        timeSaved: "45 hrs/week",
        moneySaved: "₦6.3M/year",
        errorReduction: "100%"
      }
    },
    {
      quote: "The mobile app is a game-changer for our field operations. We can submit invoices on-the-go and track compliance status in real-time. The offline capabilities ensure we never miss a submission even in remote areas.",
      author: "Grace Ekpo",
      title: "Operations Director",
      company: "Delta Oil Services",
      location: "Warri",
      rating: 5,
      metrics: {
        timeSaved: "15 hrs/week",
        moneySaved: "₦2.7M/year",
        errorReduction: "89%"
      }
    }
  ];

  return (
    <section 
      id="testimonials"
      className={`py-20 relative overflow-hidden ${sectionBackground.className} ${className}`}
      style={sectionBackground.style}
      aria-labelledby="testimonials-headline"
    >
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Enhanced Section Header */}
        <div className="text-center mb-20">
          {/* Premium Badge - Slate Theme */}
          <div 
            className="inline-flex items-center px-8 py-4 border-2 border-slate-200/50 text-slate-800 rounded-full text-base font-bold mb-8 shadow-xl hover:shadow-slate-200/40 transition-all duration-300 hover:scale-105"
            style={{
              background: 'linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="w-3 h-3 rounded-full mr-3 bg-slate-700" aria-hidden="true"></span>
            Real Stories from Real Customers
          </div>
          
          {/* Dramatic Headline */}
          <div className="relative mb-8">
            <h2 
              id="testimonials-headline"
              className="text-5xl md:text-7xl font-black text-slate-900 mb-4 leading-[0.9] tracking-tight"
              style={headlineStyle}
            >
              <span className="text-slate-700">Join</span>
              <span className="text-green-600"> 2,500+ </span>
              <span className="text-slate-700">businesses</span>
              <br />
              <span className="relative inline-block">
                <span 
                  className="text-slate-700 italic font-black"
                  style={{ 
                    fontWeight: 950,
                    textShadow: '0 2px 4px rgba(71, 85, 105, 0.3)'
                  }}
                >
                  already saving millions
                </span>
                {/* Dramatic underline effect */}
                <div 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-slate-500 via-gray-500 to-slate-500 rounded-full opacity-90" 
                  aria-hidden="true"
                ></div>
              </span>
            </h2>
          </div>
          
          {/* Enhanced Subtitle */}
          <p 
            className="text-xl md:text-2xl text-slate-600 max-w-4xl mx-auto leading-relaxed font-medium"
            style={combineStyles(TYPOGRAPHY_STYLES.optimizedText, {
              textShadow: '0 2px 4px rgba(100, 116, 139, 0.2)'
            })}
          >
            Don't take our word for it. Here's what <span className="text-slate-800 font-bold">Nigerian business leaders</span> say about their TaxPoynt transformation.
          </p>
        </div>

        {/* Trust Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
          {[
            { number: "2,500+", label: "Happy Customers", icon: "😊" },
            { number: "4.9/5", label: "Customer Rating", icon: "⭐" },
            { number: "₦8.1B+", label: "Processed Volume", icon: "💰" },
            { number: "99.2%", label: "Customer Retention", icon: "🔄" }
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-4xl mb-2">{stat.icon}</div>
              <div 
                className="text-3xl md:text-4xl font-black text-slate-800 mb-2"
                style={{ textShadow: '0 2px 4px rgba(71, 85, 105, 0.2)' }}
              >
                {stat.number}
              </div>
              <div className="text-slate-600 font-medium text-sm md:text-base">
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard
              key={index}
              {...testimonial}
            />
          ))}
        </div>

        {/* Video Testimonials Section */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Watch <span className="text-blue-600">Success Stories</span>
          </h3>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: "Lagos Manufacturing: From Chaos to Control",
                duration: "3:42",
                views: "2.1K",
                thumbnail: "🏭",
                description: "See how Lagos Manufacturing automated their entire compliance process"
              },
              {
                title: "Tech Startup: Scaling Without Compliance Stress",
                duration: "2:58",
                views: "1.8K",
                thumbnail: "💻",
                description: "InnovateTech shares their journey from manual to automated compliance"
              },
              {
                title: "Retail Chain: Enterprise Transformation",
                duration: "4:15",
                views: "3.2K",
                thumbnail: "🏪",
                description: "How Port Harcourt Retail Group achieved 100% compliance automation"
              }
            ].map((video, index) => (
              <div 
                key={index}
                className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group"
              >
                {/* Video Thumbnail */}
                <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 h-48 flex items-center justify-center">
                  <div className="text-6xl">{video.thumbnail}</div>
                  <div className="absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-all duration-300"></div>
                  <div className="absolute center flex items-center justify-center">
                    <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center group-hover:bg-white transition-all duration-300">
                      <svg className="w-6 h-6 text-blue-600 ml-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M8 5v10l8-5-8-5z"/>
                      </svg>
                    </div>
                  </div>
                  
                  {/* Video Info Overlay */}
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="flex justify-between items-center text-white text-sm">
                      <span className="bg-black/50 px-2 py-1 rounded">{video.duration}</span>
                      <span className="bg-black/50 px-2 py-1 rounded">{video.views} views</span>
                    </div>
                  </div>
                </div>
                
                {/* Video Details */}
                <div className="p-6">
                  <h4 className="font-bold text-slate-800 mb-2 group-hover:text-blue-600 transition-colors">
                    {video.title}
                  </h4>
                  <p className="text-sm text-slate-600">
                    {video.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Industry Recognition */}
        <div className="mb-20">
          <h3 
            className="text-3xl md:text-4xl font-black text-center text-slate-800 mb-12"
            style={TYPOGRAPHY_STYLES.optimizedText}
          >
            Industry <span className="text-green-600">Recognition</span>
          </h3>
          
          <div className="grid md:grid-cols-4 gap-8">
            {[
              {
                award: "🏆 Best FinTech Solution 2024",
                organization: "Nigeria FinTech Awards",
                description: "Innovation in Tax Technology"
              },
              {
                award: "⭐ Top Rated Business Tool",
                organization: "SME Business Awards",
                description: "Highest Customer Satisfaction"
              },
              {
                award: "🛡️ FIRS Certified Partner",
                organization: "Federal Inland Revenue Service",
                description: "Official Integration Partner"
              },
              {
                award: "💼 Enterprise Solution of the Year",
                organization: "Lagos Chamber of Commerce",
                description: "Outstanding Business Impact"
              }
            ].map((recognition, index) => (
              <div 
                key={index}
                className="bg-white p-6 rounded-2xl text-center shadow-lg border border-gray-100"
              >
                <div className="text-2xl mb-3">{recognition.award.split(' ')[0]}</div>
                <h4 className="font-bold text-slate-800 mb-2 text-sm leading-tight">
                  {recognition.award.substring(2)}
                </h4>
                <p className="text-xs text-blue-600 font-medium mb-2">
                  {recognition.organization}
                </p>
                <p className="text-xs text-slate-600">
                  {recognition.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Customer Success Metrics */}
        <div className="bg-gradient-to-r from-green-500 to-blue-600 rounded-3xl p-8 md:p-12 text-white mb-20">
          <div className="text-center mb-8">
            <h3 className="text-3xl md:text-4xl font-black mb-4">
              📊 Customer Success by the Numbers
            </h3>
            <p className="text-xl opacity-90">
              Real results from real Nigerian businesses using TaxPoynt
            </p>
          </div>
          
          <div className="grid md:grid-cols-5 gap-6">
            {[
              { metric: "Average Time Saved", value: "28 hrs/week", improvement: "+85%" },
              { metric: "Average Money Saved", value: "₦2.4M/year", improvement: "+340% ROI" },
              { metric: "Error Reduction", value: "96%", improvement: "From 60% to 2.4%" },
              { metric: "Compliance Rate", value: "99.8%", improvement: "Never miss deadlines" },
              { metric: "Customer Satisfaction", value: "4.9/5", improvement: "Industry leading" }
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-black mb-2">{stat.value}</div>
                <div className="text-sm opacity-90 mb-1">{stat.metric}</div>
                <div className="text-xs bg-white/20 rounded-full px-2 py-1">
                  {stat.improvement}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Social Proof CTA */}
        <div className="text-center">
          <div className="mb-8">
            <h3 
              className="text-3xl md:text-4xl font-black text-slate-800 mb-6"
              style={TYPOGRAPHY_STYLES.optimizedText}
            >
              Ready to join the <span className="text-green-600">success stories</span>?
            </h3>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Your business could be our next success story. Join the thousands of Nigerian businesses already saving millions with TaxPoynt.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button
              onClick={() => {
                const router = { push: (path: string) => window.location.href = path };
                router.push('/auth/signup');
              }}
              className="text-xl px-12 py-6 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-green-500/40 transition-all duration-300 hover:scale-105"
            >
              🚀 Start My Success Story
            </button>
            
            <button
              onClick={() => {
                document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xl px-12 py-6 border-2 border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 hover:text-slate-900 font-bold rounded-2xl shadow-lg hover:shadow-slate-200/50 transition-all duration-300"
            >
              View Success Pricing
            </button>
          </div>

          {/* Final Social Proof */}
          <div className="inline-flex items-center px-6 py-3 bg-slate-100/80 text-slate-800 rounded-full text-base font-bold border border-slate-200/50">
            <span className="mr-2" aria-hidden="true">🎯</span>
            Join 2,500+ happy customers • 99.2% retention rate • 4.9/5 satisfaction
            <span className="ml-2" aria-hidden="true">🎯</span>
          </div>
        </div>
      </div>
    </section>
  );
};
