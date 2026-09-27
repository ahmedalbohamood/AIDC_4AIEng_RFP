// ─────────────────────────────────────────────────────────────────────────────
// RFP Extract — Translations (English + Arabic)
// ─────────────────────────────────────────────────────────────────────────────

import type { Lang } from './types'

export interface Strings {
  // Branding
  brand: string
  tagline: string

  // Navigation
  extract: string
  chat: string
  categories: string
  status: string
  recent: string
  allFields: string
  allStatus: string
  version: string

  // Status labels
  found: string
  notFound: string
  needsReview: string

  // Confidence labels
  high: string
  medium: string
  low: string
  na: string
  allConf: string

  // Category labels
  catLabels: Record<string, string>

  // Page titles
  fieldExtraction: string
  rfpAssistant: string

  // Chat
  onlineDocLoaded: string
  chatPlaceholder: string
  chatDisclaimer: string
  suggestedQ: string
  hiMsg: string
  quickPrompts: string[]

  // KPI tiles
  fieldsFound: string
  missingFields: string
  needsReviewKpi: string
  avgConf: string
  pagesProcessed: string
  coverage: string
  docLanguage: string
  docType: string

  // KPI subtexts
  ofTotal: string
  fromDoc: string
  manualCheck: string
  highConfFields: string
  fromUpload: string
  coverageVal: string
  docLang: string
  docTypeVal: string

  // Table columns
  field: string
  extractedValue: string
  confidence: string
  statusCol: string

  // Evidence panel
  sourceExcerpt: string
  notFoundDoc: string
  page: string
  section: string
  askAIAbout: string
  notSpecified: string

  // Upload
  uploadTitle: string
  uploadSub: string
  uploadHint: string
  dragging: string

  // Processing
  aiExtract: string
  processDone: string
  processingSteps: string[]

  // Filters & misc
  noMatch: string
  searchFields: string
  newUpload: string
  fieldsShown: string
  fields: string
  shown: string

  // Eval insights
  evalInsights: string
  missingInfo: string
  lowConf: string
  upcomingDeadlines: string
  mandatoryItems: string

  // Confidence tooltip
  confTooltipTitle: string

  // Theme / language
  themeLight: string
  themeDark: string
  themeSystem: string
  english: string
  arabic: string

  // Recent docs (placeholder labels)
  recentDocs: string[]

  // Agent workspace
  agent: string
  agentTitle: string
  agentSubtitle: string
  agentRun: string
  agentRunning: string
  agentDone: string
  totalFindings: string
  criticalLabel: string
  highLabel: string
  mediumLabel: string
  lowLabel: string
  potentialGaps: string
  pagesReviewed: string
  allFindings: string
  confirmedIssue: string
  potentialIssue: string
  whyItMatters: string
  viewSources: string
  agentCategories: Record<string, string>
  agentCatLabels: Record<string, string>
  agentProcessingSteps: string[]
  agentEmpty: string
  sourcePage: string
  sourceSection: string
  excerpt: string
}

const en: Strings = {
  brand: 'RFP Extract',
  tagline: 'AI-powered analysis',

  extract: 'Extract',
  chat: 'Chat',
  categories: 'Categories',
  status: 'Status',
  recent: 'Recent',
  allFields: 'All Fields',
  allStatus: 'All Status',
  version: 'Beamdata · v2.4.1',

  found: 'Found',
  notFound: 'Not Found',
  needsReview: 'Needs Review',

  high: 'High',
  medium: 'Med',
  low: 'Low',
  na: 'N/A',
  allConf: 'All Confidence',

  catLabels: {
    deadline:     'Deadlines',
    contact:      'Contact & Submission',
    scope:        'Scope & Terms',
    requirements: 'Requirements',
    evaluation:   'Evaluation',
    compliance:   'Compliance',
  },

  fieldExtraction: 'Field Extraction',
  rfpAssistant: 'RFP Assistant',

  onlineDocLoaded: '● Online · Document loaded',
  chatPlaceholder: 'Ask about this RFP…',
  chatDisclaimer: 'Answers are grounded in the uploaded document only',
  suggestedQ: 'Suggested questions',
  hiMsg: "Hi! I'm your RFP assistant. I've analysed the uploaded document and can answer questions about deadlines, requirements, scoring, compliance, and more.\n\nWhat would you like to know?",
  quickPrompts: [
    'What is the submission deadline?',
    'Summarize the scope of work',
    'What insurance is required?',
    'Is a vendor demo required?',
    'List all technical requirements',
    'What is the scoring breakdown?',
    'What information is missing?',
    'What are the contract renewal options?',
  ],

  fieldsFound: 'Fields Found',
  missingFields: 'Missing Fields',
  needsReviewKpi: 'Needs Review',
  avgConf: 'Avg Confidence',
  pagesProcessed: 'Pages Processed',
  coverage: 'Coverage',
  docLanguage: 'Doc Language',
  docType: 'Doc Type',

  ofTotal: 'of total',
  fromDoc: 'not found in document',
  manualCheck: 'manual check recommended',
  highConfFields: 'high-confidence fields',
  fromUpload: 'from uploaded document',
  coverageVal: '94%',
  docLang: 'English',
  docTypeVal: 'Government RFP',

  field: 'Field',
  extractedValue: 'Extracted Value',
  confidence: 'Confidence',
  statusCol: 'Status',

  sourceExcerpt: 'Supporting Evidence',
  notFoundDoc: 'This field was not found in the uploaded document.',
  page: 'Page',
  section: 'Section',
  askAIAbout: 'Ask AI about this field',
  notSpecified: 'Not specified in the document',

  uploadTitle: 'Upload an RFP document',
  uploadSub: 'Drag & drop or click · PDF, DOCX, or TXT',
  uploadHint: 'AI will extract all 17 standard RFP fields automatically',
  dragging: 'Drop your RFP here',

  aiExtract: 'AI extraction in progress…',
  processDone: 'Extraction complete',
  processingSteps: [
    'Uploading document',
    'Reading 22 pages',
    'Extracting RFP fields',
    'Analysing requirements',
    'Evaluating evidence',
    'Complete',
  ],

  noMatch: 'No fields match the current filters.',
  searchFields: 'Search fields…',
  newUpload: 'New Upload',
  fieldsShown: 'shown',
  fields: 'fields',
  shown: 'shown',

  evalInsights: 'Evaluation Insights',
  missingInfo: 'Missing Information',
  lowConf: 'Low-Confidence Fields',
  upcomingDeadlines: 'Key Deadlines',
  mandatoryItems: 'Mandatory Requirements',

  confTooltipTitle: 'Confidence explanation',

  themeLight: 'Light',
  themeDark: 'Dark',
  themeSystem: 'System',
  english: 'English',
  arabic: 'العربية',

  recentDocs: ['City of Portland RFP 2025-047', 'State DOT Vendor Services'],

  agent: 'Agent',
  agentTitle: 'RFP Review Agent',
  agentSubtitle: 'Autonomous review — detects conflicts, gaps, ambiguities, and inconsistencies',
  agentRun: 'Run Agent Review',
  agentRunning: 'Agent reviewing document…',
  agentDone: 'Review complete',
  totalFindings: 'Total Findings',
  criticalLabel: 'Critical',
  highLabel: 'High',
  mediumLabel: 'Medium',
  lowLabel: 'Low',
  potentialGaps: 'Potential Gaps',
  pagesReviewed: 'Pages Reviewed',
  allFindings: 'All Findings',
  confirmedIssue: 'Confirmed Issue',
  potentialIssue: 'Potential Issue — Needs Human Review',
  whyItMatters: 'Why it matters',
  viewSources: 'View Sources',
  agentCategories: {
    dates:           'Dates',
    submission:      'Submission',
    requirements:    'Requirements',
    evaluation:      'Evaluation',
    contract:        'Contract',
    compliance:      'Compliance',
    references:      'References & Attachments',
    cross_references: 'Cross-References',
    ambiguity:       'Ambiguity',
    other:           'Other',
  },
  agentCatLabels: {
    dates:           'Dates',
    submission:      'Submission',
    requirements:    'Requirements',
    evaluation:      'Evaluation',
    contract:        'Contract',
    compliance:      'Compliance',
    references:      'References',
    cross_references: 'Cross-References',
    ambiguity:       'Ambiguity',
    other:           'Other',
  },
  agentProcessingSteps: [
    'Uploading document',
    'Reading pages',
    'Extracting RFP fields',
    'Checking cross-references',
    'Detecting date conflicts',
    'Analysing requirements',
    'Detecting inconsistencies',
    'Generating findings',
    'Review complete',
  ],
  agentEmpty: 'No findings match the current filters.',
  sourcePage: 'Page',
  sourceSection: 'Section',
  excerpt: 'Supporting excerpt',
}

const ar: Strings = {
  brand: 'استخراج العروض',
  tagline: 'تحليل مدعوم بالذكاء الاصطناعي',

  extract: 'استخراج',
  chat: 'محادثة',
  categories: 'التصنيفات',
  status: 'الحالة',
  recent: 'الأخيرة',
  allFields: 'جميع الحقول',
  allStatus: 'جميع الحالات',
  version: 'Beamdata · v2.4.1',

  found: 'موجود',
  notFound: 'غير موجود',
  needsReview: 'يحتاج مراجعة',

  high: 'مرتفع',
  medium: 'متوسط',
  low: 'منخفض',
  na: 'غ.م',
  allConf: 'جميع مستويات الثقة',

  catLabels: {
    deadline:     'المواعيد النهائية',
    contact:      'التواصل والتقديم',
    scope:        'النطاق والشروط',
    requirements: 'المتطلبات',
    evaluation:   'التقييم',
    compliance:   'الامتثال',
  },

  fieldExtraction: 'استخراج الحقول',
  rfpAssistant: 'مساعد طلب العروض',

  onlineDocLoaded: '● متصل · الوثيقة محمّلة',
  chatPlaceholder: 'اسأل عن هذا الطلب…',
  chatDisclaimer: 'الإجابات مستندة حصراً إلى الوثيقة المرفوعة',
  suggestedQ: 'أسئلة مقترحة',
  hiMsg: 'مرحباً! أنا مساعدك لتحليل طلبات العروض. لقد حللت الوثيقة المرفوعة ويمكنني الإجابة عن أسئلة تتعلق بالمواعيد والمتطلبات والتقييم والامتثال والمزيد.\n\nما الذي تريد معرفته؟',
  quickPrompts: [
    'ما هو الموعد النهائي للتقديم؟',
    'ملخص نطاق العمل',
    'ما هي متطلبات التأمين؟',
    'هل يُشترط تقديم عرض توضيحي؟',
    'اعرض جميع المتطلبات التقنية',
    'ما هو توزيع درجات التقييم؟',
    'ما المعلومات المفقودة في الوثيقة؟',
    'ما هي خيارات تجديد العقد؟',
  ],

  fieldsFound: 'الحقول الموجودة',
  missingFields: 'الحقول المفقودة',
  needsReviewKpi: 'يحتاج مراجعة',
  avgConf: 'متوسط الثقة',
  pagesProcessed: 'الصفحات المعالجة',
  coverage: 'التغطية',
  docLanguage: 'لغة الوثيقة',
  docType: 'نوع الوثيقة',

  ofTotal: 'من الإجمالي',
  fromDoc: 'غير موجود في الوثيقة',
  manualCheck: 'يُوصى بالمراجعة اليدوية',
  highConfFields: 'حقل عالي الثقة',
  fromUpload: 'من الوثيقة المرفوعة',
  coverageVal: '٩٤٪',
  docLang: 'الإنجليزية',
  docTypeVal: 'طلب عروض حكومي',

  field: 'الحقل',
  extractedValue: 'القيمة المستخرجة',
  confidence: 'الثقة',
  statusCol: 'الحالة',

  sourceExcerpt: 'الدليل المرجعي',
  notFoundDoc: 'لم يتم العثور على هذا الحقل في الوثيقة المرفوعة.',
  page: 'صفحة',
  section: 'قسم',
  askAIAbout: 'اسأل الذكاء الاصطناعي عن هذا الحقل',
  notSpecified: 'غير محدد في الوثيقة',

  uploadTitle: 'تحميل وثيقة طلب العروض',
  uploadSub: 'اسحب وأفلت أو انقر · PDF أو DOCX أو TXT',
  uploadHint: 'سيقوم الذكاء الاصطناعي تلقائياً باستخراج جميع الحقول المعيارية الـ 17',
  dragging: 'أفلت وثيقة طلب العروض هنا',

  aiExtract: 'جاري الاستخراج بالذكاء الاصطناعي…',
  processDone: 'اكتمل الاستخراج',
  processingSteps: [
    'تحميل الوثيقة',
    'قراءة 22 صفحة',
    'استخراج حقول الطلب',
    'تحليل المتطلبات',
    'تقييم الأدلة',
    'اكتملت العملية',
  ],

  noMatch: 'لا توجد حقول تطابق الفلاتر الحالية.',
  searchFields: 'البحث في الحقول…',
  newUpload: 'وثيقة جديدة',
  fieldsShown: 'ظاهر',
  fields: 'حقلاً',
  shown: 'ظاهر',

  evalInsights: 'رؤى التقييم',
  missingInfo: 'معلومات مفقودة',
  lowConf: 'حقول منخفضة الثقة',
  upcomingDeadlines: 'المواعيد الرئيسية',
  mandatoryItems: 'المتطلبات الإلزامية',

  confTooltipTitle: 'شرح مستوى الثقة',

  themeLight: 'فاتح',
  themeDark: 'داكن',
  themeSystem: 'النظام',
  english: 'English',
  arabic: 'العربية',

  recentDocs: ['طلب عروض بورتلاند 2025-047', 'خدمات بائعي هيئة النقل'],

  agent: 'وكيل',
  agentTitle: 'وكيل مراجعة طلبات العروض',
  agentSubtitle: 'مراجعة تلقائية — يكتشف التعارضات والفجوات والغموض والتناقضات',
  agentRun: 'تشغيل مراجعة الوكيل',
  agentRunning: 'الوكيل يراجع الوثيقة…',
  agentDone: 'اكتملت المراجعة',
  totalFindings: 'إجمالي النتائج',
  criticalLabel: 'حرج',
  highLabel: 'عالٍ',
  mediumLabel: 'متوسط',
  lowLabel: 'منخفض',
  potentialGaps: 'فجوات محتملة',
  pagesReviewed: 'الصفحات المراجعة',
  allFindings: 'جميع النتائج',
  confirmedIssue: 'مشكلة مؤكدة',
  potentialIssue: 'مشكلة محتملة — تتطلب مراجعة بشرية',
  whyItMatters: 'لماذا يهم هذا',
  viewSources: 'عرض المصادر',
  agentCategories: {
    dates:           'التواريخ',
    submission:      'التقديم',
    requirements:    'المتطلبات',
    evaluation:      'التقييم',
    contract:        'العقد',
    compliance:      'الامتثال',
    references:      'المراجع والمرفقات',
    cross_references: 'الإحالات المرجعية',
    ambiguity:       'الغموض',
    other:           'أخرى',
  },
  agentCatLabels: {
    dates:           'التواريخ',
    submission:      'التقديم',
    requirements:    'المتطلبات',
    evaluation:      'التقييم',
    contract:        'العقد',
    compliance:      'الامتثال',
    references:      'المراجع',
    cross_references: 'الإحالات',
    ambiguity:       'الغموض',
    other:           'أخرى',
  },
  agentProcessingSteps: [
    'تحميل الوثيقة',
    'قراءة الصفحات',
    'استخراج حقول الطلب',
    'فحص الإحالات المرجعية',
    'اكتشاف تعارضات التواريخ',
    'تحليل المتطلبات',
    'اكتشاف التناقضات',
    'توليد النتائج',
    'اكتملت المراجعة',
  ],
  agentEmpty: 'لا توجد نتائج تطابق الفلاتر الحالية.',
  sourcePage: 'صفحة',
  sourceSection: 'قسم',
  excerpt: 'مقتطف داعم',
}

export const translations: Record<Lang, Strings> = { en, ar }

/** Convenience hook — returns the string set for the active language */
export function t(lang: Lang): Strings {
  return translations[lang]
}
