import { 
  ComponentType,
  SVGProps
} from "react";
import { 
  GlobeAltIcon as Globe,
  BriefcaseIcon as Briefcase,
  BuildingLibraryIcon as Landmark,
  UsersIcon as Users,
  HeartIcon as HeartPulse,
  CpuChipIcon as Cpu,
  BeakerIcon as Atom,
  AcademicCapIcon as GraduationCap,
  TrophyIcon as Dumbbell,
  FilmIcon as Film,
  PuzzlePieceIcon as Gamepad2, 
  TruckIcon as Bus,
  MusicalNoteIcon as Music,
  CakeIcon as Utensils,
  ComputerDesktopIcon as Laptop,
  ChartBarIcon as LineChart,
  SparklesIcon as Wand2,
  GlobeAmericasIcon as Leaf, // Using globe as alternative for environment
  RocketLaunchIcon as Rocket,
  BookOpenIcon as BookOpen
} from "@heroicons/react/24/outline";

// Define the icon type for Heroicons
type HeroIcon = ComponentType<SVGProps<SVGSVGElement>>;

// Map topic ids or slugs to appropriate icons
export const topicIconMap: Record<string, HeroIcon> = {
  // News categories
  "world": Globe,
  "business": Briefcase,
  "politics": Landmark,
  "society": Users,
  "health": HeartPulse,
  "technology": Cpu,
  "science": Atom,
  "education": GraduationCap,
  "sports": Dumbbell,
  "entertainment": Film,
  "gaming": Gamepad2,
  "travel": Bus,
  "music": Music,
  "food": Utensils,
  "tech": Cpu,
  "finance": LineChart,
  "culture": Wand2,
  "environment": Leaf, // Using globe as alternative
  "space": Rocket,
  "literature": BookOpen,
  
  // Default fallback
  "default": Globe
};

/**
 * Get an appropriate icon for a topic based on its name or ID
 * 
 * @param topic The topic name, ID or slug
 * @returns A Heroicon component
 */
export function getTopicIcon(topic: string | number): HeroIcon {
  if (typeof topic === 'number') {
    // If we have topic IDs, we need to map them to slugs or handle directly
    // This is a placeholder - in a real app we might need to map IDs to slugs
    return topicIconMap["default"];
  }
  
  // Convert to lowercase and remove spaces for matching
  const normalizedTopic = topic.toString().toLowerCase().replace(/\s+/g, '');
  
  // Check for partial matches
  for (const [key, icon] of Object.entries(topicIconMap)) {
    if (normalizedTopic.includes(key)) {
      return icon;
    }
  }
  
  return topicIconMap["default"];
} 