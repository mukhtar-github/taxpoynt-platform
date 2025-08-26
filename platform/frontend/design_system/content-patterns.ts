/**
 * TaxPoynt Content Patterns & Constants
 * =====================================
 * Standardized content patterns for consistent messaging across the platform
 */

// ========================================
// EMOJI LIBRARY (Common UI Elements)
// ========================================

export const EMOJIS = {
  // Problem/Pain Point Emojis
  time: "⏰",
  error: "❌", 
  stress: "😰",
  document: "📝",
  calendar: "📅",
  connection: "🔗",
  
  // Solution/Positive Emojis
  check: "✅",
  rocket: "🚀",
  lightning: "⚡",
  shield: "🛡️",
  target: "🎯",
  sparkles: "✨",
  
  // Business/Professional Emojis
  chart: "📊",
  growth: "📈",
  handshake: "🤝",
  briefcase: "💼",
  money: "💰",
  trophy: "🏆",
  
  // Nigerian Context Emojis
  flag: "🇳🇬",
  building: "🏢",
  factory: "🏭",
  shop: "🏪",
} as const;

// ========================================
// NIGERIAN CITIES (For Attribution/Testimonials)
// ========================================

export const NIGERIAN_CITIES = [
  "Lagos",
  "Abuja", 
  "Kano",
  "Port Harcourt",
  "Ibadan",
  "Enugu",
  "Kaduna",
  "Jos",
  "Warri",
  "Benin City",
] as const;

// ========================================
// BUSINESS TYPES (For Realistic Testimonials)
// ========================================

export const BUSINESS_TYPES = [
  "Restaurant Owner",
  "Tech Company",
  "Manufacturing SME", 
  "Retailer",
  "Wholesaler",
  "Service Provider",
  "Import/Export Business",
  "Construction Company",
  "Consulting Firm",
  "E-commerce Store",
] as const;

// ========================================
// PROBLEM PATTERNS (Reusable Pain Points)
// ========================================

export const PROBLEM_PATTERNS = {
  timeWaste: {
    emoji: EMOJIS.time,
    title: "Hours Wasted Daily",
    commonPhrases: [
      "spend 3-4 hours every day",
      "time I should be growing my business",
      "manual processes eating up my day",
      "drowning in paperwork instead of serving customers"
    ]
  },
  
  constantErrors: {
    emoji: EMOJIS.error,
    title: "Constant Rejection Errors", 
    commonPhrases: [
      "get rejected 60% of the time",
      "wrong format, missing fields", 
      "never know what's wrong until it's too late",
      "validation errors with no clear guidance"
    ]
  },
  
  complianceStress: {
    emoji: EMOJIS.stress,
    title: "Compliance Anxiety",
    commonPhrases: [
      "always worried about penalties",
      "rules keep changing",
      "can't keep up with requirements",
      "sleep is becoming a luxury"
    ]
  },
  
  doubleEntry: {
    emoji: EMOJIS.document, 
    title: "Double Data Entry",
    commonPhrases: [
      "enter the same data twice",
      "manually re-type everything",
      "exhausting and error-prone",
      "duplicate work for the same information"
    ]
  },
  
  missedDeadlines: {
    emoji: EMOJIS.calendar,
    title: "Missing Deadlines",
    commonPhrases: [
      "sometimes miss submission deadlines",
      "penalties are crushing my cash flow", 
      "between running business and paperwork",
      "struggling to meet compliance timelines"
    ]
  },
  
  noIntegration: {
    emoji: EMOJIS.connection,
    title: "Software Disconnect", 
    commonPhrases: [
      "nothing talks to each other",
      "completely separate systems",
      "it's chaos trying to coordinate",
      "no single source of truth"
    ]
  }
} as const;

// ========================================
// PROBLEMS DATA - For ProblemCard component
// ========================================

export const PROBLEMS_DATA = [
  {
    emoji: "🏢",
    title: "Multi-System Chaos",
    quote: "Our enterprise runs 5+ disconnected business systems - SAP ERP, Salesforce CRM, multiple POS systems, e-commerce platforms. Data silos cost us millions in operational inefficiency.",
    attribution: "Lagos Financial Services Group"
  },
  {
    emoji: "📊",
    title: "Compliance at Scale", 
    quote: "With thousands of invoices monthly across multiple subsidiaries, manual invoice compliance consumes 40% of our IT resources. We're maintaining compliance infrastructure instead of innovating.",
    attribution: "Abuja Manufacturing Conglomerate"
  },
  {
    emoji: "🔄",
    title: "Integration Infrastructure Nightmare",
    quote: "Every new business system requires months of custom API development and ongoing maintenance. Simple changes become expensive IT projects that drain our technical resources.",
    attribution: "Port Harcourt Oil & Gas Enterprise"
  },
  {
    emoji: "📈",
    title: "Scalability Bottlenecks",
    quote: "Our current solutions break under enterprise volume - 1M+ transactions monthly, multiple business units, complex workflows. Growth is literally limited by our compliance infrastructure.",
    attribution: "Kano Agricultural Corporation"
  },
  {
    emoji: "🎯",
    title: "Strategic Resource Drain",
    quote: "Instead of focusing on market expansion and innovation, our enterprise resources are trapped in compliance paperwork and system maintenance. We're losing competitive advantage.",
    attribution: "Ibadan Technology Consortium"
  },
  {
    emoji: "⚡",
    title: "Performance Under Pressure", 
    quote: "Our fragmented compliance systems create bottlenecks during peak business periods. When we need speed most, manual processes slow us down and create operational risk.",
    attribution: "Enugu Retail Empire"
  }
];

// ========================================
// ENTERPRISE SOLUTIONS DATA - Direct problem solutions
// ========================================

export const ENTERPRISE_SOLUTIONS_DATA = [
  {
    emoji: "⚡",
    title: "Universal Integration Hub",
    problem: "Multi-System Chaos",
    quote: "TaxPoynt's 150+ API endpoints connect all our enterprise systems - SAP, Salesforce, Oracle, NetSuite - with real-time synchronization. One platform eliminated our data silos completely.",
    attribution: "Lagos Financial Services Group - CTO",
    metrics: "5+ systems → 1 unified platform"
  },
  {
    emoji: "🚀", 
    title: "Enterprise-Scale Automation",
    problem: "Compliance at Scale",
    quote: "We process 1M+ transactions monthly with <5 second response times and 99.9% uptime. Our IT teams now focus on innovation instead of compliance infrastructure maintenance.",
    attribution: "Abuja Manufacturing Conglomerate - IT Director",
    metrics: "40% IT resources → 100% innovation focus"
  },
  {
    emoji: "🔄",
    title: "Pre-Built API Ecosystem",
    problem: "Integration Infrastructure Nightmare", 
    quote: "No more custom API development. TaxPoynt's comprehensive integration library connects new systems in days, not months. Our technical resources are finally free for strategic projects.",
    attribution: "Port Harcourt Oil & Gas Enterprise - Lead Developer",
    metrics: "Months of development → Days of integration"
  },
  {
    emoji: "📈",
    title: "Unlimited Enterprise Capacity",
    problem: "Scalability Bottlenecks",
    quote: "Built for enterprise scale - 10M+ records monthly, horizontal scaling, load balancing. Our growth is no longer limited by compliance infrastructure constraints.",
    attribution: "Kano Agricultural Corporation - Operations Manager",
    metrics: "1M+ transactions → Unlimited capacity"
  },
  {
    emoji: "🎯", 
    title: "Strategic Resource Liberation",
    problem: "Strategic Resource Drain",
    quote: "TaxPoynt handles all compliance complexity while we focus on market expansion and innovation. It's transformed compliance from cost center to competitive advantage.",
    attribution: "Ibadan Technology Consortium - CEO",
    metrics: "Resource drain → Competitive advantage"
  },
  {
    emoji: "⚡",
    title: "Peak Performance Optimization",
    problem: "Performance Under Pressure",
    quote: "During peak business periods, TaxPoynt's unified platform maintains sub-5-second performance while our old fragmented systems would crash. Operational risk eliminated.",
    attribution: "Enugu Retail Empire - Head of Operations", 
    metrics: "System crashes → Peak performance"
  }
];

// ========================================
// ENTERPRISE FEATURES DATA - Detailed platform capabilities
// ========================================

export const ENTERPRISE_FEATURES_DATA = [
  {
    category: "Integration Ecosystem",
    icon: "🔗",
    title: "150+ Pre-Built API Integrations",
    description: "Connect seamlessly with SAP, Oracle, QuickBooks, Xero, Salesforce, and 145+ other enterprise systems through our comprehensive API library.",
    capabilities: [
      "Real-time data synchronization across all business systems",
      "Zero-code integration with drag-and-drop configuration",
      "Automated data mapping and transformation",
      "Built-in error handling and retry mechanisms"
    ],
    metrics: {
      label: "Integration Speed",
      value: "Hours, not months",
      detail: "from custom development"
    }
  },
  {
    category: "Enterprise Scale",
    icon: "🚀", 
    title: "Unlimited Transaction Processing",
    description: "Built for enterprise volume - handle millions of invoices monthly with <5 second response times and 99.9% guaranteed uptime.",
    capabilities: [
      "Horizontal scaling for unlimited growth",
      "Load balancing across multiple data centers",
      "Enterprise-grade disaster recovery",
      "24/7/365 monitoring and support"
    ],
    metrics: {
      label: "Performance",
      value: "1M+ invoices/month",
      detail: "with <5s response time"
    }
  },
  {
    category: "Compliance Automation",
    icon: "🛡️",
    title: "7-Standard Regulatory Framework",
    description: "Comprehensive compliance with UBL, WCO HS Code, NITDA GDPR, ISO 20022, ISO 27001, LEI, and PEPPOL standards.",
    capabilities: [
      "Automated regulatory updates and notifications",
      "Real-time compliance validation and reporting",
      "Audit trail generation and management", 
      "Multi-jurisdiction compliance support"
    ],
    metrics: {
      label: "Compliance Rate",
      value: "99.99% accuracy",
      detail: "across all regulations"
    }
  },
  {
    category: "Business Intelligence", 
    icon: "📊",
    title: "Advanced Analytics & Reporting",
    description: "Transform compliance data into strategic business insights with enterprise-grade analytics, forecasting, and custom reporting.",
    capabilities: [
      "Real-time dashboard with 50+ KPIs and metrics",
      "Predictive analytics for cash flow and tax planning",
      "Custom report builder with automated scheduling",
      "Multi-dimensional data analysis and visualization"
    ],
    metrics: {
      label: "Insight Generation", 
      value: "Real-time analytics",
      detail: "across 50+ business KPIs"
    }
  },
  {
    category: "Security Architecture",
    icon: "🔐",
    title: "Enterprise-Grade Security",
    description: "Bank-level security with end-to-end encryption, SOC 2 compliance, and enterprise identity management integration.",
    capabilities: [
      "256-bit AES encryption for all data transmission",
      "Multi-factor authentication and SSO integration", 
      "Role-based access control and permissions",
      "SOC 2 Type II certified infrastructure"
    ],
    metrics: {
      label: "Security Standard",
      value: "Bank-level encryption",
      detail: "SOC 2 Type II certified"
    }
  },
  {
    category: "Developer Experience",
    icon: "⚡",
    title: "Enterprise API Gateway", 
    description: "Complete developer toolkit with RESTful APIs, webhooks, SDKs, and comprehensive documentation for seamless integration.",
    capabilities: [
      "RESTful APIs with OpenAPI 3.0 specification",
      "Real-time webhooks for instant notifications",
      "SDKs for Python, Node.js, PHP, .NET, and Java",
      "Interactive API documentation and testing tools"
    ],
    metrics: {
      label: "Developer Tools",
      value: "Complete SDK library", 
      detail: "for 5 major languages"
    }
  }
];

// ========================================
// BEFORE/AFTER COMPARISON DATA - Transformation showcase
// ========================================

export const BEFORE_AFTER_DATA = [
  {
    metric: "Invoice Processing Time",
    before: {
      value: "4-6 hours",
      description: "Manual data entry, format validation, multiple system updates",
      painPoints: ["Manual data entry across 3-5 systems", "Format errors requiring rework", "Missing compliance fields", "Deadline pressure and overtime"]
    },
    after: {
      value: "< 30 seconds",
      description: "Automated processing with real-time validation and sync",
      benefits: ["One-click invoice generation", "Automatic compliance validation", "Real-time system synchronization", "Guaranteed FIRS acceptance"]
    },
    improvement: "99.9% faster",
    category: "Operational Efficiency"
  },
  {
    metric: "System Integration Complexity",
    before: {
      value: "5+ disconnected systems",
      description: "Manual data copying, version conflicts, truth scattered",
      painPoints: ["SAP, QuickBooks, Salesforce all separate", "Manual data reconciliation daily", "Version conflicts and errors", "No single source of truth"]
    },
    after: {
      value: "1 unified platform",
      description: "150+ pre-built integrations with real-time sync",
      benefits: ["All systems connected seamlessly", "Real-time data synchronization", "Single source of truth", "Zero manual reconciliation"]
    },
    improvement: "Complete unification",
    category: "System Architecture"
  },
  {
    metric: "Compliance Accuracy Rate",
    before: {
      value: "60-70% first-time success",
      description: "Frequent rejections, manual fixes, compliance anxiety",
      painPoints: ["30-40% rejection rate from FIRS", "Hours spent fixing errors", "Compliance rule confusion", "Penalty fees and stress"]
    },
    after: {
      value: "99.9% success rate",
      description: "Built-in validation, automatic updates, guaranteed compliance",
      benefits: ["Automatic compliance validation", "Real-time regulation updates", "Zero rejection anxiety", "Penalty-free operations"]
    },
    improvement: "40% accuracy gain",
    category: "Regulatory Compliance"
  },
  {
    metric: "IT Resource Allocation",
    before: {
      value: "60% on maintenance",
      description: "Constant system fixes, integration patches, technical debt",
      painPoints: ["Custom API maintenance overhead", "System downtime and fixes", "Integration breaking regularly", "Technical debt accumulation"]
    },
    after: {
      value: "5% on maintenance",
      description: "Focus on innovation, strategic projects, business growth",
      benefits: ["Zero custom integration maintenance", "99.9% platform uptime", "Resources freed for innovation", "Strategic IT initiatives"]
    },
    improvement: "55% resource liberation",
    category: "Resource Optimization"
  },
  {
    metric: "Business Scaling Capability",
    before: {
      value: "Limited by systems",
      description: "Manual processes break under volume, growth bottlenecks",
      painPoints: ["Manual processes don't scale", "System crashes during peaks", "Growth limited by infrastructure", "Exponential complexity increase"]
    },
    after: {
      value: "Unlimited scalability",
      description: "Enterprise-grade infrastructure handles millions of transactions",
      benefits: ["Handles 1M+ transactions monthly", "Auto-scaling infrastructure", "Growth enables more growth", "Enterprise-ready architecture"]
    },
    improvement: "Infinite scale potential",
    category: "Business Growth"
  },
  {
    metric: "Employee Experience",
    before: {
      value: "Frustrated and stressed",
      description: "Repetitive tasks, system fights, late nights fixing errors",
      painPoints: ["Repetitive manual data entry", "Fighting with broken systems", "Overtime fixing compliance errors", "High stress, low satisfaction"]
    },
    after: {
      value: "Empowered and strategic",
      description: "Focus on high-value work, strategic initiatives, innovation",
      benefits: ["Automated routine tasks", "Strategic project focus", "Work-life balance restored", "Career growth opportunities"]
    },
    improvement: "Complete transformation",
    category: "Human Impact"
  }
];

// ========================================
// SOLUTION PATTERNS (Positive Outcomes)
// ========================================

export const SOLUTION_PATTERNS = {
  timeRecovery: {
    emoji: EMOJIS.lightning,
    title: "Instant Automation",
    benefits: [
      "Submit invoices in seconds, not hours",
      "Automated compliance checks", 
      "Focus on growing your business",
      "No more manual data entry"
    ]
  },
  
  zeroErrors: {
    emoji: EMOJIS.check,
    title: "Perfect Accuracy",
    benefits: [
      "100% compliant submissions", 
      "Built-in validation prevents errors",
      "Real-time feedback on issues",
      "First-time success guaranteed"
    ]
  },
  
  peaceOfMind: {
    emoji: EMOJIS.shield,
    title: "Complete Confidence", 
    benefits: [
      "Always up-to-date with regulations",
      "Automated compliance monitoring",
      "Sleep well knowing you're covered",
      "Focus on business, not bureaucracy"
    ]
  },
  
  seamlessIntegration: {
    emoji: EMOJIS.target,
    title: "One-Click Integration",
    benefits: [
      "Works with your existing software",
      "Single source of truth",
      "Automated data synchronization", 
      "No system changes required"
    ]
  }
} as const;

// ========================================
// COLOR SCHEME PATTERNS
// ========================================

export const COLOR_SCHEMES = {
  // Problem section colors (professional blue)
  problems: {
    primary: "blue-500",
    primaryLight: "blue-100", 
    primaryDark: "blue-600",
    background: "gray-700",
    cardBackground: "white",
    text: "gray-700",
    accent: "blue-400"
  },
  
  // Solution section colors (success green)  
  solutions: {
    primary: "green-500",
    primaryLight: "green-100",
    primaryDark: "green-600", 
    background: "gray-50",
    cardBackground: "white",
    text: "gray-700",
    accent: "green-400"
  },
  
  // Feature section colors (professional slate)
  features: {
    primary: "slate-500", 
    primaryLight: "slate-100",
    primaryDark: "slate-600",
    background: "white",
    cardBackground: "gray-50", 
    text: "gray-700",
    accent: "slate-400"
  },
  
  // Testimonials section colors (warm amber)
  testimonials: {
    primary: "amber-500",
    primaryLight: "amber-100", 
    primaryDark: "amber-600",
    background: "amber-50",
    cardBackground: "white",
    text: "gray-700", 
    accent: "amber-400"
  }
} as const;

// ========================================
// TYPOGRAPHY PATTERNS
// ========================================

export const TYPOGRAPHY_PATTERNS = {
  // Section headers
  sectionBadge: "inline-block px-6 py-2 rounded-full text-sm font-semibold mb-6",
  sectionHeading: "text-4xl md:text-5xl font-black mb-6 leading-tight",
  sectionSubtitle: "text-xl max-w-3xl mx-auto leading-relaxed",
  
  // Card elements
  cardTitle: "text-xl font-bold text-gray-900 mb-4",
  cardContent: "text-gray-700 mb-4",
  cardAttribution: "font-semibold text-sm",
  
  // Trust indicators
  trustNumber: "!text-5xl md:!text-6xl !font-black italic mb-1",
  trustLabel: "text-base md:text-lg font-semibold transition-colors",
} as const;

// ========================================
// ANIMATION PATTERNS (from legacy animations)
// ========================================

export const ANIMATION_PATTERNS = {
  // Card hover effects
  cardHover: "hover:shadow-md hover:-translate-y-1 transition-all duration-200",
  cardHoverEnhanced: "hover:shadow-lg hover:-translate-y-2 transition-all duration-200",
  
  // Scale effects
  scaleHover: "hover:scale-105 transition-all duration-300",
  scaleSubtle: "hover:scale-110 transition-all duration-300",
  
  // Fade effects
  fadeIn: "transition-opacity duration-200 ease-out",
  slideUp: "transition-all duration-300 ease-out",
} as const;

// ========================================
// GRID PATTERNS (Responsive Layouts)
// ========================================

export const GRID_PATTERNS = {
  // Problem/Solution cards
  cardGrid: "grid md:grid-cols-2 lg:grid-cols-3 gap-8",
  
  // Feature showcase
  featureGrid: "grid md:grid-cols-2 gap-12",
  
  // Trust indicators  
  trustGrid: "grid grid-cols-2 md:grid-cols-4 gap-8 text-center",
  
  // Testimonials
  testimonialGrid: "grid md:grid-cols-2 lg:grid-cols-3 gap-6",
} as const;