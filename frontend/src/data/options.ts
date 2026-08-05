export const SKILL_OPTIONS = [
  'UX Research',
  'Figma',
  'Prototyping',
  'Design Systems',
  'React',
  'TypeScript',
  'Node.js',
  'Python',
  'Go',
  'Kubernetes',
  'System Design',
  'Machine Learning',
  'Data Visualization',
  'SQL',
  'Product Strategy',
  'Roadmapping',
  'A/B Testing',
  'User Interviews',
  'Content Strategy',
  'UX Writing',
  'SEO',
  'Brand Voice',
  'Team Leadership',
  'Project Management',
  'Customer Success',
  'Sales',
  'Public Speaking',
];

export const INTEREST_OPTIONS = [
  'Running',
  'Photography',
  'Hiking',
  'Rock Climbing',
  'Cycling',
  'Yoga',
  'Reading',
  'Cooking',
  'Perfumes',
  'Gardening',
  'Ceramics',
  'Music',
  'Embroidery',
  'Board Games',
  'Tennis',
  'Football',
  'Painting',
  'Economics',
  'Machine Learning',
  'Napping',
  'Journaling',
  'Travel',
  'Dancing',
  'Films',
  'Art',
  'Wine',
  'Language learning',
];


export const LANGUAGE_OPTIONS = [
  'English',
  'Spanish',
  'French',
  'German',
  'Italian',
  'Portuguese',
  'Mandarin',
  'Cantonese',
  'Japanese',
  'Korean',
  'Arabic',
  'Hindi',
  'Ukrainian',
  'Polish',
  'Dutch',
  'Swedish',
  'Danish',
  'Norwegian',
  'Turkish',
  'Yoruba',
  'Malayalam',
];

export const FORMAT_OPTIONS = ['Video Call', 'In-person', 'Phone', 'Async (voice notes)'];

export const DEPARTMENT_OPTIONS = [
  'Product',
  'Engineering',
  'Analytics',
  'Marketing',
  'Design',
  'Sales',
  'Customer Success',
  'People & Culture',
  'Finance',
  'Legal',
];

export const TIMEZONE_OPTIONS = [
  'PST (UTC-8)',
  'MST (UTC-7)',
  'CST (UTC-6)',
  'EST (UTC-5)',
  'GMT (UTC+0)',
  'CET (UTC+1)',
  'EET (UTC+2)',
  'IST (UTC+5:30)',
  'JST (UTC+9)',
];

export const DAYS = [
  { key: 'Mon', label: 'Monday' },
  { key: 'Tue', label: 'Tuesday' },
  { key: 'Wed', label: 'Wednesday' },
  { key: 'Thu', label: 'Thursday' },
  { key: 'Fri', label: 'Friday' },
] as const;

export const HOURS = [
  { key: '09', label: '9:00', period: 'AM' },
  { key: '10', label: '10:00', period: 'AM' },
  { key: '11', label: '11:00', period: 'AM' },
  { key: '12', label: '12:00', period: 'PM' },
  { key: '13', label: '1:00', period: 'PM' },
  { key: '14', label: '2:00', period: 'PM' },
  { key: '15', label: '3:00', period: 'PM' },
  { key: '16', label: '4:00', period: 'PM' },
  { key: '17', label: '5:00', period: 'PM' },
] as const;

export const HOUR_LABELS: Record<string, string> = Object.fromEntries(HOURS.map((h) => [h.key, `${h.label} ${h.period}`]));

export function slotKey(day: string, hour: string) {
  return `${day}-${hour}`;
}
