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